#!/usr/bin/env python3
import sys
import os

# Add backend to path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from fastapi.testclient import TestClient
from app.main import app

def test_unauthenticated_access():
    client = TestClient(app)
    
    endpoints = [
        ("POST", "/api/v1/predict", {}),
        ("POST", "/api/v1/predict/counterfactual", {}),
        ("POST", "/api/v1/copilot/summarize", {"prediction_id": "123"}),
        ("POST", "/api/v1/report/123", {}),
        ("POST", "/api/v1/clinical/notes", {"prediction_id": "123", "note": "test", "priority": "normal"}),
        ("POST", "/api/v1/upload-historical", None),
        ("POST", "/api/v1/abdm/verify-abha", {"abha_id": "123"}),
        ("GET", "/api/v1/abdm/records/123", None),
    ]

    failed = False
    for method, url, json_payload in endpoints:
        print(f"Testing {method} {url} without JWT...")
        try:
            if method == "POST":
                if "upload" in url:
                    res = client.post(url, files={"file": ("test.csv", "a,b,c")})
                else:
                    res = client.post(url, json=json_payload)
            else:
                res = client.get(url)

            # In FastAPI, missing Depends(get_current_user) throws 401 Unauthorized or 403 Forbidden
            # predict.py uses get_optional_current_user, so it won't throw 401, but we might want to check it separately.
            if res.status_code not in [401, 403]:
                print(f"  ❌ FAILED: Expected 401/403 but got {res.status_code}. Response: {res.text}")
                failed = True
            else:
                print(f"  ✅ Passed: got {res.status_code}")
        except Exception as e:
            print(f"  ❌ FAILED: Error making request: {e}")
            failed = True

    if failed:
        print("\nSecurity regression tests FAILED. Some endpoints are accessible without auth.")
        sys.exit(1)
    else:
        print("\nAll security regression tests PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    test_unauthenticated_access()
