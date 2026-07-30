import sys
import numpy as np
import torch
from app.services.inference_service import inference_service
from app.models.schemas import PredictRequest, VitalsInput

vitals = VitalsInput(
    anchor_age=65, gender=1, Creatinine=1.2, Glucose=319, Potassium=4.0, Sodium=140,
    HR=125, SBP=212, DBP=87, RR=35, O2=92
)
req = PredictRequest(
    patient_id="test",
    ecg=np.zeros((12, 1000)).tolist(),
    vitals=vitals
)

# Monkeypatch to test clipping
original_predict = inference_service.predict

# Run without clipping (current behavior)
res = original_predict(req)
print(f"Without clipping: {res.risk_score}")

# Let's see what happens if we clip
raw_vitals_arr = np.array([[getattr(req.vitals, c) for c in inference_service.scaler_feature_order]], dtype=np.float32)
scaled_vitals = inference_service.vitals_scaler.transform(raw_vitals_arr).astype(np.float32)
clipped_vitals = np.clip(scaled_vitals, -3.0, 3.0)

# We can mock the transform function
class MockScaler:
    def transform(self, X):
        orig = inference_service.vitals_scaler.transform(X)
        return np.clip(orig, -4.0, 4.0)
inference_service.vitals_scaler = MockScaler()

res_clipped = original_predict(req)
print(f"With clipping to [-4, 4]: {res_clipped.risk_score}")

class MockScaler3:
    def transform(self, X):
        orig = inference_service.vitals_scaler_orig.transform(X)
        return np.clip(orig, -3.0, 3.0)
inference_service.vitals_scaler_orig = inference_service.vitals_scaler # it's already MockScaler, need to reset
import joblib
import os
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
scaler_path = os.path.join(base_dir, 'models', 'checkpoints', 'vitals_scaler.pkl')
inference_service.vitals_scaler_orig = joblib.load(scaler_path)
inference_service.vitals_scaler = MockScaler3()

res_clipped3 = original_predict(req)
print(f"With clipping to [-3, 3]: {res_clipped3.risk_score}")

