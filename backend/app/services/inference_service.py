"""Load validated artifacts and produce multimodal risk explanations."""

import os
import json
import base64
import io
import torch
torch.set_num_threads(1)
import torch.nn.functional as F
import numpy as np
import sys
sys.modules['numpy._core'] = np.core
sys.modules['numpy._core.multiarray'] = np.core.multiarray
sys.modules['numpy._core.numeric'] = np.core.numeric
sys.modules['numpy._core.umath'] = np.core.umath
import shap
from captum.attr import LayerGradCam
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib

from app.core.config import (
    settings,
    HIGH_RISK_THRESHOLD_PCT,
    TRIAGE_RED_THRESHOLD,
    TRIAGE_ORANGE_THRESHOLD,
    TRIAGE_YELLOW_THRESHOLD
)
from app.models.networks import ResNet1D, VitalsMLP, HistoricalGRU, OmniFusionNet
from app.models.schemas import PredictRequest, PredictResponse

device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')

class InferenceService:
    """Singleton inference facade around the validated Omni-Fusion checkpoint."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InferenceService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        print("Initializing InferenceService singleton...", flush=True)
        # Resolve models_dir dynamically across local, Docker, and Render environments
        candidate_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models')),
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'models')),
            os.path.abspath(os.path.join(os.getcwd(), 'models')),
            os.path.abspath(os.path.join(os.getcwd(), 'backend', 'models')),
            '/app/models',
            '/app/backend/models',
            '/models',
        ]
        models_dir = None
        for path in candidate_paths:
            if os.path.exists(os.path.join(path, 'checkpoints', 'ecg_branch_config.json')):
                models_dir = path
                break

        if not models_dir:
            models_dir = candidate_paths[0]
            print(f"Warning: Could not find ecg_branch_config.json in candidates. Defaulting models_dir to {models_dir}", flush=True)
        else:
            print(f"Resolved models_dir to: {models_dir}", flush=True)

        with open(os.path.join(models_dir, 'checkpoints', 'ecg_branch_config.json'), 'r') as f:
            cfg_ecg = json.load(f)
        model_ecg = ResNet1D(12, cfg_ecg['num_classes'], cfg_ecg['depth'], cfg_ecg['dropout'])

        with open(os.path.join(models_dir, 'checkpoints', 'vitals_branch_config.json'), 'r') as f:
            cfg_vitals = json.load(f)
        model_vitals = VitalsMLP(cfg_vitals['input_dim'], cfg_vitals['hidden_dim'], cfg_vitals['num_layers'], cfg_vitals['dropout'])

        with open(os.path.join(models_dir, 'checkpoints', 'historical_branch_config.json'), 'r') as f:
            cfg_hist = json.load(f)
        model_hist = HistoricalGRU(cfg_hist['input_dim'], cfg_hist['hidden_dim'], cfg_hist['num_layers'], cfg_hist['dropout'])

        ecg_emb_dim = model_ecg.fc.in_features
        vitals_emb_dim = model_vitals.net[-1].in_features
        hist_emb_dim = model_hist.fc.in_features

        import torch.nn as nn
        model_ecg.fc = nn.Identity()
        model_vitals.net[-1] = nn.Identity()
        model_hist.fc = nn.Identity()

        self.model = OmniFusionNet(model_ecg, model_vitals, model_hist, ecg_emb_dim, vitals_emb_dim, hist_emb_dim).to(device)
        
        model_path = settings.model_path
        if not os.path.exists(model_path):
            if model_path.startswith('../models'):
                model_path = model_path.replace('../models', models_dir)
            if not os.path.exists(model_path):
                alt_path = os.path.join(models_dir, 'exported', 'omni_fusion_final.pt')
                if os.path.exists(alt_path):
                    model_path = alt_path
            
        self.model.load_state_dict(torch.load(model_path, weights_only=True, map_location=device))
        self.model.eval()

        # Initialize LayerGradCam
        self.layer_gc = LayerGradCam(self.model, self.model.ecg_net.layer[-1])

        # Feature columns for Tabular
        self.feature_cols = ['anchor_age', 'gender', 'Creatinine', 'Glucose', 'Potassium', 'Sodium', 'HR', 'SBP', 'DBP', 'RR', 'O2']
        self.feature_names = [f"Vital_{c}" for c in self.feature_cols] + [f"Hist_{c}" for c in self.feature_cols]

        # Load Scaler Artifacts
        scaler_path = os.path.join(models_dir, 'checkpoints', 'vitals_scaler.pkl')
        feature_order_path = os.path.join(models_dir, 'checkpoints', 'vitals_scaler_feature_order.pkl')
        shap_bg_path = os.path.join(models_dir, 'checkpoints', 'shap_background.npy')
        
        if not os.path.exists(scaler_path) or not os.path.exists(feature_order_path) or not os.path.exists(shap_bg_path):
            raise RuntimeError(f"Missing inference artifacts in {models_dir}/checkpoints. Please run training_scripts/02_preprocessing.py to generate them.")
            
        self.vitals_scaler = joblib.load(scaler_path)
        self.scaler_feature_order = joblib.load(feature_order_path)
        
        if self.feature_cols != self.scaler_feature_order:
            print(f"Warning: Expected feature order {self.feature_cols} does not match scaler feature order {self.scaler_feature_order}. Ensure correct mapping.")

        # SHAP Background
        self.bg_summary = np.load(shap_bg_path).astype(np.float32)
        import gc
        gc.collect()
        print("InferenceService initialization complete.", flush=True)

    def predict(self, req: PredictRequest) -> PredictResponse:
        """Predict hospital mortality probability and explanation artifacts.

        Raw vitals and historical values are transformed exactly once with the
        Phase 13 fitted ``StandardScaler`` in its persisted feature order. The
        ECG stays in waveform space. Kernel SHAP uses the persisted Phase 13
        vitals background, paired with zero history to represent unavailable
        longitudinal data. Grad-CAM targets mortality class 1 on the final ECG
        residual block.

        Args:
            req: Validated ECG, current vitals, and optional historical inputs.

        Returns:
            A response whose ``risk_score`` is the softmax probability of
            ``hospital_expire_flag`` (class 1), plus SHAP and ECG Grad-CAM data.
        """
        vitals_arr_raw = np.array([[getattr(req.vitals, c) for c in self.scaler_feature_order]], dtype=np.float32)
        
        # Scale vitals
        vitals_arr = self.vitals_scaler.transform(vitals_arr_raw).astype(np.float32)
        
        # Sanity check on scaled vitals
        if np.any(np.abs(vitals_arr) > 8):
            print(f"Warning: Transformed vitals have extreme values (> 8 standard deviations): {vitals_arr}")
        
        # Clip to prevent out-of-distribution neural network extrapolation
        vitals_arr = np.clip(vitals_arr, -3.0, 3.0)
        
        if req.historical:
            hist_arr_raw = np.array([[getattr(req.historical, c) for c in self.scaler_feature_order]], dtype=np.float32)
            hist_arr = self.vitals_scaler.transform(hist_arr_raw).astype(np.float32)
            if np.any(np.abs(hist_arr) > 8):
                print(f"Warning: Transformed historical vitals have extreme values (> 8 standard deviations): {hist_arr}")
            
            # Clip to prevent out-of-distribution neural network extrapolation
            hist_arr = np.clip(hist_arr, -3.0, 3.0)
            streams_used = ["ecg", "vitals", "historical"]
        else:
            hist_arr = np.zeros((1, len(self.scaler_feature_order)), dtype=np.float32)
            streams_used = ["ecg", "vitals"]

        pat_tabular = np.concatenate([vitals_arr, hist_arr], axis=1)

        v_t = torch.tensor(vitals_arr).to(device)
        h_t = torch.tensor(hist_arr).unsqueeze(1).to(device)
        
        ecg_np = np.array(req.ecg, dtype=np.float32).reshape(1, 12, 1000)
        pat_ecg = torch.tensor(ecg_np).to(device)

        with torch.no_grad():
            logits = self.model(pat_ecg, v_t, h_t)
            prob = torch.softmax(logits, dim=1).cpu().numpy()[0, 1]

        # Tabular SHAP (chunked to prevent memory spikes on 512MB RAM containers)
        def predict_fn(tabular_array):
            batch_size = 16
            n_samples = tabular_array.shape[0]
            probs = []
            for i in range(0, n_samples, batch_size):
                sub_arr = tabular_array[i:i+batch_size]
                v = sub_arr[:, :len(self.scaler_feature_order)]
                h = sub_arr[:, len(self.scaler_feature_order):]
                v_tensor = torch.tensor(v, dtype=torch.float32).to(device)
                h_tensor = torch.tensor(h, dtype=torch.float32).unsqueeze(1).to(device)
                e_tensor = pat_ecg.repeat(sub_arr.shape[0], 1, 1)
                with torch.no_grad():
                    l = self.model(e_tensor, v_tensor, h_tensor)
                    p = torch.softmax(l, dim=1).cpu().numpy()[:, 1]
                    probs.append(p)
            return np.concatenate(probs, axis=0)

        # Use a lightweight background summary (5 samples) and nsamples=25 to stay within memory limits
        bg_sub = self.bg_summary[:5] if len(self.bg_summary) > 5 else self.bg_summary
        combined_bg = np.concatenate([bg_sub, np.zeros_like(bg_sub)], axis=1)
        explainer = shap.KernelExplainer(predict_fn, combined_bg, silent=True)
        shap_vals = explainer.shap_values(pat_tabular, nsamples=25, silent=True)
        
        # Handle shap_vals format compatibility
        if isinstance(shap_vals, list):
            sv = shap_vals[0]
        else:
            sv = shap_vals
        if sv.ndim > 1:
            sv = sv[0]
            
        shap_dict = {self.feature_names[i]: float(sv[i]) for i in range(len(self.feature_names))}
        import gc
        gc.collect()

        # ECG Grad-CAM
        attr = self.layer_gc.attribute(inputs=pat_ecg, additional_forward_args=(v_t, h_t), target=1)
        attr = F.interpolate(attr, size=ecg_np.shape[2], mode='linear').squeeze().cpu().detach().numpy()

        ecg_signal = ecg_np[0, 0, :]
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(ecg_signal, color='black', linewidth=1)
        extent = [0, ecg_np.shape[2], np.min(ecg_signal)-0.5, np.max(ecg_signal)+0.5]
        im = ax.imshow(attr[np.newaxis, :], cmap='jet', aspect='auto', alpha=0.5, extent=extent)
        plt.colorbar(im, ax=ax, label='Grad-CAM Activation')
        ax.set_title(f"{req.patient_id} ECG Grad-CAM (Target=1)")
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        gc_b64 = base64.b64encode(buf.read()).decode('utf-8')

        # Failure Analysis Summary
        sorted_features = sorted(shap_dict.items(), key=lambda x: x[1])
        top_pushing = sorted_features[-2:]
        top_pulling = sorted_features[:2]
        pred_str = "High Risk (Mortality)" if prob > 0.5 else "Low Risk (Survival)"
        summary = f"Model predicted {pred_str}. "
        if prob > 0.5:
            summary += f"It overly weighted {top_pushing[1][0]} and {top_pushing[0][0]} towards risk, while underestimating the protective impact of {top_pulling[0][0]}."
        else:
            summary += f"It overly relied on {top_pulling[0][0]} and {top_pulling[1][0]} to predict safety, while ignoring the risk indicators from {top_pushing[1][0]}."

        # Compute triage tier
        prob_pct = prob * 100
        if prob_pct >= TRIAGE_RED_THRESHOLD:
            triage_tier = "Red"
        elif prob_pct >= TRIAGE_ORANGE_THRESHOLD:
            triage_tier = "Orange"
        elif prob_pct >= TRIAGE_YELLOW_THRESHOLD:
            triage_tier = "Yellow"
        else:
            triage_tier = "Green"

        return PredictResponse(
            patient_id=req.patient_id,
            risk_score=float(prob),
            triage_tier=triage_tier,
            shap_data=shap_dict,
            ecg_gradcam_heatmap_b64=gc_b64,
            ecg_gradcam_data=attr.tolist(),
            raw_ecg=req.ecg,
            failure_analysis_summary=summary,
            streams_used=streams_used
        )

# Instantiate the singleton so it loads exactly once on module import
inference_service = InferenceService()
