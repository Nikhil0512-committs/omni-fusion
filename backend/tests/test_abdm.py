import pytest
from app.services.abdm_service import abdm_service

def test_fhir_diagnostic_report_shape():
    patient = {"id": "patient-123"}
    predictions = [
        {"id": "pred-456", "risk_score": 0.85, "created_at": "2026-01-01T12:00:00Z"}
    ]
    
    report = abdm_service.generate_fhir_diagnostic_report(patient, predictions)
    
    assert report["resourceType"] == "DiagnosticReport"
    assert report["status"] == "final"
    assert "subject" in report
    assert report["subject"]["reference"] == "Patient/patient-123"
    assert "code" in report
    assert "result" in report
    assert "contained" in report
    
    assert len(report["contained"]) == 1
    obs = report["contained"][0]
    assert obs["resourceType"] == "Observation"
    assert obs["valueQuantity"]["value"] == 0.85
    assert obs["valueQuantity"]["unit"] == "%"
    
def test_fhir_diagnostic_report_empty():
    report = abdm_service.generate_fhir_diagnostic_report({"id": "p-1"}, [])
    assert report["resourceType"] == "DiagnosticReport"
    assert report["result"] == []
    assert report["contained"] == []
