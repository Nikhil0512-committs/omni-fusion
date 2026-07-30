from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from app.core.supabase_client import supabase
from app.core.auth import get_current_user
from app.core.limiter import limiter
from app.services.abdm_service import abdm_service

router = APIRouter()

class VerifyAbhaRequest(BaseModel):
    abha_id: str

class ConsentRequest(BaseModel):
    purpose: str
    duration_hours: int = 24

@router.post("/verify-abha")
@limiter.limit("5/minute")
def verify_abha(request: Request, req: VerifyAbhaRequest, user: dict = Depends(get_current_user)):
    """Simulates ABHA ID verification for the sandbox environment."""
    # In a real environment, this would call the ABDM Gateway M3 API.
    if not req.abha_id or len(req.abha_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid ABHA ID format.")
    
    return {
        "status": "success",
        "message": "ABHA ID verified (Sandbox Mode)",
        "linked_patient": {
            "name": user["profile"].get("full_name", "Unknown"),
            "abha_address": f"{req.abha_id}@sbx"
        }
    }

@router.post("/consent")
@limiter.limit("5/minute")
def grant_consent(request: Request, req: ConsentRequest, user: dict = Depends(get_current_user)):
    """Creates a time-limited consent record for sharing data via ABDM."""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=req.duration_hours)
    
    res = supabase.table("abdm_consents").insert({
        "patient_id": user["auth"].id,
        "purpose": req.purpose,
        "status": "active",
        "expires_at": expires_at.isoformat()
    }).execute()
    
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create consent record")
        
    return {"status": "success", "consent_id": res.data[0]["id"], "expires_at": expires_at.isoformat()}

@router.get("/records/{patient_id}")
@limiter.limit("5/minute")
def get_abdm_records(request: Request, patient_id: str, user: dict = Depends(get_current_user)):
    """
    Returns FHIR R4 DiagnosticReport representing the patient's records.
    Requires active consent if requested by a third party. For now, sandbox mode
    allows the patient themselves to fetch it directly.
    """
    if user["auth"].id != patient_id:
        if user["profile"].get("role") == "DOCTOR":
            links = supabase.table("doctor_patient_links").select("id").eq("doctor_id", user["auth"].id).eq("patient_id", patient_id).eq("status", "accepted").execute()
            if not links.data:
                raise HTTPException(status_code=403, detail="Unauthorized: Not linked to this patient")
        else:
            raise HTTPException(status_code=403, detail="Unauthorized to view these records")
        
    profile_res = supabase.table("profiles").select("*").eq("id", patient_id).single().execute()
    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Patient profile not found")
        
    predictions_res = supabase.table("predictions").select("*").eq("patient_id", patient_id).order("created_at", desc=True).limit(10).execute()
    
    fhir_report = abdm_service.generate_fhir_diagnostic_report(
        patient=profile_res.data,
        predictions=predictions_res.data or []
    )
    
    return fhir_report
