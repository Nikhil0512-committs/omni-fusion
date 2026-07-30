import os
import tempfile
import base64
from fpdf import FPDF
from app.models.schemas import PredictResponse

class PDFService:
    """Render immutable prediction data into a temporary clinical PDF."""
    
    def __init__(self):
        self.fonts_dir = os.path.join(os.path.dirname(__file__), "../assets/fonts")
        
    def _add_fonts(self, pdf: FPDF):
        # We assume fonts are downloaded and exist
        devanagari_path = os.path.join(self.fonts_dir, "NotoSansDevanagari-Regular.ttf")
        bengali_path = os.path.join(self.fonts_dir, "NotoSansBengali-Regular.ttf")
        
        if os.path.exists(devanagari_path):
            pdf.add_font("NotoSansDevanagari", style="", fname=devanagari_path)
        if os.path.exists(bengali_path):
            pdf.add_font("NotoSansBengali", style="", fname=bengali_path)

    def generate_report(self, predict_res: dict, lang: str = "en") -> str:
        """Generate a premium, patient-friendly clinical PDF report."""
        pdf = FPDF()
        self._add_fonts(pdf)
        pdf.add_page()
        
        # Select font based on language
        font_family = "helvetica"
        if lang == "hi":
            font_family = "NotoSansDevanagari"
        elif lang == "bn":
            font_family = "NotoSansBengali"
            
        # COLORS
        BRAND_COLOR = (30, 58, 138) # slate-900 / deep blue
        ACCENT_COLOR = (59, 130, 246) # blue-500
        TEXT_MAIN = (30, 41, 59) # slate-800
        TEXT_MUTED = (100, 116, 139) # slate-500
        DANGER_COLOR = (220, 38, 38) # red-600
        SUCCESS_COLOR = (22, 163, 74) # green-600

        # --- HEADER ---
        pdf.set_fill_color(*BRAND_COLOR)
        pdf.rect(0, 0, 210, 30, 'F')
        
        pdf.set_y(10)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 20)
        pdf.cell(0, 10, "Omni-Fusion Health", align="C", new_x="LMARGIN", new_y="NEXT")
        
        # --- TITLE & RISK SCORE ---
        pdf.ln(15)
        pdf.set_text_color(*TEXT_MAIN)
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 10, "Personalized Health Assessment", align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(5)
        risk = predict_res.get('risk_score')
        
        if risk is not None:
            risk_pct = risk * 100
            if risk_pct < 5:
                risk_level = "Low Risk (Healthy)"
                r_color = SUCCESS_COLOR
            elif risk_pct < 15:
                risk_level = "Moderate Risk (Monitor)"
                r_color = (202, 138, 4) # yellow-600
            else:
                risk_level = "High Risk (Action Required)"
                r_color = DANGER_COLOR
                
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 10, "Overall Assessment:", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*r_color)
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, f"{risk_level}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*TEXT_MAIN)
        else:
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 10, "Assessment Type: Diagnostic (ECG Only)", align="C", new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(10)
        
        # --- ECG ABNORMALITY ---
        ecg_abnormality = predict_res.get('ecg_abnormality')
        if ecg_abnormality:
            pdf.set_fill_color(254, 242, 242) # red-50
            pdf.set_text_color(*DANGER_COLOR)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(190, 10, "  ECG Abnormality Detected", new_x="LMARGIN", new_y="NEXT", fill=True)
            
            pdf.set_font("helvetica", "", 11)
            pdf.set_text_color(*TEXT_MAIN)
            # Add some padding using spaces for visual margin inside multi_cell
            padded_text = "  " + ecg_abnormality + "\n"
            pdf.multi_cell(190, 6, padded_text, fill=True)
            pdf.ln(10)

        # --- EXPLAINABLE AI (XAI) SECTION ---
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(*BRAND_COLOR)
        pdf.cell(0, 10, "What contributed to your assessment?", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(0, 6, "Our AI analyzes multiple factors. Here is how they impacted your result in layman terms:", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        
        def format_label(key: str) -> str:
            formatted = key.lower().replace('vital_', '').replace('hist_', '')
            formatted = formatted.replace('_', ' ')
            acronyms = ['hr', 'sbp', 'dbp', 'rr', 'o2', 'bmi']
            words = []
            for word in formatted.split():
                if word in acronyms:
                    words.append(word.upper())
                else:
                    words.append(word.capitalize())
            return " ".join(words)
            
        shap_data = predict_res.get('shap_data', {})
        if shap_data:
            sorted_shap = sorted(shap_data.items(), key=lambda x: abs(x[1]), reverse=True)
            pdf.set_text_color(*TEXT_MAIN)
            for feature, val in sorted_shap[:5]:
                clean_feature = format_label(feature)
                
                if val > 0.1:
                    impact = "Significantly increased your risk."
                    bullet_color = DANGER_COLOR
                elif val > 0:
                    impact = "Slightly increased your risk."
                    bullet_color = (202, 138, 4)
                elif val < -0.1:
                    impact = "Strongly lowered your risk (Protective)."
                    bullet_color = SUCCESS_COLOR
                else:
                    impact = "Slightly lowered your risk."
                    bullet_color = SUCCESS_COLOR
                    
                # Draw a colored bullet point
                pdf.set_fill_color(*bullet_color)
                pdf.ellipse(12, pdf.get_y() + 2, 3, 3, 'F')
                
                pdf.set_x(18)
                pdf.set_font("helvetica", "B", 11)
                pdf.cell(35, 7, f"{clean_feature}:", new_x="RIGHT")
                pdf.set_font("helvetica", "", 11)
                pdf.cell(0, 7, impact, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("helvetica", "I", 11)
            pdf.cell(0, 6, "No specific feature data available.", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(8)

        # --- AI REASONING / CLINICAL INSIGHTS ---
        if predict_res.get('failure_analysis_summary'):
            pdf.set_font("helvetica", "B", 14)
            pdf.set_text_color(*BRAND_COLOR)
            pdf.cell(0, 10, "AI Clinical Insights", new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_font(font_family, "", 11)
            pdf.set_text_color(*TEXT_MAIN)
            summary = predict_res['failure_analysis_summary']
            if font_family == "helvetica":
                summary = summary.replace("•", "-").replace("—", "-").replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'").replace("…", "...")
            
            pdf.set_fill_color(241, 245, 249) # slate-100
            pdf.cell(190, 4, "", new_x="LMARGIN", new_y="NEXT", fill=True) # padding top
            pdf.multi_cell(190, 6, "  " + summary, fill=True)
            pdf.cell(190, 4, "", new_x="LMARGIN", new_y="NEXT", fill=True) # padding bottom
            pdf.ln(10)

        # --- CALL TO ACTION (CONSULT DOCTOR) ---
        pdf.set_fill_color(*ACCENT_COLOR)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(190, 10, "  Need Expert Advice?", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_font("helvetica", "", 11)
        pdf.cell(190, 10, "  Consult a doctor directly through the Omni-Fusion platform to discuss these results.", new_x="LMARGIN", new_y="NEXT", fill=True)

        # --- FOOTER (Technical IDs) ---
        pdf.set_y(-20)
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(0, 5, f"Patient ID: {predict_res.get('patient_id', 'N/A')} | Prediction ID: {predict_res.get('prediction_id', 'N/A')}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, "Generated automatically by Omni-Fusion Health AI", align="C", new_x="LMARGIN", new_y="NEXT")
        

                
        blood_image_path = predict_res.get('blood_image_path')
        if blood_image_path and os.path.exists(blood_image_path):
            pdf.add_page()
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Uploaded Blood Report Document", new_x="LMARGIN", new_y="NEXT")
            try:
                pdf.image(blood_image_path, w=180)
            except Exception as e:
                pdf.set_font("helvetica", "", 12)
                pdf.cell(0, 10, f"Failed to attach blood report document: {str(e)}", new_x="LMARGIN", new_y="NEXT")
                
        ecg_image_path = predict_res.get('ecg_image_path')
        if ecg_image_path and os.path.exists(ecg_image_path):
            pdf.add_page()
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Uploaded ECG Document", new_x="LMARGIN", new_y="NEXT")
            try:
                pdf.image(ecg_image_path, w=180)
            except Exception as e:
                pdf.set_font("helvetica", "", 12)
                pdf.cell(0, 10, f"Failed to attach ECG document: {str(e)}", new_x="LMARGIN", new_y="NEXT")
                
        fd_pdf, pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd_pdf)
        pdf.output(pdf_path)
        return pdf_path

pdf_service = PDFService()
