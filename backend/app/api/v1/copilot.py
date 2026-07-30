from fastapi import APIRouter, Depends, HTTPException, Request
import logging

from app.core.auth import get_current_user
from app.models.enums import Role, LinkStatus
from app.models.schemas import CopilotRequest, CopilotResponse
from app.services.copilot_service import copilot_service
from app.core.supabase_client import supabase
from app.core.limiter import limiter

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/copilot/summarize", response_model=CopilotResponse)
@limiter.limit("5/minute")
async def summarize(request: Request, body: CopilotRequest, user_data: dict = Depends(get_current_user)):
    """Generate a clinical SOAP note using the Gemini API based on prediction artifacts."""
    # First get the prediction to ensure it exists and we have access to it
    # We query the predictions table to get the risk_score
    prediction_res = supabase.table("predictions").select("risk_score, patient_id").eq("id", body.prediction_id).execute()
    
    if not prediction_res.data:
        raise HTTPException(status_code=404, detail="Prediction not found")
        
    prediction = prediction_res.data[0]
    
    # Check IDOR Ownership
    user_id = user_data.get("auth").id
    role = user_data.get("profile").get("role")
    
    if role == Role.PATIENT.value and prediction["patient_id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    elif role == Role.DOCTOR.value:
        links = supabase.table("doctor_patient_links").select("id").eq("doctor_id", user_id).eq("patient_id", prediction["patient_id"]).eq("status", LinkStatus.ACCEPTED.value).execute()
        if not links.data:
            raise HTTPException(status_code=403, detail="Unauthorized: Not linked to this patient")

    # Next get the reports table for SHAP and Grad-CAM
    report_res = supabase.table("reports").select("shap_data, gradcam_ref").eq("prediction_id", body.prediction_id).execute()
    
    if not report_res.data:
        raise HTTPException(status_code=400, detail="Cannot generate copilot summary without report artifacts (SHAP/Grad-CAM). Please generate a report first.")
        
    report = report_res.data[0]
    
    try:
        soap_note = copilot_service.generate_soap_note(
            risk_score=prediction["risk_score"],
            shap_data=report["shap_data"],
            gradcam_b64=report.get("gradcam_ref", "")
        )
        return CopilotResponse(soap_note=soap_note)
    except Exception as e:
        logger.error(f"Copilot service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
