import requests
payload = {
    "role": "PATIENT",
    "full_name": "Test User",
    "date_of_birth": None,
    "sex": "M",
    "height_cm": None,
    "weight_kg": None,
    "smoking_status": "Never",
    "alcohol_use": "Never",
    "exercise_frequency": "Rarely"
}
headers = {
    "Content-Type": "application/json"
}
# We don't have a token, so we'll expect 401. Wait, I need a token to hit the endpoint.
# Let's get a token using supabase anon key.
import os
from supabase import create_client
url = "https://wvwzfhbohtbqxpiypioo.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2d3pmaGJvaHRicXhwaXlwaW9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1ODY1MDgsImV4cCI6MjA5OTE2MjUwOH0.8P7yGm8HPj7mfPo0Sh-zO6RDPmIuBcDckTBE7gJRB9Y"
sb = create_client(url, key)
res = sb.auth.sign_in_with_password({"email": "demo.test@omnifusion.demo", "password": "password123"})
headers["Authorization"] = f"Bearer {res.session.access_token}"

r = requests.post("http://127.0.0.1:8001/api/v1/profiles/onboard", json=payload, headers=headers)
print(r.status_code, r.text)
