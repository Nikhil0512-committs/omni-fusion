import os
import json
import base64
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
from captum.attr import LayerGradCam

torch.manual_seed(42)
np.random.seed(42)

device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device: {device}")

# ----------------- BASE MODELS -----------------
class ResBlock1D(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=5, stride=stride, padding=2, bias=False)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=5, stride=1, padding=2, bias=False)
        self.bn2 = nn.BatchNorm1d(out_channels)
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm1d(out_channels)
            )
    def forward(self, x):
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        return self.relu(out)

class ResNet1D(nn.Module):
    def __init__(self, in_channels, num_classes, depth, dropout):
        super().__init__()
        self.in_channels = 16
        self.conv1 = nn.Conv1d(in_channels, 16, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm1d(16)
        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)
        layers = []
        channels = 16
        for i in range(depth):
            out_channels = channels * 2 if i > 0 else channels
            stride = 2 if i > 0 else 1
            layers.append(ResBlock1D(self.in_channels, out_channels, stride))
            self.in_channels = out_channels
            channels = out_channels
        self.layer = nn.Sequential(*layers)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(self.in_channels, num_classes)
    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.maxpool(x)
        x = self.layer(x)
        x = torch.mean(x, dim=2)
        x = self.dropout(x)
        return self.fc(x)

