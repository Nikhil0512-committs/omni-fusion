import sys
import os
import random
import time
from datetime import datetime, timedelta
import asyncio

import neurokit2 as nk
import numpy as np

# Ensure backend path is configured
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import settings
from app.core.supabase_client import supabase
from app.models.schemas import PredictRequest, VitalsInput, HistoricalInput
from app.services.inference_service import inference_service
from app.services.pdf_service import pdf_service
from app.models.enums import Role, LinkStatus

# GUARDRAIL
if settings.environment == "production":
    print("ERROR: Cannot run seed script in production environment.")
    sys.exit(1)

DEMO_PASSWORD = "DemoPassword123!"

DOCTORS = [
    {
        "email": "demo.doctor1@omnifusion.demo",
        "full_name": "Dr. Ananya Sharma",
        "specialization": "Cardiology",
        "hospital": "Fortis Hospital",
        "medical_registration_number": "MED-1001",
        "phone": "+91-9876543210",
        "bio": "Senior Cardiologist with 15 years of experience."
    },
    {
        "email": "demo.doctor2@omnifusion.demo",
        "full_name": "Dr. Rajiv Menon",
        "specialization": "Internal Medicine",
        "hospital": "AIIMS-affiliated clinic",
        "medical_registration_number": "MED-1002",
        "phone": "+91-9876543211",
        "bio": "Internal Medicine specialist focusing on chronic conditions."
    },
    {
        "email": "demo.doctor3@omnifusion.demo",
        "full_name": "Dr. Priya Nair",
        "specialization": "Cardiology (fellow)",
        "hospital": "Apollo Hospital",
        "medical_registration_number": "MED-1003",
        "phone": "+91-9876543212",
        "bio": "Cardiology fellow passionate about AI in healthcare."
    }
]

PATIENTS = [
    {
        "email": "demo.patient1@omnifusion.demo",
        "full_name": "Ramesh Iyer",
        "age": 58,
        "sex": "Male",
        "height_cm": 170.0,
        "weight_kg": 85.0,
        "smoking_status": "Current",
        "alcohol_use": "Occasional",
        "exercise_frequency": "Rarely",
        "family_history": ["Diabetes"],
        "diagnoses": ["Hypertension", "Type 2 Diabetes"],
        "medications": ["Metformin", "Amlodipine"],
        "phone": "+91-9999900001",
        "bio": "Trending toward critical risk. Needs close monitoring.",
        "risk_profile": "critical",
        "links": [("demo.doctor1@omnifusion.demo", "accepted")]
    },
    {
        "email": "demo.patient2@omnifusion.demo",
        "full_name": "Sunita Verma",
        "age": 45,
        "sex": "Female",
        "height_cm": 160.0,
        "weight_kg": 65.0,
        "smoking_status": "Never",
        "alcohol_use": "None",
        "exercise_frequency": "Weekly",
        "family_history": ["CVD"],
        "diagnoses": [],
        "medications": [],
        "phone": "+91-9999900002",
        "bio": "Moderate risk, improving trend.",
        "risk_profile": "moderate",
        "links": [("demo.doctor1@omnifusion.demo", "accepted")]
    },
    {
        "email": "demo.patient3@omnifusion.demo",
        "full_name": "Arjun Kapoor",
        "age": 34,
        "sex": "Male",
        "height_cm": 180.0,
        "weight_kg": 75.0,
        "smoking_status": "Never",
        "alcohol_use": "None",
        "exercise_frequency": "Daily",
        "family_history": [],
        "diagnoses": [],
        "medications": [],
        "phone": "+91-9999900003",
        "bio": "Healthy baseline.",
        "risk_profile": "low",
        "links": [("demo.doctor2@omnifusion.demo", "accepted")]
    },
    {
        "email": "demo.patient4@omnifusion.demo",
        "full_name": "Meera Joshi",
        "age": 62,
        "sex": "Female",
        "height_cm": 155.0,
        "weight_kg": 70.0,
        "smoking_status": "Former",
        "alcohol_use": "None",
        "exercise_frequency": "Rarely",
        "family_history": ["CVD"],
        "diagnoses": ["Prior Cardiac Event", "Hyperlipidemia"],
        "medications": ["Atorvastatin", "Aspirin"],
        "phone": "+91-9999900004",
        "bio": "High risk, flagged by doctor.",
        "risk_profile": "high",
        "links": [("demo.doctor2@omnifusion.demo", "accepted")]
    },
    {
        "email": "demo.patient5@omnifusion.demo",
        "full_name": "Vikram Singh",
        "age": 50,
        "sex": "Male",
        "height_cm": 175.0,
        "weight_kg": 80.0,
        "smoking_status": "Never",
        "alcohol_use": "Occasional",
        "exercise_frequency": "Weekly",
        "family_history": [],
        "diagnoses": ["Borderline Hypertension"],
        "medications": [],
        "phone": "+91-9999900005",
        "bio": "Fluctuating trend.",
        "risk_profile": "moderate",
        "links": [("demo.doctor3@omnifusion.demo", "accepted"), ("demo.doctor1@omnifusion.demo", "pending")]
    }
]

