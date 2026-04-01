# backend/ai/document_generator.py
import os
import json
import logging
from datetime import datetime
from io import BytesIO

from groq import Groq

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# GROQ DOCUMENT GENERATION
# ─────────────────────────────────────────

def generate_with_groq(
    transcript: str,
    extracted_data: dict,
    rag_context: str,
    domain: str,
    session_id: str,
) -> dict:
    """
    Sends transcript + context to Groq (Llama 3 70B).
    Returns a structured document dict ready for PDF rendering.
    """
    
    domain_prompts = {
        "healthcare": """You are a medical documentation AI. 
Based on the conversation transcript and context provided, 
generate a complete, professional clinical consultation summary.

Structure your response as a JSON object with these exact keys:
{
  "document_title": "Clinical Consultation Summary",
  "patient_name": "extracted or Unknown",
  "date": "today's date",
  "chief_complaint": "main reason for visit in one sentence",
  "history_of_present_illness": "detailed paragraph about symptoms and timeline",
  "symptoms": ["list", "of", "symptoms"],
  "vital_signs": {"fever": "value", "other": "value"},
  "assessment": "clinical assessment paragraph",
  "diagnosis": "likely diagnosis",
  "treatment_plan": ["step 1", "step 2", "step 3"],
  "medications": [
    {"name": "med name", "dosage": "dose", "frequency": "how often", "duration": "how long"}
  ],
  "follow_up": "follow up instructions",
  "doctor_notes": "any additional notes",
  "disclaimer": "AI-assisted documentation. Verify with clinician."
}""",

        "banking": """You are a financial documentation AI.
Based on the conversation transcript, generate a complete loan 
application summary document.

Structure your response as a JSON object with these exact keys:
{
  "document_title": "Loan Application Summary",
  "customer_name": "extracted or Unknown",
  "date": "today's date",
  "loan_type": "type of loan requested",
  "loan_amount": "amount requested",
  "purpose": "purpose of loan",
  "monthly_income": "stated income",
  "employment_type": "salaried/self-employed",
  "tenure_requested": "years",
  "emi_estimate": "calculated EMI",
  "eligibility_assessment": "brief assessment paragraph",
  "documents_required": ["doc 1", "doc 2", "doc 3"],
  "next_steps": ["step 1", "step 2"],
  "officer_notes": "any additional notes",
  "disclaimer": "AI-assisted summary. Subject to credit verification."
}""",
        "generic": f"""You are a professional enterprise documentation AI. 
Based on the conversation transcript, extracted data, and context provided, 
generate a complete, professional summary document perfectly tailored for the '{domain}' domain.

Structure your response strictly as a JSON object. You must include:
1. "document_title": A professional title for this {domain} document.
2. "date": Today's date.
3. Every single key present in the 'EXTRACTED DATA' dictionary. Expand on their values using the conversation transcript to create readable, professional phrasing and formatting where appropriate.
4. "disclaimer": "AI-assisted {domain} documentation. Verify before taking action."

IMPORTANT: 
- Return ONLY the JSON object.
- No explanation. No markdown fences.
"""
    }

    # Use the specific prompt if healthcare/banking, else use the dynamic generic one
    system_prompt = domain_prompts.get(domain.lower(), domain_prompts["generic"])

    user_message = f"""
CONVERSATION TRANSCRIPT:
{transcript}

EXTRACTED DATA:
{json.dumps(extracted_data, indent=2)}

RAG CONTEXT:
{rag_context}

Today's date: {datetime.now().strftime("%d %B %Y")}
Session ID: {session_id}

Generate the structured JSON document now. 
Return ONLY the JSON object. No explanation. No markdown fences.
"""

    try:
        # Initialize Groq client
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
        )

        raw_text = response.choices[0].message.content

        # Clean any accidental markdown from LLM response
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        document_data = json.loads(raw_text)
        logger.info(f"[Groq] Document generated for session {session_id}")
        return document_data

    except Exception as e:
        logger.error(f"[Groq] Generation failed: {e}")
        # Fallback — build document from extracted_data without Groq
        return _fallback_document(extracted_data, domain, session_id)


