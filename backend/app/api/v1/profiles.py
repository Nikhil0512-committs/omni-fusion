from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.supabase_client import supabase, logger
from app.core.auth import get_current_user
from app.models.profile_schemas import ProfileCreate, ProfileUpdate, ProfileResponse
from app.core.errors import handle_supabase_errors
from app.core.limiter import limiter
from app.models.enums import Role

router = APIRouter()

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    if not weight_kg or not height_cm or height_cm <= 0:
        return None
    height_m = height_cm / 100
    return round(weight_kg / (height_m * height_m), 2)

@router.get("/profiles/me", response_model=ProfileResponse)
async def get_my_profile(user_data: dict = Depends(get_current_user)):
    profile = user_data.get("profile")
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/profiles/onboard", response_model=ProfileResponse)
@limiter.limit("5/minute")
@handle_supabase_errors("create profile")
async def onboard_profile(request: Request, profile_data: ProfileCreate, user_data: dict = Depends(get_current_user)):
    user = user_data.get("auth")
    existing_profile = user_data.get("profile")
    
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
        
    data = profile_data.model_dump(exclude_unset=True, mode='json')
    
    # Validate Role
    if data.get("role") not in [Role.PATIENT.value, Role.DOCTOR.value]:
        raise HTTPException(status_code=400, detail="Invalid role")
        
    if data.get("role") == Role.DOCTOR.value:
        if not data.get("medical_registration_number") or not data.get("medical_registration_number").strip():
            raise HTTPException(status_code=400, detail="medical_registration_number is required for DOCTOR role")
            
    data["id"] = user.id
    
    # Auto-populate email from the authenticated user
    if not data.get("email") and hasattr(user, "email"):
        data["email"] = user.email
    elif not data.get("email") and isinstance(user, dict) and "email" in user:
        data["email"] = user["email"]
    
    if "weight_kg" in data and "height_cm" in data:
        data["bmi"] = calculate_bmi(data["weight_kg"], data["height_cm"])
        
    res = supabase.table("profiles").insert(data).execute()
    if not res.data:
        raise RuntimeError("Insertion failed")
    return res.data[0]

@router.put("/profiles/me", response_model=ProfileResponse)
@handle_supabase_errors("update profile")
async def update_profile(profile_data: ProfileUpdate, user_data: dict = Depends(get_current_user)):
    user = user_data.get("auth")
    profile = user_data.get("profile")
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    data = profile_data.model_dump(exclude_unset=True, mode='json')
    
    # Recalculate BMI if needed
    weight = data.get("weight_kg", profile.get("weight_kg"))
    height = data.get("height_cm", profile.get("height_cm"))
    if weight and height:
        data["bmi"] = calculate_bmi(weight, height)
        
    res = supabase.table("profiles").update(data).eq("id", user.id).execute()
    if not res.data:
        raise RuntimeError("Update failed")
    return res.data[0]
