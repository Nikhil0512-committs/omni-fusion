from fastapi import APIRouter
from app.core.supabase_client import supabase, logger

router = APIRouter()

@router.get("/health")
async def health_check():
    db_healthy = False
    try:
        # A trivial query to check Supabase connectivity
        res = supabase.table('upload_sessions').select('id').limit(1).execute()
        db_healthy = True
    except Exception as e:
        logger.error(f"Health check failed to connect to Supabase: {e}")

    return {
        "status": "ok",
        "dependencies": {
            "supabase": "healthy" if db_healthy else "unhealthy"
        }
    }
