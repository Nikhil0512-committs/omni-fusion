import sys
import numpy as np
import torch
from app.services.inference_service import inference_service
from app.models.schemas import PredictRequest, VitalsInput
import time

vitals_orig = VitalsInput(
    anchor_age=65, gender=1, Creatinine=1.2, Glucose=100, Potassium=4.0, Sodium=140,
    HR=80, SBP=120, DBP=80, RR=16, O2=98
)
req = PredictRequest(
    patient_id="test",
    ecg=np.zeros((12, 1000)).tolist(),
    vitals=vitals_orig
)

# Monkeypatch predict to only do the forward pass, ignore SHAP and GradCAM for speed
def fast_predict(req):
    vitals_arr_raw = np.array([[getattr(req.vitals, c) for c in inference_service.scaler_feature_order]], dtype=np.float32)
    vitals_arr = inference_service.vitals_scaler.transform(vitals_arr_raw).astype(np.float32)
    if req.historical:
        hist_arr_raw = np.array([[getattr(req.historical, c) for c in inference_service.scaler_feature_order]], dtype=np.float32)
        hist_arr = inference_service.vitals_scaler.transform(hist_arr_raw).astype(np.float32)
    else:
        hist_arr = np.zeros((1, len(inference_service.scaler_feature_order)), dtype=np.float32)
    v_t = torch.tensor(vitals_arr).to(inference_service.model.device if hasattr(inference_service.model, 'device') else 'cpu')
    h_t = torch.tensor(hist_arr).unsqueeze(1).to(v_t.device)
    pat_ecg = torch.tensor(np.array(req.ecg, dtype=np.float32).reshape(1, 12, 1000)).to(v_t.device)
    with torch.no_grad():
        logits = inference_service.model(pat_ecg, v_t, h_t)
        prob = torch.softmax(logits, dim=1).cpu().numpy()[0, 1]
    return float(prob)

orig_score = fast_predict(req)
print(f"Original score: {orig_score}")

for k in ['HR', 'SBP', 'Glucose']:
    for v in [50, 150, 200, 300, 400]:
        test_vitals = vitals_orig.model_copy()
        setattr(test_vitals, k, v)
        test_req = PredictRequest(patient_id="test", ecg=np.zeros((12, 1000)).tolist(), vitals=test_vitals)
        score = fast_predict(test_req)
        print(f"Override {k}={v} => {score:.6f}")

