from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

@patch("app.api.v1.copilot.supabase")
@patch("app.api.v1.copilot.copilot_service")
def test_copilot_success(mock_copilot_service, mock_supabase):
    # Mock supabase queries
    mock_pred_data = {"data": [{"risk_score": 0.85, "patient_id": "test_user_id"}]}
    mock_report_data = {"data": [{"shap_data": {"Vital_HR": 0.12}, "gradcam_ref": "b64"}]}
    
    # Setup chain
    mock_supabase.table().select().eq().execute.side_effect = [
        MagicMock(data=mock_pred_data["data"]),
        MagicMock(data=mock_report_data["data"])
    ]
    
    mock_copilot_service.generate_soap_note.return_value = "### Subjective\nPatient presents with..."
    
    response = client.post("/api/v1/copilot/summarize", json={"prediction_id": "pred-123"})
    assert response.status_code == 200
    assert response.json()["soap_note"] == "### Subjective\nPatient presents with..."
    mock_copilot_service.generate_soap_note.assert_called_once_with(
        risk_score=0.85,
        shap_data={"Vital_HR": 0.12},
        gradcam_b64="b64"
    )

@patch("app.api.v1.copilot.supabase")
@patch("app.api.v1.copilot.copilot_service")
def test_copilot_failure(mock_copilot_service, mock_supabase):
    mock_pred_data = {"data": [{"risk_score": 0.85, "patient_id": "test_user_id"}]}
    mock_report_data = {"data": [{"shap_data": {"Vital_HR": 0.12}, "gradcam_ref": "b64"}]}
    
    mock_supabase.table().select().eq().execute.side_effect = [
        MagicMock(data=mock_pred_data["data"]),
        MagicMock(data=mock_report_data["data"])
    ]
    
    mock_copilot_service.generate_soap_note.side_effect = Exception("API Timeout")
    
    response = client.post("/api/v1/copilot/summarize", json={"prediction_id": "pred-123"})
    assert response.status_code == 503
    assert "API Timeout" in response.json()["detail"]
