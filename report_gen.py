import os
from datetime import datetime
from typing import List, Dict, Any
from fpdf import FPDF

class SurveillancePDF(FPDF):
    """Custom PDF generator with standardized security header and footer pagination."""
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Secure-Vision: YOLOv8 Surveillance Report", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Secure-Vision Automated Surveillance Audit", align="C")

def generate_pdf_report(events: List[Dict[str, Any]], filename: str = "report.pdf") -> str:
    """Compiles detected surveillance events into a visual PDF audit report.
    
    Args:
        events: List of detection event dictionaries.
        filename: Destination path for the generated PDF.
        
    Returns:
        The written filename path.
    """
    pdf = SurveillancePDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    if not events:
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, "No detection events recorded for this session.", new_x="LMARGIN", new_y="NEXT")
        pdf.output(filename)
        return filename

    # Summary section
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Total Detections Logged: {len(events)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Group events by frame if applicable
    frames_processed = set()
    for i, event in enumerate(events, 1):
        label = event.get("label", "Unknown")
        conf = event.get("confidence", 0.0)
        timestamp = event.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        img_path = event.get("filepath")
        if not img_path and "frame" in event:
            img_path = os.path.join("static", event["frame"])

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, f"Event #{i}: {label.upper()} (Confidence: {int(conf * 100)}%) - {timestamp}", new_x="LMARGIN", new_y="NEXT")

        # Embed annotated snapshot if available and not already embedded
        if img_path and os.path.exists(img_path) and img_path not in frames_processed:
            try:
                # Add page break if vertical space is insufficient
                if pdf.get_y() > 200:
                    pdf.add_page()
                pdf.image(img_path, w=110)
                pdf.ln(4)
                frames_processed.add(img_path)
            except Exception:
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 6, "[Snapshot image could not be rendered]", new_x="LMARGIN", new_y="NEXT")
        elif not img_path or not os.path.exists(img_path):
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 5, "No snapshot image found on disk.", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(2)

    pdf.output(filename)
    return filename