def generate_ecg(risk_profile: str):
    """Generate a realistic 12-lead ECG (12x1000) using neurokit2."""
    if risk_profile == "critical":
        hr = 110
    elif risk_profile == "high":
        hr = 95
    elif risk_profile == "moderate":
        hr = 80
    else:
        hr = 65
    
    # Generate 1 lead and duplicate/scale to 12 leads for simplicity while maintaining shape
    sim_ecg = nk.ecg_simulate(duration=10, sampling_rate=100, heart_rate=hr)
    leads = []
    for i in range(12):
        scale = 1.0 - (i * 0.05)
        leads.append((sim_ecg * scale).tolist())
    return leads

def generate_vitals(patient: dict, step: int, total_steps: int):
    """Generate realistic vitals based on risk profile and trend."""
    risk = patient["risk_profile"]
    
    # Base ranges
    if risk == "critical":
        hr_base, sbp_base, glu_base, creat_base = 100, 160, 180, 1.5
    elif risk == "high":
        hr_base, sbp_base, glu_base, creat_base = 90, 140, 130, 1.2
    elif risk == "moderate":
        hr_base, sbp_base, glu_base, creat_base = 75, 125, 100, 1.0
    else:
        hr_base, sbp_base, glu_base, creat_base = 65, 115, 90, 0.9

    # Add trend
    progress = step / float(total_steps)
    if risk == "critical":
        # Worsening trend
        hr = hr_base + (progress * 15)
        sbp = sbp_base + (progress * 20)
        glu = glu_base + (progress * 30)
    elif risk == "moderate" and patient["full_name"] == "Sunita Verma":
        # Improving trend
        hr = hr_base - (progress * 5)
        sbp = sbp_base - (progress * 10)
        glu = glu_base - (progress * 10)
    else:
        # Slight fluctuation
        hr = hr_base + random.uniform(-2, 2)
        sbp = sbp_base + random.uniform(-5, 5)
        glu = glu_base + random.uniform(-5, 5)

    gender_val = 1.0 if patient["sex"] == "Female" else 0.0
    
    return VitalsInput(
        anchor_age=float(patient["age"]),
        gender=gender_val,
        Creatinine=creat_base + random.uniform(-0.1, 0.1),
        Glucose=glu,
        Potassium=4.0 + random.uniform(-0.2, 0.2),
        Sodium=140.0 + random.uniform(-1.0, 1.0),
        HR=hr,
        SBP=sbp,
        DBP=sbp - 40,
        RR=16.0 + random.uniform(-1, 1),
        O2=98.0 if risk == "low" else 95.0 + random.uniform(-2, 2)
    )

def upload_pdf_to_supabase(pdf_path: str, patient_id: str, prediction_id: str) -> str:
    """Upload PDF to Supabase Storage and return signed URL."""
    storage_path = f"{patient_id}/{prediction_id}.pdf"
    with open(pdf_path, "rb") as f:
        supabase.storage.from_("reports").upload(storage_path, f, file_options={"content-type": "application/pdf"})
    
    signed_url = supabase.storage.from_("reports").create_signed_url(storage_path, 86400 * 7) # 7 days
    return signed_url["signedURL"], storage_path

