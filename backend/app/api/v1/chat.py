from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.auth import require_role
from app.core.errors import handle_supabase_errors
from app.core.supabase_client import supabase
from app.models.enums import Role, LinkStatus

router = APIRouter()

class ChatMessageInput(BaseModel):
    content: str

@router.get("/chat/messages/{other_user_id}")
@handle_supabase_errors("fetch chat messages")
async def get_chat_messages(other_user_id: str, user_data: dict = Depends(require_role([Role.PATIENT, Role.DOCTOR]))):
    user_id = user_data.get("auth").id
    
    # Verify they have an accepted connection
    link = supabase.table("doctor_patient_links").select("id").or_(
        f"and(doctor_id.eq.{user_id},patient_id.eq.{other_user_id}),and(doctor_id.eq.{other_user_id},patient_id.eq.{user_id})"
    ).eq("status", LinkStatus.ACCEPTED.value).execute()
    
    if not link.data:
        raise HTTPException(status_code=403, detail="You are not connected to this user.")
        
    messages = supabase.table("chat_messages").select("*").or_(
        f"and(sender_id.eq.{user_id},receiver_id.eq.{other_user_id}),and(sender_id.eq.{other_user_id},receiver_id.eq.{user_id})"
    ).order("created_at", desc=False).execute()
    
    return messages.data

@router.post("/chat/messages/{other_user_id}")
@handle_supabase_errors("send chat message")
async def send_chat_message(other_user_id: str, payload: ChatMessageInput, user_data: dict = Depends(require_role([Role.PATIENT, Role.DOCTOR]))):
    user_id = user_data.get("auth").id
    
    # Verify they have an accepted connection
    link = supabase.table("doctor_patient_links").select("id").or_(
        f"and(doctor_id.eq.{user_id},patient_id.eq.{other_user_id}),and(doctor_id.eq.{other_user_id},patient_id.eq.{user_id})"
    ).eq("status", LinkStatus.ACCEPTED.value).execute()
    
    if not link.data:
        raise HTTPException(status_code=403, detail="You are not connected to this user.")
        
    new_message = {
        "sender_id": user_id,
        "receiver_id": other_user_id,
        "content": payload.content,
        "read": False
    }
    
    response = supabase.table("chat_messages").insert(new_message).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to send message.")
        
    # Trigger notification for the receiver
    supabase.table("notifications").insert({
        "user_id": other_user_id,
        "title": "New Message",
        "message": f"You received a new message.",
        "type": "chat_message",
        "read": False
    }).execute()
        
    return response.data[0]
