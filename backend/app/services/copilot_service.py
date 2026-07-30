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
            "Your task is to write a highly structured SOAP note based strictly on the provided AI risk prediction artifacts.\n"
            f"You MUST write the entire SOAP note and any analysis in {target_language}. Do not use English unless it is for standard medical acronyms.\n"
            "Do NOT fabricate any vitals, history, or patient data that is not explicitly provided in this prompt.\n"
            "Do NOT make diagnostic claims, but DO reference relevant clinical guideline families (e.g., ACC/AHA, KDIGO, ESC) as general context where applicable.\n\n"
            "Write the note in Markdown using the standard SOAP (Subjective, Objective, Assessment, Plan) format. "
            "Under 'Objective', list the SHAP drivers and state that an ECG Grad-CAM indicates regions of interest. "
            "Under 'Assessment', synthesize the risk score and features. "
            "Under 'Plan', recommend general clinical follow-up steps referencing standard guidelines."
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

            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
            response.raise_for_status()
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
