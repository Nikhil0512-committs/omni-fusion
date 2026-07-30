import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
sb = create_client(url, key)

try:
    res = sb.table("profiles").insert({
        "id": "6d3bd6bf-df6b-4c0a-8716-0c88dbaf570b", # Real UUID
        "role": "PATIENT",
        "full_name": "Test User",
        "date_of_birth": None,
        "sex": "M",
        "height_cm": 180,
        "weight_kg": 80,
        "smoking_status": "Never",
        "alcohol_use": "Never",
        "exercise_frequency": "Rarely",
        "bmi": 24.69
    }).execute()
    print("Success:", res)
except Exception as e:
    print("Exception:", str(e))
