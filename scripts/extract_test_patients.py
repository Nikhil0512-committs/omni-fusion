import numpy as np
import pandas as pd
import json
import os

# Load val data
ecg_val = np.load('data/processed/ecg_val.npy')
vitals_val = pd.read_parquet('data/processed/vitals_val.parquet')
historical_val = pd.read_parquet('data/processed/historical_val.parquet')

# Get 3 distinct patients (indices 0, 5, 10)
indices = [0, 5, 10]

os.makedirs('frontend/test_data', exist_ok=True)

for i, idx in enumerate(indices):
    patient_id = f"real_val_patient_{idx}"
    
    # ECG shape is (N, 1000, 12), we need (12, 1000) for backend
    ecg_data = ecg_val[idx].T.tolist()
    
    # Vitals - convert row to dict
    vitals_row = vitals_val.iloc[idx].to_dict()
    
    # Ensure float/int
    for k, v in vitals_row.items():
        if isinstance(v, (np.float32, np.float64)):
            vitals_row[k] = float(v)
        elif isinstance(v, (np.int32, np.int64)):
            vitals_row[k] = int(v)
            
    # Historical data - save as CSV for upload
    hist_subset = historical_val.iloc[idx:idx+1]
    csv_path = f"frontend/test_data/historical_patient_{i+1}.csv"
    hist_subset.to_csv(csv_path, index=False)
    
    payload = {
        "patient_id": patient_id,
        "ecg": ecg_data,
        "vitals": vitals_row
    }
    
    with open(f"frontend/test_data/patient_{i+1}_payload.json", "w") as f:
        json.dump(payload, f)
        
print("Extracted 3 validation patients successfully.")
