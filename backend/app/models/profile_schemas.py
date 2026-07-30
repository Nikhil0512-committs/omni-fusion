from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import date, datetime

class ProfileCreate(BaseModel):
    role: str
    full_name: str
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    smoking_status: Optional[str] = None
    alcohol_use: Optional[str] = None
    exercise_frequency: Optional[str] = None
    family_history: Optional[Dict] = None
    diagnoses: Optional[Dict] = None
    medications: Optional[Dict] = None
    medical_registration_number: Optional[str] = None
    specialization: Optional[str] = None
    hospital: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    smoking_status: Optional[str] = None
    alcohol_use: Optional[str] = None
    exercise_frequency: Optional[str] = None
    family_history: Optional[Dict] = None
    diagnoses: Optional[Dict] = None
    medications: Optional[Dict] = None
    hospital: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class ProfileResponse(ProfileCreate):
    id: str
    bmi: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class LinkStatusUpdate(BaseModel):
    status: str

class DoctorNoteCreate(BaseModel):
    prediction_id: str
    note: str
    priority: str

class DoctorNoteResponse(DoctorNoteCreate):
    id: str
    doctor_id: str
    created_at: datetime
