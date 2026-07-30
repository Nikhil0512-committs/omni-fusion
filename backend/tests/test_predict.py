import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "supabase" in data["dependencies"]
    assert data["dependencies"]["supabase"] == "healthy"

def test_predict_endpoint():
    # Use dummy values that match our test_user_id
    payload = {
        "patient_id": "test_user_id",
        "ecg": [[0.0] * 1000] * 12,
        "vitals": {
            "anchor_age": 65.0,
            "gender": 1,
            "Creatinine": 1.2,
            "Glucose": 105.0,
            "Potassium": 4.1,
            "Sodium": 138.0,
            "HR": 85.0,
            "SBP": 140.0,
            "DBP": 85.0,
            "RR": 18.0,
            "O2": 96.0
        },
        "historical": {
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
        }
    }
    
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["patient_id"] == "test_user_id"
    assert "risk_score" in data
    assert "shap_data" in data
    assert "ecg_gradcam_heatmap_b64" in data
    assert "failure_analysis_summary" in data
    assert data["streams_used"] == ["ecg", "vitals", "historical"]
    
    assert "Vital_HR" in data["shap_data"]

def test_predict_counterfactual():
    from unittest.mock import patch, MagicMock
    payload = {
        "base_request": {
            "patient_id": "test_user_id",
            "ecg": [[0.0]*1000]*12,
            "vitals": {
                "anchor_age": 50.0, "gender": 1.0, "Creatinine": 1.0, "Glucose": 100.0,
                "Potassium": 4.0, "Sodium": 140.0, "HR": 80.0, "SBP": 120.0, "DBP": 80.0,
                "RR": 16.0, "O2": 98.0
            }
        },
        "overrides": {
            "SBP": 160.0
        }
    }
    
    with patch("app.api.v1.predict.inference_service.predict") as mock_predict:
        # We simulate the reuse of the inference_service by mocking it
        mock_response = MagicMock()
        mock_response.prediction_id = "test-pred"
        mock_response.patient_id = "test-patient"
        mock_response.risk_score = 0.90
        mock_response.triage_tier = "Red"
        mock_response.shap_data = {}
        mock_response.ecg_gradcam_heatmap_b64 = "b64"
        mock_response.failure_analysis_summary = "test"
        mock_response.streams_used = ["ecg", "vitals"]
        mock_predict.return_value = mock_response
        
        # We rely on the global get_current_user override from conftest.py
        # which sets user id to "test_user_id" and role to "PATIENT".
        
        response = client.post("/api/v1/predict/counterfactual", json=payload)
        
        assert response.status_code == 200
        assert response.json()["prediction_id"] == "counterfactual_sim"
        # Verify that inference_service.predict was called with the modified SBP
        call_args = mock_predict.call_args[0][0]
        assert call_args.vitals.SBP == 160.0
        assert call_args.vitals.HR == 80.0 # unchanged
