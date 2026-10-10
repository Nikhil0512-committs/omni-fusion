import base64
import json
import logging
from typing import Any, Dict

from fastapi import HTTPException

from app.services.gemini_service import GeminiServiceError, gemini_service
from app.services.pdf_extractor import extract_text_from_pdf_bytes

logger = logging.getLogger(__name__)


class EcgReportService:
    @staticmethod
    def _findings_from_response(response_data: dict[str, Any]) -> str:
        try:
            raw_text = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPException(status_code=422, detail="The AI service found no readable ECG findings.") from exc

        cleaned_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned_text)
            if isinstance(parsed, dict) and parsed.get("ecg_abnormality"):
                return str(parsed["ecg_abnormality"])
            if isinstance(parsed, dict):
                findings = [f"{key}: {value}" for key, value in parsed.items() if value]
                if findings:
                    return " | ".join(findings)
        except json.JSONDecodeError:
            pass

        if raw_text:
            return raw_text
        raise HTTPException(status_code=422, detail="The AI service found no readable ECG findings.")

    def parse_ecg_report(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """Analyze a 12-lead ECG PDF/image and return its clinical findings."""
        if not file_content:
            raise HTTPException(status_code=400, detail="The uploaded ECG report is empty.")

        pdf_text = extract_text_from_pdf_bytes(file_content) if "pdf" in mime_type.lower() else ""
        system_instruction = (
            "You are an expert cardiologist analyzing a 12-lead ECG report image or document.\n"
            "Extract written measurements including heart rate, PR, QRS, QT/QTc, axes, rhythm, and diagnosis.\n"
            "Return a valid JSON object with one key, ecg_abnormality, containing a concise clinical findings summary.\n"
            "If normal, use: Normal Sinus Rhythm - No acute ECG abnormality detected."
        )
        user_content = "Analyze this ECG report and provide the clinical measurements and diagnosis summary."
        if pdf_text:
            user_content += f"\n\nExtracted document text:\n{pdf_text[:3000]}"

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{
                "parts": [
                    {"text": user_content},
                    {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(file_content).decode("utf-8")}},
                ]
            }],
            "generationConfig": {"response_mime_type": "application/json"},
        }

        try:
            findings = self._findings_from_response(gemini_service.generate_content(payload))
        except GeminiServiceError as exc:
            # A text-based ECG can still be displayed to the clinician when the
            # vision provider is unavailable. Images need an explicit retryable
            # upstream error rather than an opaque 500.
            if pdf_text:
                logger.warning("Using locally extracted ECG text after Gemini failure: %s", exc.detail)
                return {"ecg_abnormality": pdf_text[:1000]}
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

        return {"ecg_abnormality": findings}


ecg_report_service = EcgReportService()
