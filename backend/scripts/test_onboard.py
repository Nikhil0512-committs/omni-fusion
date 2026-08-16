import os
import requests
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
sb = create_client(url, key)

try:
    res = sb.auth.sign_in_with_password({"email": "demo.test@omnifusion.demo", "password": "password123"})
    token = res.session.access_token

    payload = {
        "role": "PATIENT",
        "full_name": "Test User",
        "date_of_birth": None,
        "sex": "M",
        "height_cm": 180.0,
        "weight_kg": 80.0,
        "smoking_status": "Never",
        "alcohol_use": "Never",
        "exercise_frequency": "Rarely"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    r = requests.post("http://127.0.0.1:8001/api/v1/profiles/onboard", json=payload, headers=headers)
    print("Status:", r.status_code)
    print("Response:", r.text)
except Exception as e:
    print("Error:", e)
