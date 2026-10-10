from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.blood_report_service import blood_report_service
from app.services.ecg_report_service import ecg_report_service
from app.services.gemini_service import GeminiService, GeminiServiceError


def _candidate_response(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_blood_report_uses_structured_vision_response(monkeypatch):
    generate = MagicMock(return_value=_candidate_response(
        '{"creatinine": 1.2, "glucose": 98, "potassium": 4.1, "sodium": 140}'
    ))
    monkeypatch.setattr("app.services.blood_report_service.gemini_service.generate_content", generate)

    result = blood_report_service.parse_blood_report(b"image-bytes", "image/jpeg")

    assert result["creatinine"] == 1.2
    assert result["sodium"] == 140
    assert generate.call_args.args[0]["generationConfig"]["response_mime_type"] == "application/json"


def test_ecg_upload_returns_retryable_upstream_error_not_500(monkeypatch):
    monkeypatch.setattr(
        "app.services.ecg_report_service.gemini_service.generate_content",
        MagicMock(side_effect=GeminiServiceError(502, "No compatible model is enabled.")),
    )

    with pytest.raises(HTTPException) as error:
        ecg_report_service.parse_ecg_report(b"image-bytes", "image/jpeg")

    assert error.value.status_code == 502
    assert error.value.detail == "No compatible model is enabled."


def test_model_discovery_uses_only_generate_content_models():
    service = GeminiService()
    client = MagicMock()
    response = MagicMock(status_code=200)
    response.json.return_value = {
        "models": [
            {"name": "models/gemini-3.5-flash", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]},
            {"name": "models/gemini-3.1-pro", "supportedActions": ["generateContent"]},
        ]
    }
    client.get.return_value = response

    models = service._discover_models(client, "test-key")

    assert models == ["models/gemini-3.5-flash", "models/gemini-3.1-pro"]
