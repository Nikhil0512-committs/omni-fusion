import os
import base64
import httpx
import json

api_key = os.popen("grep GEMINI_API_KEY backend/.env | cut -d '=' -f2").read().strip()
model_name = "gemini-flash-latest"
api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

with open("sample_blood_report.jpg", "rb") as f:
    b64_data = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "contents": [{
        "parts": [
            {"text": "What is this image?"},
            {
                "inlineData": {
                    "mimeType": "image/jpeg",
                    "data": b64_data
                }
            }
        ]
    }]
}

response = httpx.post(api_url, json=payload, headers={"Content-Type": "application/json"}, timeout=60.0)
print(response.status_code)
print(response.text)
