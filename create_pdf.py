from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Omni-Fusion Hackathon Video Script', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_script():
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Target Duration: 1.3 Minutes (~80 seconds)', 0, 1)
    pdf.ln(5)

    sections = [
        {
            "time": "[0:00 - 0:15] The Hook & Problem",
            "visual": "High-energy montage. Fast cuts of doctors looking stressed in a busy ER. Text on screen: 'Fragmented Data.' 'Algorithmic Bias.' 'Missing Records.'",
            "audio": "In high-volume emergency rooms, doctors are forced to make life-or-death cardiovascular decisions using fragmented data. Worse, existing AI models often suffer from bias and fail completely when patient records are missing."
        },
        {
            "time": "[0:15 - 0:35] The Multimodal Solution",
            "visual": "Omni-Fusion logo animated. 3D glowing streams of data (ECG waves, Vitals, Text) merging into one glowing core. Text on screen: '12-Lead ECG + Vitals + History'",
            "audio": "Meet Omni-Fusion - a multimodal AI platform that fuses real-time ECGs, clinical vitals, and longitudinal history to predict cardiovascular risk with unprecedented accuracy."
        },
        {
            "time": "[0:35 - 0:50] Resilience (Key Innovation 1)",
            "visual": "Screen recording of the Omni-Fusion UI. A user uploads data but skips the 'historical data' section. The AI still successfully processes it. Text on screen: '100% Uptime via Dynamic Routing.'",
            "audio": "What if data is missing? Our first breakthrough is Resilience. Using dynamic routing, if a patient lacks historical records, Omni-Fusion seamlessly falls back to available streams, ensuring 100% uptime in low-resource settings."
        },
        {
            "time": "[0:50 - 1:10] Algorithmic Equity (Key Innovation 2)",
            "visual": "Split screen showing two diverse patients. A graph shows the 'Error Divergence' shrinking from 12.5% to <1.5%.",
            "audio": "Our second breakthrough is Equity. We engineered a custom Equity-Aware Loss Function that actively penalizes the network for bias during training. We reduced the demographic error gap from 12.5% to under 1.5%."
        },
        {
            "time": "[1:10 - 1:30] Trust & Impact (Key Innovation 3)",
            "visual": "Close-up of the UI showing the 1D Grad-CAM heatmap highlighting a specific T-wave on the ECG, and a SHAP waterfall chart. Doctor smiling, looking at the tablet.",
            "audio": "And finally, Trust. Doctors need to understand the AI. Omni-Fusion provides full explainability - using Grad-CAM to highlight exact anomalies on the ECG, and SHAP charts to explain which vitals drove the risk score. Omni-Fusion: Equitable, explainable, and resilient cardiovascular AI."
        }
    ]

    for sec in sections:
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 8, sec["time"], 0, 1)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(20, 6, "Visual: ", 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, sec["visual"])
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(20, 6, "Audio: ", 0, 0)
        pdf.set_font('Arial', 'I', 10)
        pdf.multi_cell(0, 6, f'"{sec["audio"]}"')
        
        pdf.ln(6)

    pdf.output('OmniFusion_Hackathon_Video_Script.pdf')
    print("PDF created successfully!")

if __name__ == '__main__':
    create_script()
