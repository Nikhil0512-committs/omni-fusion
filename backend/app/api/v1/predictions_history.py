from fastapi import APIRouter, Query, HTTPException, Depends
from app.models.schemas import HistoryResponse, HistoryItem
from app.core.supabase_client import supabase
from app.core.auth import get_current_user
from app.models.enums import Role, LinkStatus
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/history", response_model=HistoryResponse)
async def get_history(limit: int = Query(20, le=100), offset: int = Query(0), user_data: dict = Depends(get_current_user)):
    try:
        user_id = user_data.get("auth").id
        role = user_data.get("profile").get("role")
        
        query = supabase.table('predictions').select('id, created_at, risk_score, streams_used, reports(id)', count='exact')
        
        if role == Role.PATIENT.value:
            query = query.eq('patient_id', user_id)
        elif role == Role.DOCTOR.value:
            links = supabase.table("doctor_patient_links").select("patient_id").eq("doctor_id", user_id).eq("status", LinkStatus.ACCEPTED.value).execute()
            patient_ids = [item["patient_id"] for item in links.data] if links.data else []
            if not patient_ids:
                return HistoryResponse(items=[], total=0)
            query = query.in_('patient_id', patient_ids)
            
        # Execute query with count='exact' to get both data and total count
        res = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        total_count = res.count if res.count else 0
        
        items = []
        for row in res.data:
            has_report = len(row.get('reports', [])) > 0
            
            items.append(HistoryItem(
                prediction_id=row['id'],
                created_at=row['created_at'],
                risk_score=row['risk_score'],
                streams_used=row['streams_used'],
                has_report=has_report
            ))
            
        return HistoryResponse(items=items, total=total_count)
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error fetching history.")
