import logging
import json
import base64
from typing import Dict, Any
import httpx
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

class EcgReportService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model_name = "gemini-1.5-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

    def parse_ecg_report(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Parses an ECG report (PDF/Image) using Gemini to extract clinical parameters and interpretations.
        """
        import os
        current_api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not current_api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable is not configured on the server.")

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={current_api_key}"

        system_instruction = (
            "You are an expert cardiologist and clinical AI assistant analyzing a 12-lead ECG report image or document.\n"
            "Carefully examine the image and extract all written clinical parameters, measurements, and text interpretations.\n"
            "Include:\n"
            "- Heart Rate, PR interval, QRS duration, QT/QTc, P-R-T Axes\n"
            "- Rhythm & Diagnosis (e.g. Sinus Rhythm, Atrial Fibrillation, ST Elevation, T-Wave Inversion, Normal ECG)\n"
            "Summarize all extracted parameters and findings into a concise, accurate clinical finding string for 'ecg_abnormality'.\n"
            "If the ECG is normal, state 'Normal Sinus Rhythm - No acute ECG abnormality detected'.\n"
            "Return strictly a valid JSON object with the single key 'ecg_abnormality'."
        )

        user_content = "Please analyze this attached ECG report/image and provide the exact clinical parameters and diagnosis summary."

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
            response_data = None
            for attempt in range(max_retries):
                try:
                    with httpx.Client(timeout=60.0) as client:
                        response = client.post(
                            api_url,
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        )
                    response.raise_for_status()
                    response_data = response.json()
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in [429, 503] and attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    error_text = e.response.text
                    logger.error(f"Gemini API HTTP status error ({e.response.status_code}): {error_text}")
                    detail_msg = f"Gemini AI Error ({e.response.status_code})"
                    try:
                        err_json = e.response.json()
                        if "error" in err_json and "message" in err_json["error"]:
                            detail_msg = f"AI Engine: {err_json['error']['message']}"
                    except Exception:
                        pass
                    raise HTTPException(status_code=502, detail=detail_msg)
                except Exception as req_err:
                    logger.error(f"Gemini API request failed: {req_err}")
                    raise HTTPException(status_code=500, detail=f"Gemini API request failed: {str(req_err)}")

            if response_data:
                try:
                    raw_text = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    cleaned_text = raw_text
                    if "```" in cleaned_text:
                        cleaned_text = cleaned_text.replace("```json", "").replace("```", "").strip()
                    
                    try:
                        parsed = json.loads(cleaned_text)
                        if isinstance(parsed, dict) and "ecg_abnormality" in parsed:
                            return {"ecg_abnormality": str(parsed["ecg_abnormality"])}
                        elif isinstance(parsed, dict):
                            vals = [f"{k}: {v}" for k, v in parsed.items() if v]
                            return {"ecg_abnormality": " | ".join(vals)}
                    except Exception:
                        pass
                    
                    if raw_text:
                        return {"ecg_abnormality": raw_text}
                except (KeyError, IndexError) as parse_err:
                    logger.error(f"Could not extract text from Gemini response: {parse_err}")
                    raise HTTPException(status_code=502, detail="Failed to extract ECG findings from AI response.")

            raise HTTPException(status_code=422, detail="Could not read a valid ECG report from the provided file.")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error parsing ECG report: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while parsing the ECG report.")

ecg_report_service = EcgReportService()
