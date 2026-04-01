from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO

def generate_prescription_pdf(data):
    """Generates a professional PDF in memory and returns bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Custom Professional Styles
    header_style = ParagraphStyle('Header', fontSize=20, textColor=colors.navy, spaceAfter=20, alignment=1)
    label_style = ParagraphStyle('Label', fontSize=10, textColor=colors.grey, spaceBefore=5)
    value_style = ParagraphStyle('Value', fontSize=12, spaceAfter=10)

    # Header Title
    domain_name = data.get('domain', 'Service').upper()
    elements.append(Paragraph(f"OMNIVOICE {domain_name} SUMMARY", header_style))
    elements.append(Spacer(1, 12))

    # Data Table Construction
    ext_data = data.get('extracted_data', {})
    table_data = []
    for key, value in ext_data.items():
        clean_key = key.replace('_', ' ').title()
        table_data.append([clean_key, str(value)])

    # Grid Design
    summary_table = Table(table_data, colWidths=[150, 300])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkslategray),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Signature/Footer
    elements.append(Paragraph("__________________________", styles['Normal']))
    elements.append(Paragraph("Authorized Digital Signature (OmniVoice AI)", styles['Normal']))

    doc.build(elements)
    pdf_out = buffer.getvalue()
    buffer.close()
    return pdf_out