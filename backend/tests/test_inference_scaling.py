import os
import joblib
import numpy as np
from app.models.schemas import PredictRequest, VitalsInput, HistoricalInput
from app.services.inference_service import inference_service

def test_inference_scaling_applies_correctly():
    """
    Test that the InferenceService correctly loads and applies the StandardScaler,
    and that unscaled raw vitals do not saturate the model (yielding 0.0 or 1.0).
    """
    
    # 1. Create a "normal" patient profile
    normal_vitals = VitalsInput(
        anchor_age=40, gender=0, Creatinine=0.9, Glucose=90.0,
        Potassium=4.0, Sodium=140.0, HR=70.0, SBP=120.0,
        DBP=80.0, RR=16.0, O2=98.0
    )
    
    # 2. Create an "abnormal" patient profile
    abnormal_vitals = VitalsInput(
        anchor_age=85, gender=1, Creatinine=2.5, Glucose=350.0,
        Potassium=6.5, Sodium=125.0, HR=130.0, SBP=180.0,
        DBP=110.0, RR=28.0, O2=88.0
    )
    
    # Common ECG (zeros) and no historical for this test, focusing purely on vitals
    ecg = [[0.0] * 1000] * 12
    
    req_normal = PredictRequest(
        patient_id="test_normal",
        ecg=ecg,
        vitals=normal_vitals,
        historical=None
    )
    
    req_abnormal = PredictRequest(
        patient_id="test_abnormal",
        ecg=ecg,
        vitals=abnormal_vitals,
        historical=None
    )
    
    res_normal = inference_service.predict(req_normal)
    res_abnormal = inference_service.predict(req_abnormal)
    
    # 3. Assert scores are not saturated to 0.0 or 1.0
    # 6 decimal places check
    assert round(res_normal.risk_score, 6) not in (0.000000, 1.000000), f"Normal score saturated: {res_normal.risk_score}"
    assert round(res_abnormal.risk_score, 6) not in (0.000000, 1.000000), f"Abnormal score saturated: {res_abnormal.risk_score}"
    
    # 4. Assert that the abnormal profile has a materially higher risk score
    # We expect some difference. If it's a small difference, the model might need retraining, 
    # but given the scale of abnormality, it should be visibly higher.
    assert res_abnormal.risk_score > res_normal.risk_score, f"Expected abnormal risk > normal, got {res_abnormal.risk_score} <= {res_normal.risk_score}"

def test_artifacts_exist():
    """
    Test that the required inference artifacts are correctly persisted.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    models_dir = os.path.join(base_dir, 'models')
    
    scaler_path = os.path.join(models_dir, 'checkpoints', 'vitals_scaler.pkl')
    feature_order_path = os.path.join(models_dir, 'checkpoints', 'vitals_scaler_feature_order.pkl')
    shap_bg_path = os.path.join(models_dir, 'checkpoints', 'shap_background.npy')
    knn_imputer_path = os.path.join(models_dir, 'checkpoints', 'historical_knn_imputer.pkl')
    
    assert os.path.exists(scaler_path), "Scaler artifact missing"
    assert os.path.exists(feature_order_path), "Feature order artifact missing"
    assert os.path.exists(shap_bg_path), "SHAP background missing"
    assert os.path.exists(knn_imputer_path), "KNN imputer missing"
