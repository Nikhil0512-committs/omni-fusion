import requests
import json
import math
import random
import pandas as pd

noisy_ecg = [[math.sin(j * 0.05 + i) * 0.5 + (random.random() * 0.2) for j in range(1000)] for i in range(12)]

for p in range(1, 4):
    df = pd.read_csv(f'frontend/test_data/historical_patient_{p}.csv')
    means = df.mean().to_dict()
    data = {
        "patient_id": f"patient_{p}",
        "ecg": noisy_ecg,
        "vitals": means,
        "historical": means
    }
    resp = requests.post('http://localhost:8000/api/v1/predict', json=data)
    print(f"Risk score for historical_patient_{p}:", resp.json()['risk_score'])
