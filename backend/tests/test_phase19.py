import pytest
from fastapi.testclient import TestClient
import uuid
from unittest.mock import MagicMock
from app.main import app
from app.core.auth import get_current_user

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def patient_headers():
    return {"Authorization": "Bearer fake-token"}

@pytest.fixture
def doctor_headers():
    return {"Authorization": "Bearer fake-token"}

def test_language_validation(client: TestClient, patient_headers: dict):
    # Need a dummy prediction ID
    prediction_id = str(uuid.uuid4())
    payload = {
        "patient_id": "test_patient",
        "shap_data": {"Vital": 0.5},
        "ecg_gradcam_heatmap_b64": "dummy",
        "failure_analysis_summary": "Test"
    }

    # Test invalid language
    response = client.post(
        f"/api/v1/report/{prediction_id}?lang=fr",
        json=payload,
        headers=patient_headers
    )
    assert response.status_code == 400
    assert "Unsupported language" in response.json()["detail"]

def test_offline_deduplication(client: TestClient, patient_headers: dict):
    payload = {
        "patient_id": "test_patient",
        "ecg": [[0.0] * 1000] * 12,
        "vitals": {
            "anchor_age": 45,
            "gender": 1,
            "Creatinine": 1.0,
            "Glucose": 100,
            "Potassium": 4.0,
            "Sodium": 140,
            "HR": 75,
            "SBP": 120,
            "DBP": 80,
            "RR": 16,
            "O2": 98
        },
        "offline_client_id": f"off_{uuid.uuid4()}"
    }

    # First request
    res1 = client.post("/api/v1/predict", json=payload, headers=patient_headers)
    assert res1.status_code == 200
    id1 = res1.json()["prediction_id"]

    # Second request with same offline_client_id
    res2 = client.post("/api/v1/predict", json=payload, headers=patient_headers)
    assert res2.status_code == 200
    id2 = res2.json()["prediction_id"]

    # IDs should match due to deduplication
    assert id1 == id2

def test_epidemiology_heatmap(client: TestClient, doctor_headers: dict):
    # Override auth to pretend to be a doctor
    app.dependency_overrides[get_current_user] = lambda: {
        "auth": MagicMock(id="doctor_id"),
        "profile": {"role": "DOCTOR"}
    }
    try:
        response = client.get("/api/v1/epidemiology/heatmap", headers=doctor_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        if len(data) > 0:
            assert "location" in data[0]
            assert "average_risk" in data[0]
            assert "sample_size" in data[0]
    finally:
        # Restore auth back to patient (as set in conftest)
        app.dependency_overrides[get_current_user] = lambda: {
            "auth": MagicMock(id="test_user_id"),
            "profile": {"role": "PATIENT"}
        }
