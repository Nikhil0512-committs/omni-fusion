import logging
from typing import Dict, Optional
import httpx

from app.core.config import settings, HIGH_RISK_THRESHOLD_PCT

logger = logging.getLogger(__name__)

class CopilotService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model_name = "gemini-flash-latest"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

    def generate_soap_note(
        self,
        risk_score: float,
        shap_data: Dict[str, float],
        gradcam_b64: str,
        lang: str = "en"
    ) -> str:
        """
        Generates a clinical SOAP note based on the model's prediction artifacts.
        
        Args:
            risk_score (float): The predicted mortality risk score (0-1).
            shap_data (Dict[str, float]): Feature importance scores.
            gradcam_b64 (str): Base64 encoded string of the Grad-CAM heatmap.
            lang (str): Language code (en, hi, bn).
            
        Returns:
            str: Markdown formatted SOAP note.
        """
        # Determine top pushing and pulling features based on SHAP values
        sorted_features = sorted(shap_data.items(), key=lambda x: x[1])
        top_risk_drivers = sorted_features[-3:] if len(sorted_features) >= 3 else sorted_features
        top_protective_factors = sorted_features[:3] if len(sorted_features) >= 3 else sorted_features

        risk_str = "High Risk (Mortality)" if risk_score > (HIGH_RISK_THRESHOLD_PCT / 100.0) else "Low Risk (Survival)"

        language_map = {
            "en": "English",
            "hi": "Hindi (Devanagari script)",
            "bn": "Bengali"
        }
        target_language = language_map.get(lang, "English")

        system_instruction = (
            "You are an expert AI clinical assistant supporting a cardiologist.\n"
            "Your task is to write a CONCISE, HIGH-YIELD SOAP note based strictly on the provided AI risk prediction artifacts.\n"
            f"You MUST write the note in {target_language}.\n"
            "CRITICAL CONCISENESS RULE: Keep the ENTIRE SOAP note under 120 words total. Maximum 2 short bullet points per section.\n"
            "Do NOT include filler text, generic intros, or repetitive disclaimers.\n"
            "Do NOT make absolute diagnostic claims, but reference relevant ACC/AHA or ESC clinical guidelines.\n\n"
            "Structure strictly as:\n"
            "## Subjective\n- Key intake context\n\n"
            "## Objective\n- Mortality Risk Score & Key SHAP Biomarkers\n\n"
            "## Assessment\n- Concise clinical risk synthesis\n\n"
            "## Plan\n- Actionable recommendation"
        )

        user_content = (
            f"### AI Prediction Data\n"
            f"- **Mortality Risk Score:** {risk_score:.2f} ({risk_str})\n"
            f"- **Top Risk Drivers (SHAP > 0):** {', '.join([f'{k} ({v:.2f})' for k, v in top_risk_drivers])}\n"
            f"- **Top Protective Factors (SHAP < 0):** {', '.join([f'{k} ({v:.2f})' for k, v in top_protective_factors])}\n"
            "- **ECG Grad-CAM Heatmap:** Provided as an image. Look at the highlighted regions on the ECG to note structural/electrical anomalies localized by the model."
        )

        try:
            # Construct the parts for the Gemini REST API
            parts = [{"text": user_content}]
            
            if gradcam_b64:
                # Check if it has a data URI scheme, remove it if it does
                if "," in gradcam_b64:
                    gradcam_b64 = gradcam_b64.split(",")[1]
                    
                parts.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": gradcam_b64
                    }
                })

            payload = {
                "system_instruction": {
                    "parts": [{"text": system_instruction}]
                },
                "contents": [{
                    "parts": parts
                }]
            }

            import os
            current_api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
            if not current_api_key:
                raise Exception("GEMINI_API_KEY environment variable is not configured on the server.")

            models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-flash-latest", "gemini-1.5-pro"]
            response = None
            last_err = None

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
                        break
                    else:
                        last_err = resp
                except Exception as req_err:
                    logger.warning(f"Copilot model {model_name} failed: {req_err}")

            if not response:
                if last_err is not None:
                    last_err.raise_for_status()
                raise Exception("Failed to query Gemini API models for clinical summary.")

            response_data = response.json()
            
            try:
                text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            except (KeyError, IndexError):
                raise ValueError("Unexpected response structure from Gemini API")
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise Exception("Failed to generate clinical summary. The AI service may be temporarily unavailable or timed out.")

copilot_service = CopilotService()
