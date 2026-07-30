import os
import httpx
from app.core.config import settings

url = f"{settings.supabase_url}/auth/v1/admin/users"
headers = {
    "apikey": settings.supabase_service_role_key,
    "Authorization": f"Bearer {settings.supabase_service_role_key}",
    "Content-Type": "application/json"
}
data = {
    "email": "demo.test@omnifusion.demo",
    "password": "DemoPassword123!",
    "email_confirm": True
}
resp = httpx.post(url, headers=headers, json=data)
print(resp.status_code)
print(resp.text)
