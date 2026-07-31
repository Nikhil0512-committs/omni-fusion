import fitz  # PyMuPDF
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract raw text from a PDF document using PyMuPDF."""
    text_content = ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text_content += page.get_text("text") + "\n"
    except Exception as e:
        logger.warning(f"PyMuPDF text extraction failed: {e}")
    return text_content.strip()

def parse_lab_values_from_text(raw_text: str) -> Dict[str, Any]:
    """Parse common blood lab parameters directly from document text using regex."""
    extracted = {}
    if not raw_text:
        return extracted

    patterns = {
        "creatinine": r"(?:serum\s*)?creatinine[\s\:\=]*([\d\.]+)",
        "glucose": r"(?:blood\s*|fasting\s*|random\s*)?glucose[\s\:\=]*([\d\.]+)",
        "potassium": r"(?:serum\s*)?potassium[\s\:\=]*([\d\.]+)",
        "sodium": r"(?:serum\s*)?sodium[\s\:\=]*([\d\.]+)",
        "hr": r"(?:heart\s*rate|hr)[\s\:\=]*([\d\.]+)",
        "sbp": r"(?:systolic\s*bp|sbp)[\s\:\=]*([\d\.]+)",
        "dbp": r"(?:diastolic\s*bp|dbp)[\s\:\=]*([\d\.]+)",
        "rr": r"(?:respiratory\s*rate|rr)[\s\:\=]*([\d\.]+)",
        "o2": r"(?:oxygen\s*saturation|o2|spo2)[\s\:\=]*([\d\.]+)",
        "anchor_age": r"(?:age|patient\s*age)[\s\:\=]*([\d]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            try:
                extracted[key] = float(match.group(1))
            except ValueError:
                pass

    raw_lower = raw_text.lower()
    if "female" in raw_lower:
        extracted["gender"] = 0
    elif "male" in raw_lower:
        extracted["gender"] = 1

    return extracted
