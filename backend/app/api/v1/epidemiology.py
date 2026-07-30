from fastapi import APIRouter, Depends, HTTPException
import logging
from app.core.supabase_client import supabase
from app.core.auth import require_role
from app.models.enums import Role

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/heatmap")
async def get_epidemiology_heatmap(user_data: dict = Depends(require_role([Role.DOCTOR]))):
    """
    Returns aggregated risk predictions grouped by pincode/district.
    Strips out all per-patient identifying fields for public-health visualization.
    """
    try:
        # Join predictions with profiles to get location data
        # Aggregate logic is performed server-side
        result = (
            supabase.table("predictions")
            .select("risk_score, profiles(district, pincode)")
            .execute()
        )
        
        aggregates = {}
        for row in result.data or []:
            profile = row.get("profiles")
            if not profile:
                continue
                
            loc_key = profile.get("pincode") or profile.get("district") or "Unknown"
            if loc_key not in aggregates:
                aggregates[loc_key] = {"total_risk": 0.0, "count": 0}
                
            aggregates[loc_key]["total_risk"] += row.get("risk_score", 0.0)
            aggregates[loc_key]["count"] += 1
            
        # Compute averages
        heatmap_data = []
        for loc, data in aggregates.items():
            avg_risk = data["total_risk"] / data["count"] if data["count"] > 0 else 0
            heatmap_data.append({
                "location": loc,
                "average_risk": avg_risk,
                "sample_size": data["count"]
            })
            
        return {"data": heatmap_data}
        
    except Exception as e:
        logger.error(f"Error generating epidemiology heatmap: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate epidemiology data")
