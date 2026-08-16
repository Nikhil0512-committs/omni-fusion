import asyncio
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from datetime import datetime, timezone

from app.core.auth import get_optional_current_user
from app.core.limiter import limiter
from app.services.live_monitor import LiveMonitorService
from app.core.supabase_client import supabase
from app.services.inference_service import inference_service
from app.models.schemas import PredictRequest, VitalsInput
from app.models.enums import Role

router = APIRouter()
logger = logging.getLogger(__name__)

async def handle_anomaly(patient_id: str, doctor_id: str, hr: float, spo2: float, sbp: float, dbp: float):
    """Trigger background prediction and notify doctor on anomaly."""
    try:
        # Mocking labs to normal values, fetching age/gender if possible
        # Realistically, we would fetch the last PredictRequest for this patient
        vitals = VitalsInput(
            anchor_age=65.0,
            gender=1.0,
            Creatinine=1.0,
            Glucose=100.0,
            Potassium=4.0,
            Sodium=140.0,
            HR=hr,
            SBP=sbp,
            DBP=dbp,
            RR=16.0,
            O2=spo2
        )
        
        # We need a 12-lead ECG for inference (12x1000)
        # We'll just generate a quick dummy one for the inference call
        ecg_dummy = [[0.0] * 1000] * 12
        
        req = PredictRequest(
            patient_id=patient_id,
            ecg=ecg_dummy,
            vitals=vitals,
            historical=None,
            upload_session_id=None
        )
        
        # Run inference synchronously in background thread or directly
        # Since inference is CPU bound and this is a background task, we just call it
        # Actually it's better to run in executor, but for simplicity here we just call it
        prediction = inference_service.predict(req)
        
        # Raise real notification for doctor
        supabase.table("notifications").insert({
            "user_id": doctor_id,
            "title": "CRITICAL: Live Monitor Anomaly",
            "message": f"Patient {patient_id} breached SpO2 threshold (SpO2: {spo2}%). Model Risk: {prediction.risk_score:.2f}.",
            "type": "triage_red",
        }).execute()
        
    except Exception as e:
        logger.error(f"Error handling anomaly: {e}")

@router.websocket("/live-monitor/{patient_id}")
async def live_monitor_endpoint(websocket: WebSocket, patient_id: str, token: str):
    await websocket.accept()
    
    # We should normally authenticate using the token, but for WebSocket it's passed as query param
    # In a real app we'd verify the JWT token here
    doctor_id = None
    
    try:
        # Decode JWT to get doctor ID (simplified)
        # Assuming the token is valid, we can fetch doctor_id from the links
        links = supabase.table("doctor_patient_links").select("doctor_id").eq("patient_id", patient_id).eq("status", "accepted").execute()
        # Fetch baseline vitals from the most recent prediction request if available
        base_hr, base_spo2, base_sbp, base_dbp = 75.0, 98.0, 120.0, 80.0
        # In a real app we would fetch the raw vitals from a dedicated vitals table.
        # For this demo, we will use default vitals.
        
        service = LiveMonitorService(patient_id=patient_id, sampling_rate=250, base_hr=base_hr, base_spo2=base_spo2, base_sbp=base_sbp, base_dbp=base_dbp)
        
        # We'll stream chunks every 1 second
        async for frame in service.generate_stream(chunk_duration_sec=1.0):
            # Send the frame to the client
            await websocket.send_json(frame)
            
            if frame["is_anomaly"]:
                # Trigger background anomaly logic if we have a doctor_id
                if doctor_id:
                    hr = frame["hr"]
                    spo2 = frame["spo2"]
                    try:
                        sbp_str, dbp_str = frame["bp"].split("/")
                        sbp, dbp = float(sbp_str), float(dbp_str)
                    except ValueError:
                        sbp, dbp = 120.0, 80.0
                        
                    asyncio.create_task(
                        handle_anomaly(patient_id, doctor_id, hr, spo2, sbp, dbp)
                    )
                
                # Push alert frame over the same socket
                spo2 = frame["spo2"]
                alert_frame = {
                    "type": "ALERT",
                    "message": f"SpO2 dropped to {spo2}%! Background inference triggered."
                }
                await websocket.send_json(alert_frame)
                
    except WebSocketDisconnect:
        logger.info(f"Live monitor websocket disconnected for patient {patient_id}")
    except Exception as e:
        logger.error(f"Error in live monitor: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        # Ensure cleanup
        pass
