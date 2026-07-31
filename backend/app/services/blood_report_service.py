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

        from app.services.pdf_extractor import extract_text_from_pdf_bytes, parse_lab_values_from_text
        
        pdf_text = ""
        local_parsed = {}
        if "pdf" in mime_type.lower():
            pdf_text = extract_text_from_pdf_bytes(file_content)
            local_parsed = parse_lab_values_from_text(pdf_text)

        system_instruction = (
            "You are a clinical AI assistant that extracts lab values from blood reports and medical documents.\n"
            "Extract the following values if present: creatinine, glucose, potassium, sodium, hr (heart rate), sbp (systolic blood pressure), dbp (diastolic blood pressure), rr (respiratory rate), o2 (oxygen saturation), anchor_age (patient age), gender (1 for male, 0 for female).\n"
            "Return the data strictly as a JSON object with these keys. If a value is missing or cannot be found, use null.\n"
            "Do NOT include markdown backticks like ```json in your response, just the raw JSON object."
        )

        user_content = "Please extract the lab values and vitals from this attached medical report."
        if pdf_text:
            user_content += f"\n\nHere is the raw text extracted from the document:\n{pdf_text[:3000]}"

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

            models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-flash-latest", "gemini-1.5-pro"]
            response = None
            last_http_error = None

            for model_name in models_to_try:
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={current_api_key}"
                try:
                    with httpx.Client(timeout=60.0) as client:
                        resp = client.post(
                            api_url,
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        )
                    if resp.status_code == 200:
                        response = resp
                        logger.info(f"Successfully generated blood report extraction using model: {model_name}")
                        break
                    else:
                        logger.warning(f"Model {model_name} returned status {resp.status_code}: {resp.text}")
                        last_http_error = resp
                except Exception as req_err:
                    logger.warning(f"Request failed for model {model_name}: {req_err}")

            if not response:
                if local_parsed and all(k in local_parsed for k in ['creatinine', 'glucose', 'potassium', 'sodium']):
                    logger.info("Using PyMuPDF local text parsing for blood report extraction!")
                    return local_parsed
                if last_http_error is not None:
                    last_http_error.raise_for_status()
                raise HTTPException(status_code=502, detail="Failed to connect to any Gemini AI vision model.")

            response_data = response.json()
            
            try:
                text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                # Parse the JSON
                extracted_data = json.loads(text)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                if local_parsed and all(k in local_parsed for k in ['creatinine', 'glucose', 'potassium', 'sodium']):
                    return local_parsed
                logger.error(f"Failed to parse Gemini response: {e}, Response: {response_data}")
                raise ValueError("Could not parse the report data correctly.")
                
            # Merge local PyMuPDF regex extractions if Gemini missed any field
            if local_parsed:
                for k, v in local_parsed.items():
                    if extracted_data.get(k) is None:
                        extracted_data[k] = v

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
