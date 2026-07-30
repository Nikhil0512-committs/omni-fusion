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
        """Generate a report and return its temporary filesystem path.

        Args:
            predict_res: Prediction fields and optional explanation artifacts.
            lang: Language code (en, hi, bn)

        Returns:
            Path to a temporary PDF owned by the caller.
        """
        pdf = FPDF()
        self._add_fonts(pdf)
        pdf.add_page()
        
        # Select font based on language
        font_family = "helvetica"
        if lang == "hi":
            font_family = "NotoSansDevanagari"
        elif lang == "bn":
            font_family = "NotoSansBengali"
            
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Omni-Fusion Risk Prediction Report", align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 10, f"Patient ID: {predict_res['patient_id']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"Prediction ID: {predict_res['prediction_id']}", new_x="LMARGIN", new_y="NEXT")
        
        risk = predict_res.get('risk_score')
        if risk is not None:
            pdf.cell(0, 10, f"Risk Score: {risk:.4f}", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 10, f"Risk Score: N/A (ECG Only)", new_x="LMARGIN", new_y="NEXT")
        
        ecg_abnormality = predict_res.get('ecg_abnormality')
        if ecg_abnormality:
            pdf.set_font("helvetica", "I", 12)
            pdf.set_text_color(220, 53, 69)  # Red color for abnormality
            pdf.cell(0, 10, "ECG Abnormality Detected!", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", "", 12)
            
            pdf.multi_cell(0, 8, ecg_abnormality)
            pdf.cell(0, 10, "Please consult a doctor for further evaluation.", new_x="LMARGIN", new_y="NEXT")

        
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Key Risk Factors", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 12)
        
        def format_label(key: str) -> str:
            # Remove prefix
            formatted = key.lower().replace('vital_', '').replace('hist_', '')
            # Replace underscores with spaces
            formatted = formatted.replace('_', ' ')
            # Capitalize acronyms
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
            for feature, val in sorted_shap[:5]:
                clean_feature = format_label(feature)
                impact = "Increases Risk" if val > 0 else "Decreases Risk"
                pdf.cell(0, 8, f"- {clean_feature}: {impact} (Magnitude: {abs(val):.4f})", new_x="LMARGIN", new_y="NEXT")

        if predict_res.get('failure_analysis_summary'):
            pdf.ln(5)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Failure Analysis / Borderline Summary", new_x="LMARGIN", new_y="NEXT")
            
            # Use localized font for the summary text
            pdf.set_font(font_family, "", 12)
            summary = predict_res['failure_analysis_summary']
            if font_family == "helvetica":
                summary = summary.replace("•", "-").replace("—", "-").replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'").replace("…", "...")
            pdf.multi_cell(0, 8, summary)
        

                
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