def _fallback_document(extracted_data: dict, domain: str, session_id: str) -> dict:
    """If Groq fails, build a generic basic document dynamically from extracted fields."""
    # Attempt to extract some common name fields for the top banner
    person_name = extracted_data.get("patient_name", 
                    extracted_data.get("customer_name", 
                    extracted_data.get("name", "Unknown")))

    doc = {
        "document_title": f"{domain.title()} Summary",
        "date": datetime.now().strftime("%d %B %Y"),
        "person_name": person_name,
        "disclaimer": f"AI-assisted {domain} summary. Verify before action."
    }

    # Dynamically inject all remaining keys from the extracted_data schema
    for k, v in extracted_data.items():
        if k not in ["patient_name", "customer_name", "name"]:
            doc[k] = v

    return doc


# ─────────────────────────────────────────
# PDF RENDERER
# ─────────────────────────────────────────

def render_document_to_pdf(document_data: dict, domain: str) -> bytes:
    """
    Takes the structured document dict.
    Renders a beautiful professional PDF.
    Returns bytes — never writes to disk.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    # ── STYLES ──
    styles = getSampleStyleSheet()

    style_header = ParagraphStyle(
        "OVHeader",
        fontSize=22,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    style_subheader = ParagraphStyle(
        "OVSub",
        fontSize=11,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName="Helvetica",
        spaceAfter=2,
    )
    style_section = ParagraphStyle(
        "OVSection",
        fontSize=12,
        textColor=colors.HexColor("#1a4f7a"),
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=4,
    )
    style_body = ParagraphStyle(
        "OVBody",
        fontSize=10,
        textColor=colors.HexColor("#2d2d2d"),
        fontName="Helvetica",
        spaceAfter=4,
        leading=16,
    )
    style_disclaimer = ParagraphStyle(
        "OVDisclaimer",
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        fontName="Helvetica-Oblique",
        spaceBefore=20,
    )

    elements = []

    # ── HEADER BANNER ──
    title = document_data.get("document_title", "OmniVoice Summary")
    date = document_data.get("date", datetime.now().strftime("%d %B %Y"))

    header_table = Table(
        [[
            Paragraph(f"🏥 {title}", style_header) if domain == "healthcare" else Paragraph(f"💰 {title}", style_header),
            Paragraph(f"OmniVoice AI\n{date}", style_subheader),
        ]],
        colWidths=[120*mm, 50*mm]
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0a1628")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [5, 5, 5, 5]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    # ── PATIENT/CUSTOMER INFO ROW ──
    # Check for anything that hints at an entity name
    name = document_data.get("patient_name", 
               document_data.get("customer_name", 
                   document_data.get("person_name", 
                       document_data.get("applicant_name", "Unknown"))))
                       
    info_label = "Name"

    info_table = Table(
        [[
            f"{info_label}: {name}",
            f"Date: {date}",
            f"Domain: {domain.title()}",
        ]],
        colWidths=[60*mm, 60*mm, 50*mm]
    )
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4fb")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a4f7a")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1a4f7a")),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # ── HELPER: section divider ──
    def add_section(title):
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#1a4f7a"),
            spaceAfter=4
        ))
        elements.append(Paragraph(title.upper(), style_section))

    # ── DOMAIN SPECIFIC SECTIONS ──
    _render_dynamic_sections(document_data, elements, add_section, style_body, style_disclaimer)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def _render_dynamic_sections(data, elements, add_section, style_body, style_disclaimer):
    """Render PDF sections automatically based on any JSON schema returned by the LLM."""
    
    ignore_keys = ["document_title", "date", "patient_name", "customer_name", "person_name", "applicant_name", "disclaimer"]
    
    for key, val in data.items():
        if key.lower() in ignore_keys or not val:
            continue
            
        formatted_title = str(key).replace("_", " ").title()
        add_section(formatted_title)
        
        # Handle lists (e.g. Next Steps, Symptoms, Documents Required)
        if isinstance(val, list):
            if val and isinstance(val[0], dict):
                # Table format for a list of dictionaries (like medications with dose/duration properties)
                headers = list(val[0].keys())
                header_row = [h.replace("_", " ").title() for h in headers]
                
                rows = [header_row]
                for item in val:
                    rows.append([str(item.get(h, "")) for h in headers])
                
                col_width = (170/len(headers))*mm
                t_widths = [col_width] * len(headers)
                t = Table(rows, colWidths=t_widths)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a1628")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                elements.append(t)
            else:
                # Normal list format
                for i, item in enumerate(val, 1):
                    elements.append(Paragraph(f"• {item}", style_body))
        
        # Handle dictionaries (e.g. Vital Signs)
        elif isinstance(val, dict):
            rows = [[k.replace("_", " ").title(), str(v)] for k, v in val.items()]
            t = Table(rows, colWidths=[80*mm, 80*mm])
            t.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef4fb")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            elements.append(t)
        
        # Standard String / Text block
        else:
            elements.append(Paragraph(str(val), style_body))
            
        elements.append(Spacer(1, 4))
        
    elements.append(Spacer(1, 20))
    sig_table = Table(
        [["_______________________", "_______________________"]],
        colWidths=[85*mm, 85*mm]
    )
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.grey),
    ]))
    elements.append(sig_table)
    
    label_table = Table(
        [["Authority Signature", "Client/Patient Signature"]],
        colWidths=[85*mm, 85*mm]
    )
    label_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(label_table)
        
    # Append the disclaimer at the very bottom
    elements.append(Paragraph(
        data.get("disclaimer", f"AI-assisted {data.get('domain', 'document')} documentation. Ensure you verify with a professional."),
        style_disclaimer
    ))
    elements.append(Paragraph(
        "🔒 Secured & Delivered via OmniVoice Engine | AWS S3 + CloudFront",
        style_disclaimer
    ))


# ─────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────

async def generate_and_render_pdf(
    transcript: str,
    extracted_data: dict,
    rag_context: str,
    domain: str,
    session_id: str,
) -> bytes:
    """
    Full pipeline:
    transcript + RAG + extracted_data
    → Groq (Llama 3 70B)
    → structured document
    → beautiful PDF bytes
    """
    # Step 1: Groq generates structured document
    document_data = generate_with_groq(
        transcript=transcript,
        extracted_data=extracted_data,
        rag_context=rag_context,
        domain=domain,
        session_id=session_id,
    )

    # Step 2: Render to PDF
    pdf_bytes = render_document_to_pdf(document_data, domain)

    logger.info(
        f"[DocGen] PDF ready for session {session_id} "
        f"({len(pdf_bytes)} bytes)"
    )
    return pdf_bytes


# ─────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    test_session = {
        "session_id": "test-groq-001",
        "domain": "healthcare",
        "transcript": """
