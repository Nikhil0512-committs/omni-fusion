import sys
import numpy as np
import torch
from app.services.inference_service import inference_service
from app.models.schemas import PredictRequest, VitalsInput

vitals_orig = VitalsInput(
    anchor_age=65, gender=1, Creatinine=1.2, Glucose=100, Potassium=4.0, Sodium=140,
    HR=80, SBP=120, DBP=80, RR=16, O2=98
)
req = PredictRequest(
    patient_id="test",
    ecg=np.zeros((12, 1000)).tolist(),
    vitals=vitals_orig
)

orig_score = inference_service.predict(req).risk_score
print(f"Original score: {orig_score}")

for k in ['HR', 'SBP', 'Glucose']:
    for v in [50, 150, 200, 300]:
        test_vitals = vitals_orig.model_copy()
        setattr(test_vitals, k, v)
        test_req = PredictRequest(patient_id="test", ecg=np.zeros((12, 1000)).tolist(), vitals=test_vitals)
        score = inference_service.predict(test_req).risk_score
        print(f"Override {k}={v} => {score}")

