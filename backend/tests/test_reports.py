import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

@patch("app.api.v1.reports.pdf_service")
def test_generate_report_unsupported_language(mock_pdf_service):
    payload = {
        "patient_id": "test_id",
        "shap_data": {},
        "failure_analysis_summary": "test",
        "ecg_gradcam_heatmap_b64": ""
    }
    
    response = client.post("/api/v1/report/test-pred?lang=fr", json=payload)
    
    assert response.status_code == 400
    assert "Unsupported language code: fr" in response.json()["detail"]

@patch("app.api.v1.reports.copilot_service.generate_soap_note")
@patch("app.api.v1.reports.pdf_service")
def test_generate_report_supported_language(mock_pdf_service, mock_copilot_service):
    mock_pdf_service.generate_report.return_value = "/tmp/fake_report.pdf"
    mock_copilot_service.return_value = "Fake localized summary"
    
    # We need to mock os.remove and open for the fake file
    with patch("builtins.open", MagicMock()), patch("os.remove", MagicMock()):
        payload = {
            "patient_id": "test_id",
            "shap_data": {},
            "failure_analysis_summary": "test",
            "ecg_gradcam_heatmap_b64": ""
        }
        
        response = client.post("/api/v1/report/test_id?lang=hi", json=payload)
        
        assert response.status_code == 200