Doctor: Namaskara, barthiri. Hegiddira?
Patient: Doctor, naanu 2 days-ininda bahala kashi aagide. 
         Fever ide, around 101 temperature.
Doctor: Headache kuda idiya?
Patient: Haan doctor, headache and body pain kuda bahala ide.
Doctor: Ok. I'll prescribe Dolo 650, once tab 3x daily after food.
        ORS also take twice daily. Rest for 5 days.
Patient: Ok doctor. Follow up yavaga?
Doctor: 5 days later come.
        """,
        "extracted_data": {
            "patient_name": "Ravi Kumar",
            "age": "34",
            "symptoms": ["fever 101F", "headache", "body ache"],
            "duration": "2 days",
            "prescription": "Dolo 650 - 1 tab 3x daily, ORS twice daily",
            "follow_up": "5 days"
        }
    }

    async def test():
        # Using a dummy RAG context for standalone testing
        rag_ctx = "RAG CONTEXT: Fever and headache are common symptoms of viral infections."
        
        pdf_bytes = await generate_and_render_pdf(
            transcript=test_session["transcript"],
            extracted_data=test_session["extracted_data"],
            rag_context=rag_ctx,
            domain=test_session["domain"],
            session_id=test_session["session_id"],
        )
        with open("test_groq_prescription.pdf", "wb") as f:
            f.write(pdf_bytes)
        print(f"✅ PDF generated: {len(pdf_bytes)} bytes")
        print("Open test_groq_prescription.pdf to review")

    asyncio.run(test())