def seed_users():
    print("Starting seed script...")
    user_map = {}
    
    # 1. Create Doctors
    for d in DOCTORS:
        res = supabase.table("profiles").select("id").eq("email", d["email"]).execute()
        if len(res.data) > 0:
            print(f"Doctor {d['email']} already exists. Skipping creation.")
            user_map[d["email"]] = res.data[0]["id"]
            continue
            
        print(f"Creating Doctor {d['email']}...")
        import httpx
        url = f"{settings.supabase_url}/auth/v1/admin/users"
        headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json"
        }
        data = {
            "email": d["email"],
            "password": DEMO_PASSWORD,
            "email_confirm": True
        }
        resp = httpx.post(url, headers=headers, json=data)
        if resp.status_code not in (200, 201):
            print("ERROR creating user:", resp.text)
            resp.raise_for_status()
        uid = resp.json()["id"]
        user_map[d["email"]] = uid
        
        # Insert profile
        supabase.table("profiles").insert({
            "id": uid,
            "email": d["email"],
            "role": "DOCTOR",
            "full_name": d["full_name"],
            "specialization": d["specialization"],
            "hospital": d["hospital"],
            "medical_registration_number": d["medical_registration_number"],
            "phone": d["phone"],
            "bio": d["bio"]
        }).execute()

    # 2. Create Patients
    for p in PATIENTS:
        res = supabase.table("profiles").select("id").eq("email", p["email"]).execute()
        if len(res.data) > 0:
            print(f"Patient {p['email']} already exists. Skipping creation.")
            user_map[p["email"]] = res.data[0]["id"]
            continue
            
        print(f"Creating Patient {p['email']}...")
        import httpx
        url = f"{settings.supabase_url}/auth/v1/admin/users"
        headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json"
        }
        data = {
            "email": p["email"],
            "password": DEMO_PASSWORD,
            "email_confirm": True
        }
        resp = httpx.post(url, headers=headers, json=data)
        if resp.status_code not in (200, 201):
            print("ERROR creating user:", resp.text)
            resp.raise_for_status()
        uid = resp.json()["id"]
        user_map[p["email"]] = uid
        
        bmi = p["weight_kg"] / ((p["height_cm"]/100)**2)
        supabase.table("profiles").insert({
            "id": uid,
            "email": p["email"],
            "role": "PATIENT",
            "full_name": p["full_name"],
            "age": p["age"],
            "sex": p["sex"],
            "height_cm": p["height_cm"],
            "weight_kg": p["weight_kg"],
            "bmi": bmi,
            "smoking_status": p["smoking_status"],
            "alcohol_use": p["alcohol_use"],
            "exercise_frequency": p["exercise_frequency"],
            "family_history": p["family_history"],
            "diagnoses": p["diagnoses"],
            "medications": p["medications"],
            "phone": p["phone"],
            "bio": p["bio"]
        }).execute()

        # Create Predictions & History
        print(f"  Generating predictions for {p['full_name']}...")
        num_visits = 5
        now = datetime.utcnow()
        for i in range(num_visits):
            # Backdate
            visit_date = now - timedelta(days=(num_visits - i - 1) * 30)
            
            vitals = generate_vitals(p, i, num_visits)
            hist = HistoricalInput(**vitals.model_dump()) # Duplicate for simplicity if used
            ecg = generate_ecg(p["risk_profile"])
            
            req = PredictRequest(
                patient_id=uid,
                ecg=ecg,
                vitals=vitals,
                historical=hist
            )
            
            # Predict
            pred_res = inference_service.predict(req)
            
            # Insert Prediction
            ins_res = supabase.table("predictions").insert({
                "patient_id": uid,
                "risk_score": pred_res.risk_score,
                "streams_used": pred_res.streams_used,
                "created_at": visit_date.isoformat(),
                "raw_input_ref": {"vitals": vitals.model_dump(), "historical": hist.model_dump()}
            }).execute()
            
            pred_id = ins_res.data[0]["id"]
            
            # For the most recent visit (and maybe Meera's flagged visit), generate a Report
            if i == num_visits - 1 or (p["full_name"] == "Meera Joshi" and i == num_visits - 2):
                pdf_path = pdf_service.generate_report(pred_res.model_dump())
                signed_url, storage_path = upload_pdf_to_supabase(pdf_path, uid, pred_id)
                os.remove(pdf_path)
                
                supabase.table("reports").insert({
                    "prediction_id": pred_id,
                    "shap_data": pred_res.shap_data,
                    "gradcam_ref": "gradcam_b64", # store a ref or skip
                    "failure_analysis_text": pred_res.failure_analysis_summary,
                    "pdf_storage_path": storage_path,
                    "created_at": visit_date.isoformat()
                }).execute()
                
                # Insert Notification for patient
                supabase.table("notifications").insert({
                    "user_id": uid,
                    "title": "New Report Available",
                    "message": "Your latest risk prediction report is ready.",
                    "type": "report",
                    "created_at": visit_date.isoformat()
                }).execute()

                # Mock a doctor review for Meera Joshi
                if p["full_name"] == "Meera Joshi" and i == num_visits - 2:
                    doctor_email = p["links"][0][0]
                    doc_id = user_map.get(doctor_email)
                    if doc_id:
                        supabase.table("predictions").update({
                            "doctor_reviewed": True,
                            "reviewed_at": (visit_date + timedelta(days=1)).isoformat()
                        }).eq("id", pred_id).execute()
                        
                        supabase.table("doctor_notes").insert({
                            "prediction_id": pred_id,
                            "doctor_id": doc_id,
                            "note": "Patient exhibits elevated risk markers post-cardiac event. Adjusting statin dosage and scheduling follow-up.",
                            "priority": "urgent",
                            "created_at": (visit_date + timedelta(days=1)).isoformat()
                        }).execute()
                        
                        supabase.table("notifications").insert({
                            "user_id": uid,
                            "title": "Doctor Reviewed Prediction",
                            "message": "Dr. Rajiv Menon reviewed your prediction and left a note.",
                            "type": "review",
                            "created_at": (visit_date + timedelta(days=1)).isoformat()
                        }).execute()

    # 3. Create Links
    for p in PATIENTS:
        pat_uid = user_map.get(p["email"])
        for link in p["links"]:
            doc_email, status = link
            doc_uid = user_map.get(doc_email)
            if pat_uid and doc_uid:
                # Check if exists
                res = supabase.table("doctor_patient_links").select("id").eq("doctor_id", doc_uid).eq("patient_id", pat_uid).execute()
                if len(res.data) == 0:
                    supabase.table("doctor_patient_links").insert({
                        "doctor_id": doc_uid,
                        "patient_id": pat_uid,
                        "status": status
                    }).execute()
                    print(f"  Linked Patient {p['email']} to Doctor {doc_email} ({status})")

    print("Seed complete.")

if __name__ == "__main__":
    seed_users()
