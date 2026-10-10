import base64
import json
import logging
from typing import Any, Dict

from fastapi import HTTPException

from app.services.gemini_service import GeminiServiceError, gemini_service
from app.services.pdf_extractor import extract_text_from_pdf_bytes, parse_lab_values_from_text

logger = logging.getLogger(__name__)


class BloodReportService:
    REQUIRED_FIELDS = ("creatinine", "glucose", "potassium", "sodium")

    @staticmethod
    def _parse_response(response_data: dict[str, Any]) -> dict[str, Any]:
        try:
            raw_text = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("The AI service returned no readable report data.") from exc

        cleaned_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            raise ValueError("The AI service returned report data in an invalid format.") from exc
        if not isinstance(parsed, dict):
            raise ValueError("The AI service returned report data in an invalid format.")
        return parsed

    def parse_blood_report(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """Extract required lab values from a PDF or report image.

        Text-based PDFs are parsed locally first. This makes common lab-report
        uploads work even while the optional vision service is unavailable.
        """
        if not file_content:
            raise HTTPException(status_code=400, detail="The uploaded blood report is empty.")

        pdf_text = ""
        local_parsed: dict[str, Any] = {}
        if "pdf" in mime_type.lower():
            pdf_text = extract_text_from_pdf_bytes(file_content)
            local_parsed = parse_lab_values_from_text(pdf_text)

        if all(local_parsed.get(field) is not None for field in self.REQUIRED_FIELDS):
            logger.info("Extracted all required blood values locally from PDF text.")
            return local_parsed

        system_instruction = (
            "You are a clinical AI assistant that extracts lab values from blood reports and medical documents.\n"
            "Extract the following values if present: creatinine, glucose, potassium, sodium, hr (heart rate), "
            "sbp (systolic blood pressure), dbp (diastolic blood pressure), rr (respiratory rate), o2 (oxygen "
            "saturation), anchor_age (patient age), gender (1 for male, 0 for female).\n"
            "Return a JSON object with exactly these keys. Use null for missing values."
        )
        user_content = "Extract the laboratory values and vitals from this medical report."
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
            extracted_data = self._parse_response(gemini_service.generate_content(payload))
        except GeminiServiceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

        for key, value in local_parsed.items():
            if extracted_data.get(key) is None:
                extracted_data[key] = value

        missing_fields = [field for field in self.REQUIRED_FIELDS if extracted_data.get(field) is None]
        if missing_fields:
            raise HTTPException(
                status_code=422,
                detail="The report is missing required values: " + ", ".join(missing_fields) + ".",
            )
        return extracted_data


blood_report_service = BloodReportService()
