import sys
import numpy as np
import torch
from app.services.inference_service import inference_service
from app.models.schemas import PredictRequest, VitalsInput

vitals_orig = VitalsInput(
    anchor_age=80, gender=1, Creatinine=3.0, Glucose=300, Potassium=5.5, Sodium=130,
    HR=110, SBP=90, DBP=50, RR=28, O2=85
)
# Make a fake ECG that might look sick
req = PredictRequest(
    patient_id="test_sick",
    ecg=np.random.normal(0, 1, (12, 1000)).tolist(),
    vitals=vitals_orig
)

def fast_predict(r, clip=None):
    vitals_arr_raw = np.array([[getattr(r.vitals, c) for c in inference_service.scaler_feature_order]], dtype=np.float32)
    vitals_arr = inference_service.vitals_scaler.transform(vitals_arr_raw).astype(np.float32)
    if clip:
        vitals_arr = np.clip(vitals_arr, -clip, clip)
    
    hist_arr = np.zeros((1, len(inference_service.scaler_feature_order)), dtype=np.float32)
    v_t = torch.tensor(vitals_arr).to('cpu')
    h_t = torch.tensor(hist_arr).unsqueeze(1).to('cpu')
    pat_ecg = torch.tensor(np.array(r.ecg, dtype=np.float32).reshape(1, 12, 1000)).to('cpu')
    
    # We must ensure model is on CPU for this quick test
    model = inference_service.model.to('cpu')
    with torch.no_grad():
        logits = model(pat_ecg, v_t, h_t)
        prob = torch.softmax(logits, dim=1).cpu().numpy()[0, 1]
    return float(prob)

orig_score = fast_predict(req)
print(f"Original score (no clip): {orig_score:.4f}")
print(f"Original score (clip 2.5): {fast_predict(req, 2.5):.4f}")

# Now apply user's overrides
user_overrides = {"SBP": 212, "HR": 125, "Glucose": 319, "RR": 35}
test_vitals = vitals_orig.model_copy()
for k, v in user_overrides.items():
    setattr(test_vitals, k, v)
test_req = PredictRequest(patient_id="test", ecg=req.ecg, vitals=test_vitals)

print(f"Override score (no clip): {fast_predict(test_req):.4f}")
print(f"Override score (clip 3.0): {fast_predict(test_req, 3.0):.4f}")
print(f"Override score (clip 2.5): {fast_predict(test_req, 2.5):.4f}")
print(f"Override score (clip 2.0): {fast_predict(test_req, 2.0):.4f}")

