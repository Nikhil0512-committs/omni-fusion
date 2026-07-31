import logging
import json
import base64
from typing import Dict, Optional, Any
import httpx
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

class BloodReportService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model_name = "gemini-1.5-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

    def parse_blood_report(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Parses a blood report (PDF/Image) using Gemini to extract lab values.
        """
        import os
        current_api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not current_api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable is not configured on the server.")

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={current_api_key}"

        system_instruction = (
            "You are a clinical AI assistant that extracts lab values from blood reports and medical documents.\n"
            "Extract the following values if present: creatinine, glucose, potassium, sodium, hr (heart rate), sbp (systolic blood pressure), dbp (diastolic blood pressure), rr (respiratory rate), o2 (oxygen saturation), anchor_age (patient age), gender (1 for male, 0 for female).\n"
            "Return the data strictly as a JSON object with these keys. If a value is missing or cannot be found, use null.\n"
            "Do NOT include markdown backticks like ```json in your response, just the raw JSON object."
        )

        user_content = "Please extract the lab values and vitals from this attached medical report."

        try:
            b64_data = base64.b64encode(file_content).decode('utf-8')
            
            payload = {
                "system_instruction": {
                    "parts": [{"text": system_instruction}]
                },
                "contents": [{
                    "parts": [
                        {"text": user_content},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_data
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "response_mime_type": "application/json"
                }
            }

            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with httpx.Client(timeout=60.0) as client:
                        response = client.post(
                            api_url,
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        )
                        
                    response.raise_for_status()
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in [429, 503] and attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise e
            response_data = response.json()
            
            try:
                text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                # Parse the JSON
                extracted_data = json.loads(text)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                logger.error(f"Failed to parse Gemini response: {e}, Response: {response_data}")
                raise ValueError("Could not parse the report data correctly.")
                
            # Validate required fields
            required_fields = ['creatinine', 'glucose', 'potassium', 'sodium']
            missing_fields = []
            
            for field in required_fields:
                val = extracted_data.get(field)
                if val is None:
                    missing_fields.append(field)
                    
            if missing_fields:
                missing_str = ", ".join(missing_fields)
                raise ValueError(f"The following required parameters are missing from this blood report: {missing_str}. Please try uploading a different report.")
                
            return extracted_data

        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            logger.error(f"Gemini API HTTP Error ({e.response.status_code}): {error_text}")
            detail_msg = f"Gemini AI Error ({e.response.status_code})"
            try:
                err_json = e.response.json()
                if "error" in err_json and "message" in err_json["error"]:
                    detail_msg = f"AI Engine: {err_json['error']['message']}"
            except Exception:
                pass
            raise HTTPException(status_code=502, detail=detail_msg)
        except ValueError as e:
            logger.error(f"Validation error in extracted data: {e}")
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error analyzing report: {str(e)}")

blood_report_service = BloodReportService()
