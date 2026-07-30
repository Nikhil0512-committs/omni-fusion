from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.auth import get_current_user
from app.core.errors import handle_supabase_errors
from app.core.supabase_client import supabase

router = APIRouter()

class Notification(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    read: bool
    created_at: datetime

class PaginatedNotifications(BaseModel):
    items: List[Notification]
    total: int
    unread_count: int

@router.get("/notifications", response_model=PaginatedNotifications)
@handle_supabase_errors("fetch notifications")
async def get_notifications(
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    unread_only: bool = Query(False),
    user_data: dict = Depends(get_current_user)
):
    user_id = user_data.get("auth").id

    # Get total count
    count_query = supabase.table("notifications").select("*", count="exact").eq("user_id", user_id)
    if unread_only:
        count_query = count_query.eq("read", False)
    count_res = count_query.execute()
    total_count = count_res.count if count_res.count is not None else 0

    # Get unread count (for badge)
    unread_count_res = supabase.table("notifications").select("*", count="exact").eq("user_id", user_id).eq("read", False).execute()
    unread_count = unread_count_res.count if unread_count_res.count is not None else 0

    # Get actual data
    data_query = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + limit - 1)
    if unread_only:
        data_query = data_query.eq("read", False)
    
    res = data_query.execute()

    return {
        "items": res.data or [],
        "total": total_count,
        "unread_count": unread_count
    }

@router.patch("/notifications/{notification_id}/read")
@handle_supabase_errors("mark notification read")
async def mark_notification_read(notification_id: str, user_data: dict = Depends(get_current_user)):
    user_id = user_data.get("auth").id
    # RLS guarantees we can only update our own notifications, but we still explicitly filter by user_id
    res = supabase.table("notifications").update({"read": True}).eq("id", notification_id).eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True, "notification": res.data[0]}

@router.patch("/notifications/read-all")
@handle_supabase_errors("mark all notifications read")
async def mark_all_notifications_read(user_data: dict = Depends(get_current_user)):
    user_id = user_data.get("auth").id
    res = supabase.table("notifications").update({"read": True}).eq("user_id", user_id).eq("read", False).execute()
    return {"success": True, "updated_count": len(res.data or [])}
