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

# We can mock the transform function safely
orig_scaler = inference_service.vitals_scaler

class MockScaler:
    def __init__(self, orig, bound):
        self.orig = orig
        self.bound = bound
    def transform(self, X):
        out = self.orig.transform(X)
        return np.clip(out, -self.bound, self.bound)

inference_service.vitals_scaler = MockScaler(orig_scaler, 4.0)
res_clip4 = original_predict(req)
print(f"With clipping to [-4, 4]: {res_clip4.risk_score}")

inference_service.vitals_scaler = MockScaler(orig_scaler, 3.0)
res_clip3 = original_predict(req)
print(f"With clipping to [-3, 3]: {res_clip3.risk_score}")

inference_service.vitals_scaler = MockScaler(orig_scaler, 2.0)
res_clip2 = original_predict(req)
print(f"With clipping to [-2, 2]: {res_clip2.risk_score}")

