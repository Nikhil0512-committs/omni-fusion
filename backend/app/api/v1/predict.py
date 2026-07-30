"""Single prediction endpoint for authenticated and manual inference flows."""

import logging
import uuid
import asyncio

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.concurrency import run_in_threadpool
from datetime import datetime, timedelta, timezone
import neurokit2 as nk
import numpy as np

from app.core.auth import get_current_user
from app.core.supabase_client import supabase
from app.core.limiter import limiter
from app.models.enums import LinkStatus, Role
from app.models.schemas import PredictRequest, PredictResponse, PredictCounterfactualRequest, VitalsInput
from app.services.inference_service import inference_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/predict", response_model=PredictResponse)
@limiter.limit("10/minute")
async def predict(request: Request, payload: PredictRequest, user_data: dict = Depends(get_current_user)):
    """Run inference and persist it only for an authenticated patient."""
    try:
        # Check for deduplication first
        if payload.offline_client_id:
            # Check if this offline_client_id was already synced
            existing = supabase.table("predictions").select("id").eq("raw_input_ref->>offline_client_id", payload.offline_client_id).execute()
            if existing.data:
                # Re-run inference just to get the artifacts, but don't persist
                prediction = await run_in_threadpool(inference_service.predict, payload)
                prediction.prediction_id = existing.data[0]["id"]
                return prediction
                
        if payload.is_ecg_only:
            prediction = PredictResponse(
                patient_id=payload.patient_id,
                risk_score=None,
                triage_tier=None,
                shap_data={},
                failure_analysis_summary=payload.ecg_abnormality or "ECG Analysis without vitals.",
                streams_used=["ECG Image Analysis"],
                ecg_abnormality=payload.ecg_abnormality
            )
        else:
            prediction = await run_in_threadpool(inference_service.predict, payload)
            if payload.ecg_abnormality:
                prediction.ecg_abnormality = payload.ecg_abnormality
            if payload.ecg_image_path or payload.ecg_abnormality:
                if not any("ecg" in s.lower() for s in prediction.streams_used):
                    prediction.streams_used.append("12-Lead ECG")
                
        prediction_id = str(uuid.uuid4())
        prediction.prediction_id = prediction_id
        
        db_risk_score = prediction.risk_score if prediction.risk_score is not None else -1.0
        
        raw_input_ref_common = {
            "patient_id": payload.patient_id,
            "has_vitals": not payload.is_ecg_only,
            "has_historical": payload.historical is not None,
            "has_upload_session": payload.upload_session_id is not None,
            "offline_client_id": payload.offline_client_id,
            "blood_image_path": payload.blood_image_path,
            "ecg_image_path": payload.ecg_image_path,
            "ecg_abnormality": payload.ecg_abnormality,
            "is_ecg_only": payload.is_ecg_only,
        }

        profile = user_data.get("profile") if user_data else None
        if not profile or profile.get("role") != Role.PATIENT.value:
            # Manual/test predictions remain persisted for report generation, but
            # are deliberately not linked to the UUID-only patient profile column.
            try:
                supabase.table("predictions").insert({
                    "id": prediction_id,
                    "upload_session_id": payload.upload_session_id,
                    "risk_score": db_risk_score,
                    "streams_used": prediction.streams_used,
                    "raw_input_ref": raw_input_ref_common,
                }).execute()
            except Exception as e:
                logger.warning(f"Could not persist manual prediction to Supabase (likely test env): {e}")
            return prediction

        patient_id = user_data.get("auth").id
        raw_input_ref = {**raw_input_ref_common, "patient_id": patient_id}
        links = supabase.table("doctor_patient_links").select("doctor_id").eq("patient_id", patient_id).eq("status", LinkStatus.ACCEPTED.value).execute()
        doctor_id = links.data[0].get("doctor_id") if links.data else None
        try:
            supabase.table("predictions").insert({
                "id": prediction_id,
                "upload_session_id": payload.upload_session_id,
                "risk_score": db_risk_score,
                "streams_used": prediction.streams_used,
                "raw_input_ref": raw_input_ref,
                "patient_id": patient_id,
                "doctor_id": doctor_id,
            }).execute()
            if doctor_id:
                if prediction.triage_tier == "Red":
                    # Duplicate suppression
                    six_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
                    recent_alerts = supabase.table("notifications") \
                        .select("created_at") \
                        .eq("user_id", doctor_id) \
                        .eq("type", "triage_red") \
                        .ilike("message", f"%{patient_id}%") \
                        .gte("created_at", six_hours_ago) \
                        .execute()
                        
                    if not recent_alerts.data:
                        supabase.table("notifications").insert({
                            "user_id": doctor_id,
                            "title": "CRITICAL: Red-Tier Patient Alert",
                            "message": f"Patient {patient_id} has a new Red-tier cardiovascular risk assessment ({prediction.risk_score:.2f}). Immediate review recommended.",
                            "type": "triage_red",
                        }).execute()
                else:
                    supabase.table("notifications").insert({
                        "user_id": doctor_id,
                        "title": "New Patient Prediction",
                        "message": f"Patient {patient_id} has completed a new cardiovascular assessment.",
                        "type": "new_prediction",
                    }).execute()
        except Exception as e:
            logger.warning(f"Could not persist authenticated prediction or notification to Supabase: {e}")
        return prediction
    except HTTPException:
        raise
    except Exception as error:
        logger.error("Error during prediction: %s", error)
        raise HTTPException(status_code=500, detail="Internal Server Error during prediction.") from error

