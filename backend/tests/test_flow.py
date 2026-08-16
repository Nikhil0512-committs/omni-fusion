import pytest
from fastapi.testclient import TestClient
from app.main import app
import json
import base64

client = TestClient(app)

def test_full_flow():
    # 1. Test Historical CSV Upload
    csv_data = "anchor_age,gender,Creatinine,Glucose,Potassium,Sodium,HR,SBP,DBP,RR,O2\n65,1,1.1,100,4.0,139,82,135,80,16,98\n"
    res = client.post("/api/v1/upload-historical", files={"file": ("test.csv", csv_data, "text/csv")})
    assert res.status_code == 200
    upload_res = res.json()
    assert "session_id" in upload_res
    session_id = upload_res["session_id"]
    
    # 2. Test Predict with session_id
    payload = {
        "patient_id": "patient_13",
        "ecg": [[0.0] * 1000] * 12,
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
        },
        "upload_session_id": session_id
    }
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    predict_res = res.json()
    assert "prediction_id" in predict_res
    prediction_id = predict_res["prediction_id"]
    
    # 3. Test Report Generation
    report_payload = {
        "patient_id": "patient_13",
        "shap_data": predict_res["shap_data"],
        "ecg_gradcam_heatmap_b64": predict_res["ecg_gradcam_heatmap_b64"],
        "failure_analysis_summary": predict_res["failure_analysis_summary"]
    }
    res = client.post(f"/api/v1/report/{prediction_id}", json=report_payload)
    assert res.status_code == 200
    report_res = res.json()
    assert "pdf_signed_url" in report_res
    assert report_res["pdf_signed_url"] != ""
    
    # 4. Test History Endpoint
    res = client.get("/api/v1/history?limit=5")
    assert res.status_code == 200
    history_res = res.json()
    assert history_res["total"] > 0
    assert len(history_res["items"]) > 0

def test_missing_stream_3():
    payload = {
        "patient_id": "patient_13",
        "ecg": [[0.0] * 1000] * 12,
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
        }
    }
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    assert res.json()["streams_used"] == ["ecg", "vitals"]

def test_malformed_csv():
    res = client.post("/api/v1/upload-historical", files={"file": ("test.txt", "not a csv", "text/plain")})
    assert res.status_code == 400
    
    res = client.post("/api/v1/upload-historical", files={"file": ("test.csv", b"\x00\x01\x02", "text/csv")})
    assert res.status_code == 400

