from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends, BackgroundTasks
from app.services.historical_service import historical_service
from app.services.blood_report_service import blood_report_service
from app.services.ecg_report_service import ecg_report_service
from app.models.schemas import UploadHistoricalResponse
from app.core.limiter import limiter
from app.core.auth import get_current_user
from app.core.supabase_client import supabase
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload-historical", response_model=UploadHistoricalResponse)
@limiter.limit("5/minute")
async def upload_historical(
    request: Request,
    file: UploadFile = File(...),
    user_data: dict = Depends(get_current_user)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        contents = await file.read()
        result = historical_service.process_csv_upload(contents)
        return UploadHistoricalResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing historical CSV upload: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during file processing.")

@router.post("/upload-blood-report", response_model=UploadHistoricalResponse)
@limiter.limit("5/minute")
async def upload_blood_report(
    request: Request,
    file: UploadFile = File(...),
    user_data: dict = Depends(get_current_user)
):
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and Image files (JPEG/PNG) are supported.")
        
    try:
        contents = await file.read()
        extracted_data = blood_report_service.parse_blood_report(contents, file.content_type)
        
        # We must return it in the format of UploadHistoricalResponse
        # with aggregatedData matching the VitalsInput schema mapping.
        # But VitalsInput schema mapping wants camelCase in frontend, but snake_case in backend.
        # UploadHistoricalResponse expects aggregated_data to be dict.
        # The frontend expects snake_case for aggregated_data keys because it uses `mapVitalsFromWire` which expects things like `anchor_age`, `gender`, `creatinine`, `glucose`, etc.
        
        # Let's map any missing vitals to default dummy values if not provided, just like historical_service does.
        # actually, mapVitalsFromWire in frontend will just take what we give it.
        import re
        def safe_float(val, default):
            if val is None:
                return float(default)
            if isinstance(val, (int, float)):
                return float(val)
            # Try to extract first float-like number from string
            match = re.search(r"[-+]?\d*\.\d+|\d+", str(val))
            if match:
                return float(match.group())
            return float(default)

        # Let's make sure it matches the backend schema for VitalsInput, or at least the wire format.
        aggregated_data = {
            "anchor_age": safe_float(extracted_data.get("anchor_age"), 45.0),
            "gender": safe_float(extracted_data.get("gender"), 1.0),
            "Creatinine": safe_float(extracted_data.get("creatinine"), 1.1),
            "Glucose": safe_float(extracted_data.get("glucose"), 100.0),
            "Potassium": safe_float(extracted_data.get("potassium"), 4.0),
            "Sodium": safe_float(extracted_data.get("sodium"), 139.0),
            "HR": safe_float(extracted_data.get("hr"), 82.0),
            "SBP": safe_float(extracted_data.get("sbp"), 135.0),
            "DBP": safe_float(extracted_data.get("dbp"), 80.0),
            "RR": safe_float(extracted_data.get("rr"), 16.0),
            "O2": safe_float(extracted_data.get("o2"), 98.0)
        }
        
        # Save image to Supabase
        file_name = f"blood_report_{uuid.uuid4().hex[:8]}.jpg"
        storage_path = f"uploads/images/{file_name}"
        supabase.storage.from_("reports").upload(storage_path, contents, file_options={"content-type": file.content_type})

        # Add image path to aggregated_data so it passes through PredictRequest
        aggregated_data["uploaded_image_path"] = storage_path

        session_id = str(uuid.uuid4())
        try:
            supabase.table('upload_sessions').insert({
                'id': session_id,
                'source_filename': file.filename,
                'row_count': 1,
                'imputation_summary': {"info": "Blood report parsed successfully."},
                'status': 'PROCESSED'
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save upload session to DB: {e}")

        return UploadHistoricalResponse(
            session_id=session_id,
            row_count=1,
            imputation_summary={"info": "Blood report parsed successfully."},
            status="success",
            aggregated_data=aggregated_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing blood report upload: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during blood report processing.")

@router.post("/upload-ecg-report", response_model=UploadHistoricalResponse)
@limiter.limit("5/minute")
async def upload_ecg_report(
    request: Request,
    file: UploadFile = File(...),
    user_data: dict = Depends(get_current_user)
):
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and Image files are supported.")
        
    try:
        contents = await file.read()
        extracted_data = ecg_report_service.parse_ecg_report(contents, file.content_type)
        
        file_name = f"ecg_report_{uuid.uuid4().hex[:8]}.jpg"
        storage_path = f"uploads/images/{file_name}"
        supabase.storage.from_("reports").upload(storage_path, contents, file_options={"content-type": file.content_type})

        aggregated_data = {
            "uploaded_image_path": storage_path,
            "ecg_abnormality": extracted_data.get("ecg_abnormality", "No specific abnormality extracted.")
        }
        
        session_id = str(uuid.uuid4())
        try:
            supabase.table('upload_sessions').insert({
                'id': session_id,
                'source_filename': file.filename,
                'row_count': 1,
                'imputation_summary': {"info": "ECG report parsed successfully."},
                'status': 'PROCESSED'
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save upload session to DB: {e}")

        return UploadHistoricalResponse(
            session_id=session_id,
            row_count=1,
            imputation_summary={"info": "ECG report parsed successfully."},
            status="success",
            aggregated_data=aggregated_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing ECG report upload: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during ECG report processing.")
