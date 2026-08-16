from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

app.dependency_overrides = {}
from app.core.auth import get_current_user
async def mock_get_current_user():
    class DummyAuth:
        id = "test-patient-id"
    return {"profile": {"role": "patient"}, "auth": DummyAuth()}
app.dependency_overrides[get_current_user] = mock_get_current_user

ecg_data = [[0.0] * 1000 for _ in range(12)]
payload = {
    "patient_id": "test-patient-id",
    "ecg": ecg_data,
    "vitals": {
        "anchor_age": 65.0,
        "gender": 1,
        "Creatinine": 1.1,
        "Glucose": 100.0,
        "Potassium": 4.0,
        "Sodium": 139.0,
        "HR": 82.0,
        "SBP": 135.0,
        "DBP": 80.0,
        "RR": 16.0,
        "O2": 98.0
    },
    "is_ecg_only": False
}

response = client.post("/api/v1/predict", json=payload)
print("STATUS CODE:", response.status_code)
print("RESPONSE:", response.json())
