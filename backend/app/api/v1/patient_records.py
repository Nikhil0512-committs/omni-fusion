"""Detailed records available to a patient's connected doctor."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_role
from app.core.errors import handle_supabase_errors
from app.core.supabase_client import supabase
from app.models.enums import LinkStatus, Role
from app.services.forecasting import ForecastingService
from datetime import datetime
import uuid
from pydantic import BaseModel

router = APIRouter()


@router.get("/patients/{patient_id}/record")
@handle_supabase_errors("fetch patient record")
async def get_patient_record(patient_id: str, user_data: dict = Depends(require_role([Role.DOCTOR]))):
    doctor_id = user_data.get("auth").id
    link = supabase.table("doctor_patient_links").select("id").eq("doctor_id", doctor_id).eq("patient_id", patient_id).eq("status", LinkStatus.ACCEPTED.value).execute()
    if not link.data:
        raise HTTPException(status_code=403, detail="You are not connected to this patient")
    profile = supabase.table("profiles").select("*").eq("id", patient_id).single().execute()
    predictions = supabase.table("predictions").select("id,created_at,risk_score,streams_used,doctor_reviewed,reports(id,created_at,pdf_storage_path,gradcam_ref,shap_data,failure_analysis_text),doctor_notes(id,note,priority,created_at)").eq("patient_id", patient_id).order("created_at", desc=True).execute()
    for prediction in predictions.data or []:
        for report in prediction.get("reports") or []:
            path = report.get("pdf_storage_path")
            if path:
                try:
                    signed = supabase.storage.from_("reports").create_signed_url(path, 3600)
                    report["download_url"] = signed.get("signedURL") or signed.get("signedUrl") or ""
                except Exception:
                    pass
            gradcam_path = report.get("gradcam_ref")
            if gradcam_path and gradcam_path != "embedded_in_pdf":
                try:
                    signed_asset = supabase.storage.from_("reports").create_signed_url(gradcam_path, 3600)
                    asset_url = signed_asset.get("signedURL") or signed_asset.get("signedUrl") or ""
                    if gradcam_path.endswith(".json"):
                        report["interactive_data_url"] = asset_url
                    else:
                        report["ecg_image_url"] = asset_url
                except Exception:
                    pass
    return {"profile": profile.data, "predictions": predictions.data or []}

@router.get("/patients/{patient_id}/forecast")
@handle_supabase_errors("fetch patient forecast")
async def get_patient_forecast(patient_id: str, user_data: dict = Depends(require_role([Role.DOCTOR]))):
    doctor_id = user_data.get("auth").id
    link = supabase.table("doctor_patient_links").select("id").eq("doctor_id", doctor_id).eq("patient_id", patient_id).eq("status", LinkStatus.ACCEPTED.value).execute()
    if not link.data:
        raise HTTPException(status_code=403, detail="You are not connected to this patient")
        
    predictions = supabase.table("predictions").select("created_at,risk_score").eq("patient_id", patient_id).order("created_at", desc=False).execute()
    
    historical_scores = []
    historical_dates = []
    
    for pred in predictions.data or []:
        historical_scores.append(pred["risk_score"])
        try:
            # Parse ISO string
            dt = datetime.fromisoformat(pred["created_at"].replace('Z', '+00:00'))
            historical_dates.append(dt)
        except Exception:
            pass
            
    result = ForecastingService.generate_forecast(historical_scores, historical_dates)
    return result

class PrescriptionInput(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    notes: str = ""

@router.post("/patients/{patient_id}/prescriptions")
@handle_supabase_errors("add prescription")
async def add_prescription(patient_id: str, prescription: PrescriptionInput, user_data: dict = Depends(require_role([Role.DOCTOR]))):
    doctor_id = user_data.get("auth").id
    link = supabase.table("doctor_patient_links").select("id").eq("doctor_id", doctor_id).eq("patient_id", patient_id).eq("status", LinkStatus.ACCEPTED.value).execute()
    if not link.data:
        raise HTTPException(status_code=403, detail="You are not connected to this patient")
        
    profile_req = supabase.table("profiles").select("medications").eq("id", patient_id).single().execute()
    medications = profile_req.data.get("medications") or []
    
    new_med = {
        "id": str(uuid.uuid4()),
        "medicationName": prescription.medication_name,
        "dosage": prescription.dosage,
        "frequency": prescription.frequency,
        "duration": prescription.duration,
        "notes": prescription.notes,
        "createdAt": datetime.utcnow().isoformat()
    }
    medications.append(new_med)
    
    supabase.table("profiles").update({"medications": medications}).eq("id", patient_id).execute()
    return {"message": "Prescription added successfully", "prescription": new_med}
