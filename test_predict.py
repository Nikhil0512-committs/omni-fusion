import httpx
import json

payload = {
    "patient_id": "test",
    "ecg": [[0.0] * 1000] * 12,
    "is_ecg_only": False,
    "vitals": {
        "anchor_age": 45,
        "gender": 1,
        "Creatinine": 1.1,
        "Glucose": 100,
        "Potassium": 4.0,
        "Sodium": 135,
        "HR": 80,
        "SBP": 120,
        "DBP": 80,
        "RR": 16,
        "O2": 98
    }
}
r = httpx.post("http://localhost:8000/api/v1/predict", json=payload)
print(r.status_code)
print(r.text)