class VitalsMLP(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        layers = []
        in_dim = input_dim
        for _ in range(num_layers):
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            in_dim = hidden_dim
        layers.append(nn.Linear(in_dim, 2))
        self.net = nn.Sequential(*layers)
    def forward(self, x):
        return self.net(x)

class HistoricalGRU(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        self.gru = nn.GRU(input_size=input_dim, hidden_size=hidden_dim, num_layers=num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0.0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 2)
    def forward(self, x):
        out, _ = self.gru(x)
        last_out = out[:, -1, :]
        last_out = self.dropout(last_out)
        return self.fc(last_out)

class OmniFusionNet(nn.Module):
    def __init__(self, model_ecg, model_vitals, model_hist, ecg_dim, vitals_dim, hist_dim):
        super().__init__()
        self.ecg_net = model_ecg
        self.vitals_net = model_vitals
        self.hist_net = model_hist
        self.total_dim = ecg_dim + vitals_dim + hist_dim
        self.fusion_mlp = nn.Sequential(
            nn.Linear(self.total_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 2)
        )
    def forward(self, x_ecg, x_vitals, x_hist):
        e_ecg = self.ecg_net(x_ecg)
        e_vitals = self.vitals_net(x_vitals)
        e_hist = self.hist_net(x_hist)
        hist_sum = torch.sum(torch.abs(x_hist), dim=(1,2), keepdim=True)
        mask = (hist_sum > 0).float().squeeze(2)
        e_hist = e_hist * mask
        fused = torch.cat([e_ecg, e_vitals, e_hist], dim=1)
        return self.fusion_mlp(fused)

# ----------------- LOAD MODELS -----------------
with open('models/checkpoints/ecg_branch_config.json', 'r') as f:
    cfg_ecg = json.load(f)
model_ecg = ResNet1D(12, cfg_ecg['num_classes'], cfg_ecg['depth'], cfg_ecg['dropout'])

with open('models/checkpoints/vitals_branch_config.json', 'r') as f:
    cfg_vitals = json.load(f)
model_vitals = VitalsMLP(cfg_vitals['input_dim'], cfg_vitals['hidden_dim'], cfg_vitals['num_layers'], cfg_vitals['dropout'])

with open('models/checkpoints/historical_branch_config.json', 'r') as f:
    cfg_hist = json.load(f)
model_hist = HistoricalGRU(cfg_hist['input_dim'], cfg_hist['hidden_dim'], cfg_hist['num_layers'], cfg_hist['dropout'])

# Extract embedding sizes
ecg_emb_dim = model_ecg.fc.in_features
vitals_emb_dim = model_vitals.net[-1].in_features
hist_emb_dim = model_hist.fc.in_features

model_ecg.fc = nn.Identity()
model_vitals.net[-1] = nn.Identity()
model_hist.fc = nn.Identity()

model_fusion = OmniFusionNet(model_ecg, model_vitals, model_hist, ecg_emb_dim, vitals_emb_dim, hist_emb_dim).to(device)
model_fusion.load_state_dict(torch.load('models/exported/omni_fusion_final.pt', weights_only=True, map_location=device))
model_fusion.eval()

# ----------------- LOAD DATA -----------------
print("Loading Data for Analysis...")
df_vitals_train = pd.read_parquet('data/processed/vitals_train.parquet')
df_vitals_val = pd.read_parquet('data/processed/vitals_val.parquet')
df_hist_val = pd.read_parquet('data/processed/historical_val.parquet')

ecg_val_all = np.load('data/processed/ecg_val.npy').astype(np.float32)
ecg_val = ecg_val_all[:len(df_vitals_val)]

target_col = 'hospital_expire_flag'
feature_cols = [c for c in df_vitals_val.columns if c != target_col]

vitals_val = df_vitals_val[feature_cols].values.astype(np.float32)
hist_val = df_hist_val[feature_cols].values.astype(np.float32)[:, np.newaxis, :]
y_val = df_vitals_val[target_col].values.astype(np.int64)
ecg_val_t = torch.tensor(ecg_val).transpose(1, 2)

# Create background data for SHAP KernelExplainer
# We'll use K-Means summaries of training vitals
import shap
bg_vitals = df_vitals_train[feature_cols].values.astype(np.float32)
bg_tabular = np.concatenate([bg_vitals, bg_vitals], axis=1) # 11 vitals + 11 historical
bg_summary = shap.sample(bg_tabular, 10)
print("SHAP background sampled.")

# Directory for outputs
os.makedirs('xai_outputs', exist_ok=True)

# Find misclassified samples
print("Running Inference...")
with torch.no_grad():
    v_t = torch.tensor(vitals_val).to(device)
    h_t = torch.tensor(hist_val).to(device)
    e_t = ecg_val_t.to(device)
    logits = model_fusion(e_t, v_t, h_t)
    probs = torch.softmax(logits, dim=1).cpu().numpy()[:, 1]
    preds = (probs > 0.5).astype(int)

# Pick 3 samples: True Positive, False Positive (or False Negative), True Negative
# Note: In the dummy dataset, there may not be any positive cases (all 0s). 
# We'll just take 1 False Positive if exists, else the ones with highest prediction error.
errors = np.abs(probs - y_val)
sample_indices = np.argsort(errors)[-3:] # top 3 highest errors (worst classified)

output_schema = {}
feature_names = [f"Vital_{c}" for c in feature_cols] + [f"Hist_{c}" for c in feature_cols]

layer_gc = LayerGradCam(model_fusion, model_fusion.ecg_net.layer[-1])

for idx in sample_indices:
    patient_id = f"patient_{idx}"
    print(f"Analyzing {patient_id}...")
    
    pat_ecg = ecg_val_t[idx:idx+1].to(device)
    pat_vitals = v_t[idx:idx+1]
    pat_hist = h_t[idx:idx+1]
    true_label = y_val[idx]
    pred_prob = probs[idx]
    
    # 1. SHAP for Tabular
    def predict_fn(tabular_array):
        v = tabular_array[:, :len(feature_cols)]
        h = tabular_array[:, len(feature_cols):]
        v_t = torch.tensor(v, dtype=torch.float32).to(device)
        h_t = torch.tensor(h, dtype=torch.float32).unsqueeze(1).to(device)
        e_t = pat_ecg.repeat(tabular_array.shape[0], 1, 1)
        with torch.no_grad():
            logits = model_fusion(e_t, v_t, h_t)
            p = torch.softmax(logits, dim=1).cpu().numpy()[:, 1]
        return p

    explainer = shap.KernelExplainer(predict_fn, bg_summary)
    pat_tabular = np.concatenate([vitals_val[idx:idx+1], vitals_val[idx:idx+1]], axis=1) # Note: historical features are same as vitals just with missing imputed. Using vitals_val for both.
    shap_vals = explainer.shap_values(pat_tabular)
    
    # Generate SHAP waterfall
    shap_exp = shap.Explanation(values=shap_vals[0], base_values=explainer.expected_value, data=pat_tabular[0], feature_names=feature_names)
    plt.figure()
    shap.plots.waterfall(shap_exp, show=False)
    shap_path = f"xai_outputs/{patient_id}_shap.png"
    plt.savefig(shap_path, bbox_inches='tight')
    plt.close()
    
    # 2. Captum Grad-CAM for ECG
    # We attribute w.r.t class 1 (mortality)
    attr = layer_gc.attribute(inputs=pat_ecg, additional_forward_args=(pat_vitals, pat_hist), target=1)
    attr = F.interpolate(attr, size=1000, mode='linear').squeeze().cpu().detach().numpy()
    
    # Plot heatmap
    ecg_signal = pat_ecg[0, 0, :].cpu().numpy() # take lead 0
    plt.figure(figsize=(10, 3))
    plt.plot(ecg_signal, color='black', linewidth=1)
    
    # Overlay heatmap
    extent = [0, 1000, np.min(ecg_signal)-0.5, np.max(ecg_signal)+0.5]
    plt.imshow(attr[np.newaxis, :], cmap='jet', aspect='auto', alpha=0.5, extent=extent)
    plt.colorbar(label='Grad-CAM Activation')
    plt.title(f"{patient_id} ECG Grad-CAM (Target=1)")
    gc_path = f"xai_outputs/{patient_id}_gradcam.png"
    plt.savefig(gc_path, bbox_inches='tight')
    plt.close()
    
    with open(gc_path, "rb") as image_file:
        gc_b64 = base64.b64encode(image_file.read()).decode('utf-8')
    
    # 3. Failure Analysis Summary
    is_misclassified = (int(pred_prob > 0.5) != true_label)
    summary = ""
    
    shap_dict = {feature_names[i]: float(shap_vals[0][i]) for i in range(len(feature_names))}
    
    if is_misclassified:
        sorted_features = sorted(shap_dict.items(), key=lambda x: x[1])
        top_pushing = sorted_features[-2:] # Top 2 pushing towards 1
        top_pulling = sorted_features[:2]  # Top 2 pulling towards 0
        
        pred_str = "High Risk (Mortality)" if pred_prob > 0.5 else "Low Risk (Survival)"
        true_str = "High Risk (Mortality)" if true_label == 1 else "Low Risk (Survival)"
        
        summary = f"Model incorrectly predicted {pred_str} (True label was {true_str}). "
        
        if pred_prob > 0.5:
            summary += f"It overly weighted {top_pushing[1][0]} and {top_pushing[0][0]} towards risk, "
            summary += f"while underestimating the protective impact of {top_pulling[0][0]}."
        else:
            summary += f"It overly relied on {top_pulling[0][0]} and {top_pulling[1][0]} to predict safety, "
            summary += f"while ignoring the risk indicators from {top_pushing[1][0]}."
            
    output_schema[patient_id] = {
        "true_label": int(true_label),
        "predicted_prob": float(pred_prob),
        "shap_values": shap_dict,
        "ecg_gradcam_heatmap_b64": gc_b64,
        "failure_analysis_summary": summary
    }

with open('xai_outputs/xai_schema.json', 'w') as f:
    json.dump(output_schema, f, indent=4)

print("XAI Analysis complete. Output schema written to xai_outputs/xai_schema.json")
