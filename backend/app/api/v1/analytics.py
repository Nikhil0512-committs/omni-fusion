"""Role-aware dashboard analytics endpoints."""

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.core.config import HIGH_RISK_THRESHOLD_PCT
from app.core.errors import handle_supabase_errors
from app.core.supabase_client import supabase
from app.models.enums import LinkStatus, Role

router = APIRouter()


@router.get("/analytics")
@handle_supabase_errors("fetch analytics")
async def get_analytics(user_data: dict = Depends(get_current_user)):
    user_id = user_data.get("auth").id
    role = user_data.get("profile").get("role")
    if role == Role.PATIENT.value:
        predictions = supabase.table("predictions").select("created_at, risk_score").eq("patient_id", user_id).order("created_at").execute()
        if not predictions.data:
            return {"trends": [], "average_risk": 0, "highest_risk": 0}
        scores = [item["risk_score"] for item in predictions.data]
        return {"trends": predictions.data, "average_risk": sum(scores) / len(scores), "highest_risk": max(scores)}
    if role == Role.DOCTOR.value:
        links = supabase.table("doctor_patient_links").select("patient_id").eq("doctor_id", user_id).eq("status", LinkStatus.ACCEPTED.value).execute()
        patient_ids = [item["patient_id"] for item in links.data]
        if not patient_ids:
            return {
                "total_patients": 0, 
                "average_risk_all": 0, 
                "high_risk_patients": 0,
                "risk_distribution": {"low": 0, "medium": 0, "high": 0},
                "top_patients": [],
                "trends": []
            }
            
        # Get profiles to join names to top patients
        profiles_res = supabase.table("profiles").select("id, full_name, email").in_("id", patient_ids).execute()
        profile_map = {p["id"]: p for p in profiles_res.data} if profiles_res.data else {}
        
        predictions = supabase.table("predictions").select("patient_id, risk_score, created_at").in_("patient_id", patient_ids).execute()
        
        # Risk distribution calculation
        # Low < HIGH_RISK_THRESHOLD_PCT / 2, High >= HIGH_RISK_THRESHOLD_PCT
        low_count, medium_count, high_count = 0, 0, 0
        latest_patient_scores = {}
        
        for item in (predictions.data or []):
            pid = item["patient_id"]
            score = item["risk_score"]
            if pid not in latest_patient_scores or item["created_at"] > latest_patient_scores[pid]["created_at"]:
                latest_patient_scores[pid] = {"score": score, "created_at": item["created_at"]}
                
        scores = [v["score"] for v in latest_patient_scores.values()]
        
        for score in scores:
            if score >= HIGH_RISK_THRESHOLD_PCT:
                high_count += 1
            elif score < (HIGH_RISK_THRESHOLD_PCT / 2):
                low_count += 1
            else:
                medium_count += 1
                
        average = sum(scores) / len(scores) if scores else 0
        
        # Top patients sorting
        top_list = []
        for pid, data in latest_patient_scores.items():
            profile = profile_map.get(pid, {})
            top_list.append({
                "patient_id": pid,
                "name": profile.get("full_name") or "Unknown Patient",
                "email": profile.get("email") or "",
                "risk_score": data["score"],
                "last_assessment": data["created_at"]
            })
        top_list.sort(key=lambda x: x["risk_score"], reverse=True)
        top_patients = top_list[:5]

        return {
            "total_patients": len(patient_ids),
            "average_risk_all": average,
            "high_risk_patients": high_count,
            "risk_distribution": {"low": low_count, "medium": medium_count, "high": high_count},
            "top_patients": top_patients,
            "trends": predictions.data or []
        }
    return {}