@router.post("/predict/counterfactual", response_model=PredictResponse)
@limiter.limit("10/minute")
async def counterfactual_predict(request: Request, payload: PredictCounterfactualRequest, user_data: dict = Depends(get_current_user)):
    """Re-run inference using existing singleton model with overridden vitals. Does not persist to db."""
    try:
        base_req = payload.base_request
        # Apply overrides
        vitals_dict = base_req.vitals.model_dump()
        for k, v in payload.overrides.items():
            if k in vitals_dict:
                vitals_dict[k] = v
        
        # We need to construct a new PredictRequest with the overridden vitals.
        # But we must update the vitals object
        from app.models.schemas import VitalsInput
        base_req.vitals = VitalsInput(**vitals_dict)
        
        # Run inference (reuse singleton)
        prediction = await run_in_threadpool(inference_service.predict, base_req)
        # We don't save counterfactuals to the DB. They are just simulations.
        prediction.prediction_id = "counterfactual_sim"
        return prediction
    except Exception as error:
        logger.error("Error during counterfactual prediction: %s", error)
        raise HTTPException(status_code=400, detail="Invalid counterfactual request.") from error

@router.get("/demo-ecg")
async def get_demo_ecg():
    """Generate a realistic 12-lead synthetic ECG using neurokit2."""
    try:
        # Generate 1D ECG (duration 10s, 100Hz -> 1000 points) to match 10-second standard 12-lead
        base_ecg = nk.ecg_simulate(duration=10, sampling_rate=100, heart_rate=65)
        
        # Expand to 12 leads with varying amplitude, noise, and polarity to look like a real 12-lead
        leads = []
        for i in range(12):
            # Lead I, II, III, aVR, aVL, aVF, V1-V6
            amplitude = 0.5 + (i % 3) * 0.2
            noise = np.random.normal(0, 0.05, 1000)
            
            # aVR (index 3) and V1 (index 6) are typically mostly negative (inverted)
            polarity = -1 if i in [3, 6] else 1
            
            # Add some phase shift or morphology variation? Just polarity and amp is fine for demo
            lead = (base_ecg * amplitude * polarity) + noise
            leads.append(lead.tolist())
            
        return {"ecg": leads}
    except Exception as e:
        logger.error(f"Error generating demo ECG: {e}")
        raise HTTPException(status_code=500, detail="Error generating demo ECG.")
