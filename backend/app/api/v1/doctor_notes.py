"""Clinical note endpoints for connected doctors."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_role
from app.core.errors import handle_supabase_errors
from app.core.supabase_client import supabase
from app.models.enums import LinkStatus, Role
from app.models.profile_schemas import DoctorNoteCreate, DoctorNoteResponse

router = APIRouter()


@router.post("/notes", response_model=DoctorNoteResponse)
@handle_supabase_errors("add doctor note")
async def create_note(note: DoctorNoteCreate, user_data: dict = Depends(require_role([Role.DOCTOR]))):
    doctor_id = user_data.get("auth").id
    prediction = supabase.table("predictions").select("patient_id").eq("id", note.prediction_id).execute()
    if not prediction.data:
        raise HTTPException(status_code=404, detail="Prediction not found")
    patient_id = prediction.data[0]["patient_id"]
    link = supabase.table("doctor_patient_links").select("id").eq("doctor_id", doctor_id).eq("patient_id", patient_id).eq("status", LinkStatus.ACCEPTED.value).execute()
    if not link.data:
        raise HTTPException(status_code=403, detail="Not linked to this patient")
    data = note.model_dump()
    data["doctor_id"] = doctor_id
    result = supabase.table("doctor_notes").insert(data).execute()
    supabase.table("predictions").update({"doctor_reviewed": True, "doctor_note": note.note, "reviewed_at": "now()"}).eq("id", note.prediction_id).execute()
    supabase.table("notifications").insert({"user_id": patient_id, "title": "Doctor Review Added", "message": f"Your doctor has reviewed your prediction and left a {note.priority} note.", "type": "clinical_review"}).execute()
    return result.data[0]
