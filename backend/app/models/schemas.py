from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class VitalsInput(BaseModel):
    anchor_age: float = 65.0
    gender: float = 1.0
    Creatinine: float = 1.1
    Glucose: float = 100.0
    Potassium: float = 4.0
    Sodium: float = 139.0
    HR: float = 82.0
    SBP: float = 135.0
    DBP: float = 80.0
    RR: float = 16.0
    O2: float = 98.0

class HistoricalInput(BaseModel):
    anchor_age: float = 65.0
    gender: float = 1.0
    Creatinine: float = 1.1
    Glucose: float = 100.0
    Potassium: float = 4.0
    Sodium: float = 139.0
    HR: float = 82.0
    SBP: float = 135.0
    DBP: float = 80.0
    RR: float = 16.0
    O2: float = 98.0

class PredictRequest(BaseModel):
    patient_id: str
    ecg: List[List[float]] = Field(..., description="12-lead ECG signal array, shape (12, 1000)")
    vitals: Optional[VitalsInput] = None
    historical: Optional[HistoricalInput] = None
    upload_session_id: Optional[str] = None
    offline_client_id: Optional[str] = None
    is_ecg_only: bool = False
    blood_image_path: Optional[str] = None
    ecg_image_path: Optional[str] = None
    ecg_abnormality: Optional[str] = None

class PredictCounterfactualRequest(BaseModel):
    base_request: PredictRequest
    overrides: Dict[str, float]

class PredictResponse(BaseModel):
    prediction_id: str = ""
    patient_id: str
    risk_score: Optional[float] = None
    triage_tier: Optional[str] = None
    shap_data: Dict[str, float]
    ecg_gradcam_heatmap_b64: Optional[str] = None
    ecg_gradcam_data: Optional[List[float]] = None
    raw_ecg: Optional[List[List[float]]] = None
    failure_analysis_summary: str
    streams_used: List[str]
    ecg_abnormality: Optional[str] = None

class UploadHistoricalResponse(BaseModel):
    session_id: str
    row_count: int
    imputation_summary: Dict[str, Any]
    status: str
    aggregated_data: Optional[Dict[str, Any]] = None

class ReportResponse(BaseModel):
    prediction_id: str
    risk_score: float
    shap_data: Dict[str, float]
    failure_analysis_text: str
    pdf_storage_path: str
    pdf_signed_url: str

class HistoryItem(BaseModel):
    prediction_id: str
    created_at: str
    risk_score: float
    streams_used: List[str]
    has_report: bool

class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int

class ReportRequest(BaseModel):
    patient_id: str
    shap_data: Dict[str, float]
    ecg_gradcam_heatmap_b64: str
    ecg_gradcam_data: Optional[List[float]] = None
    raw_ecg: Optional[List[List[float]]] = None
    failure_analysis_summary: str

class CopilotRequest(BaseModel):
    prediction_id: str

class CopilotResponse(BaseModel):
    soap_note: str
