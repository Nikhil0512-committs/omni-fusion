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
    filename_lower = (file.filename or "").lower()
    content_type = file.content_type
    if not content_type or content_type == "application/octet-stream":
        if filename_lower.endswith(".pdf"):
            content_type = "application/pdf"
        elif filename_lower.endswith((".jpg", ".jpeg")):
            content_type = "image/jpeg"
        elif filename_lower.endswith(".png"):
            content_type = "image/png"

    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if content_type not in allowed_types and not filename_lower.endswith((".pdf", ".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Only PDF and Image files (JPEG/PNG) are supported.")
        
    try:
        contents = await file.read()
        extracted_data = blood_report_service.parse_blood_report(contents, content_type or "image/jpeg")
        
        import re
        def safe_float(val, default):
            if val is None:
                return float(default)
            if isinstance(val, (int, float)):
                return float(val)
            match = re.search(r"[-+]?\d*\.\d+|\d+", str(val))
            if match:
                return float(match.group())
            return float(default)

        extracted_fields = []
        aggregated_data = {}

        field_mapping = {
            "anchor_age": ("anchor_age", 45.0),
            "gender": ("gender", 1.0),
            "creatinine": ("Creatinine", 1.1),
            "glucose": ("Glucose", 100.0),
            "potassium": ("Potassium", 4.0),
            "sodium": ("Sodium", 139.0),
            "hr": ("HR", None),
            "sbp": ("SBP", None),
            "dbp": ("DBP", None),
            "rr": ("RR", None),
            "o2": ("O2", None)
        }

        for raw_key, (target_key, fallback) in field_mapping.items():
            val = extracted_data.get(raw_key) if extracted_data else None
            if val is not None:
                parsed_val = safe_float(val, fallback if fallback is not None else 0.0)
                aggregated_data[target_key] = parsed_val
                extracted_fields.append(target_key)
            elif fallback is not None:
                aggregated_data[target_key] = float(fallback)
                extracted_fields.append(target_key)

        aggregated_data["extracted_fields"] = extracted_fields
        
        # Save image to Supabase storage safely
        try:
            file_name = f"blood_report_{uuid.uuid4().hex[:8]}.jpg"
            storage_path = f"uploads/images/{file_name}"
            supabase.storage.from_("reports").upload(storage_path, contents, file_options={"content-type": content_type or "image/jpeg"})
            aggregated_data["uploaded_image_path"] = storage_path
        except Exception as storage_err:
            logger.warning(f"Could not save blood report image to storage: {storage_err}")

        session_id = str(uuid.uuid4())
        try:
            supabase.table('upload_sessions').insert({
                'id': session_id,
                'source_filename': file.filename or "blood_report.jpg",
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
        logger.error(f"Error processing blood report upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error during blood report processing.")

@router.post("/upload-ecg-report", response_model=UploadHistoricalResponse)
@limiter.limit("5/minute")
async def upload_ecg_report(
    request: Request,
    file: UploadFile = File(...),
    user_data: dict = Depends(get_current_user)
):
    filename_lower = (file.filename or "").lower()
    content_type = file.content_type
    if not content_type or content_type == "application/octet-stream":
        if filename_lower.endswith(".pdf"):
            content_type = "application/pdf"
        elif filename_lower.endswith((".jpg", ".jpeg")):
            content_type = "image/jpeg"
        elif filename_lower.endswith(".png"):
            content_type = "image/png"

    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if content_type not in allowed_types and not filename_lower.endswith((".pdf", ".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Only PDF and Image files are supported.")
        
    try:
        contents = await file.read()
        extracted_data = ecg_report_service.parse_ecg_report(contents, content_type or "image/jpeg")
        
        storage_path = None
        try:
            file_name = f"ecg_report_{uuid.uuid4().hex[:8]}.jpg"
            storage_path = f"uploads/images/{file_name}"
            supabase.storage.from_("reports").upload(storage_path, contents, file_options={"content-type": content_type or "image/jpeg"})
        except Exception as storage_err:
            logger.warning(f"Could not save ECG report image to storage: {storage_err}")

        aggregated_data = {
            "ecg_abnormality": (extracted_data or {}).get("ecg_abnormality", "No specific abnormality extracted.")
        }
        if storage_path:
            aggregated_data["uploaded_image_path"] = storage_path
        
        session_id = str(uuid.uuid4())
        try:
            supabase.table('upload_sessions').insert({
                'id': session_id,
                'source_filename': file.filename or "ecg_report.jpg",
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
        logger.error(f"Error processing ECG report upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error during ECG report processing.")
