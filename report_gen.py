from fpdf import FPDF

def generate_pdf_report(events, filename="report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="YOLOv8 Surveillance Report", ln=True, align='C')
    pdf.ln(10)

    if not events:
        pdf.cell(200, 10, txt="No objects were detected.", ln=True)
    else:
        for i, event in enumerate(events, 1):
            txt = f"{i}. {event['label']} - Confidence: {event['confidence']}"
            pdf.cell(200, 10, txt=txt, ln=True)

    pdf.output(filename)