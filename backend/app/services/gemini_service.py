"""Small, dependency-free Gemini REST client for the document AI features.

The Gemini model catalogue is account and region dependent and model aliases are
retired periodically.  Discovering the models enabled for the configured API key
avoids pinning uploads to an alias that no longer supports ``generateContent``.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiServiceError(Exception):
    """A safe, user-facing failure from the upstream Gemini API."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class GeminiService:
    """Generate structured multimodal content with an available Gemini model."""

    # Used only if model discovery is temporarily unavailable.  Normal requests
    # use the per-key list returned by ``models.list`` instead.
    FALLBACK_MODELS = (
        "gemini-3.5-flash",
        "gemini-3-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    )

    def __init__(self, timeout_seconds: float = 60.0):
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _normalise_model_name(model_name: str) -> str:
        return model_name if model_name.startswith("models/") else f"models/{model_name}"

    @staticmethod
    def _supports_generate_content(model: dict[str, Any]) -> bool:
        methods = model.get("supportedGenerationMethods") or model.get("supportedActions") or []
        return "generateContent" in methods

    @staticmethod
    def _model_sort_key(model_name: str) -> tuple[int, str]:
        """Prefer current Flash models: they are fast and support document vision."""
        short_name = model_name.removeprefix("models/").lower()
        if "flash" in short_name and "image" not in short_name and "tts" not in short_name:
            return (0, short_name)
        if "pro" in short_name and "image" not in short_name and "tts" not in short_name:
            return (1, short_name)
        return (2, short_name)

    def _discover_models(self, client: httpx.Client, api_key: str) -> list[str]:
        """Return models this key explicitly permits for generateContent."""
        try:
            response = client.get(
                f"{GEMINI_API_BASE}/models",
                headers={"x-goog-api-key": api_key},
            )
        except httpx.RequestError as exc:
            logger.warning("Gemini model discovery failed: %s", exc)
            return []

        if response.status_code in (401, 403):
            raise GeminiServiceError(502, "The server's Gemini API key was rejected. Please update GEMINI_API_KEY.")
        if response.status_code != 200:
            logger.warning("Gemini model discovery returned %s: %s", response.status_code, response.text[:500])
            return []

        try:
            models = response.json().get("models", [])
        except ValueError:
            logger.warning("Gemini model discovery returned invalid JSON")
            return []

        names = [
            self._normalise_model_name(model["name"])
            for model in models
            if isinstance(model, dict) and model.get("name") and self._supports_generate_content(model)
        ]
        return sorted(dict.fromkeys(names), key=self._model_sort_key)

    def _candidate_models(self, client: httpx.Client, api_key: str) -> Iterable[str]:
        discovered = self._discover_models(client, api_key)
        configured = (settings.gemini_model or "").strip()
        if configured:
            configured = self._normalise_model_name(configured)
            # An explicit configured model is allowed first, but discovery still
            # provides a safe fallback if it has been retired.
            yield configured

        for model_name in discovered:
            if model_name != configured:
                yield model_name

        if not discovered:
            for model_name in self.FALLBACK_MODELS:
                normalised = self._normalise_model_name(model_name)
                if normalised != configured:
                    yield normalised

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            message = response.json().get("error", {}).get("message")
            if message:
                return str(message)
        except ValueError:
            pass
        return response.text[:500] or response.reason_phrase

    def generate_content(self, payload: dict[str, Any], api_key: str | None = None) -> dict[str, Any]:
        """Return a Gemini response using a model available to this API key."""
        active_key = api_key or settings.gemini_api_key
        if not active_key:
            raise GeminiServiceError(503, "GEMINI_API_KEY is not configured on the server.")

        last_error: tuple[int, str] | None = None
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                for model_name in self._candidate_models(client, active_key):
                    try:
                        response = client.post(
                            f"{GEMINI_API_BASE}/{model_name}:generateContent",
                            json=payload,
                            headers={"Content-Type": "application/json", "x-goog-api-key": active_key},
                        )
                    except httpx.RequestError as exc:
                        logger.warning("Gemini request for %s failed: %s", model_name, exc)
                        last_error = (502, "The Gemini service could not be reached.")
                        continue

                    if response.status_code == 200:
                        logger.info("Gemini generated content with %s", model_name)
                        return response.json()

                    detail = self._error_detail(response)
                    logger.warning("Gemini model %s returned %s: %s", model_name, response.status_code, detail)
                    if response.status_code in (401, 403):
                        raise GeminiServiceError(502, "The server's Gemini API key was rejected. Please update GEMINI_API_KEY.")
                    if response.status_code == 429:
                        raise GeminiServiceError(503, "Gemini is temporarily rate limited. Please try again shortly.")
                    last_error = (502, f"Gemini could not analyze this report: {detail}")
        except GeminiServiceError:
            raise

        if last_error:
            raise GeminiServiceError(*last_error)
        raise GeminiServiceError(502, "No Gemini model is available for document analysis with this API key.")


gemini_service = GeminiService()
