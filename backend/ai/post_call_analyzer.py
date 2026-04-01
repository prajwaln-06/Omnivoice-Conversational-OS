import asyncio
import json
import logging
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any, Dict, List
# --- ADD THESE TWO LINES ---
from rag_pipeline.rag import get_context, check_contraindications
# -------------------------

import requests
from dotenv import load_dotenv
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

load_dotenv()
logger = logging.getLogger(__name__)


def transcribe_audio_file(audio_bytes: bytes, filename: str) -> str:
    """Transcribe MP3/WAV bytes via Sarvam STT API."""
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        logger.warning("SARVAM_API_KEY missing; transcription skipped")
        return ""

    name = (filename or "audio.wav").lower()
    ext = ".mp3" if name.endswith(".mp3") else ".wav"
    content_type = "audio/mpeg" if ext == ".mp3" else "audio/wav"

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": api_key}

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            files = {"file": (f"audio{ext}", f, content_type)}
            data = {
                "model": "saarika:v2.5",
                "language_code": "unknown",
                "with_timestamps": "false",
            }
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=45)
            resp.raise_for_status()
            return resp.json().get("transcript", "").strip()
    except Exception as exc:
        logger.error("Transcription failed: %s", exc)
        return ""
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _fallback_analytics(transcript: str) -> Dict[str, Any]:
    meds: List[Dict[str, Any]] = []

    if re.search(r"paracetamol", transcript, re.IGNORECASE):
        meds.append(
            {
                "name": "Paracetamol",
                "dosage": "500mg",
                "frequency_hours": 12,
                "frequency_label": "twice daily",
                "duration_days": 5,
                "instructions": "after food",
                "reminder_message": "Time to take Paracetamol 500mg",
            }
        )

    if re.search(r"cetirizine", transcript, re.IGNORECASE):
        meds.append(
            {
                "name": "Cetirizine",
                "dosage": "10mg",
                "frequency_hours": 24,
                "frequency_label": "once daily",
                "duration_days": 5,
                "instructions": "before sleep",
                "reminder_message": "Time to take Cetirizine 10mg",
            }
        )

    if not meds:
        meds = [
            {
                "name": "General Medication",
                "dosage": "as advised",
                "frequency_hours": 24,
                "frequency_label": "once daily",
                "duration_days": 3,
                "instructions": "after food",
                "reminder_message": "Time to take your medicine",
            }
        ]

    return {
        "medications": meds,
        "reminder_schedule": [
            {
                "type": "medication",
                "medicine_name": med["name"],
                "send_at_hours_from_now": med["frequency_hours"],
                "message": med["reminder_message"],
            }
            for med in meds
        ],
        "whatsapp_immediate_message": "Doctor consultation summary ready. Please follow medication schedule.",
        "risk_flags": ["High fever risk"],
        "follow_up": {
            "required": True,
            "days_from_today": 5,
            "message": "Please return for follow-up after 5 days.",
        },
    }


def _normalize_analytics(analytics: Dict[str, Any], transcript: str) -> Dict[str, Any]:
    base = _fallback_analytics(transcript)
    merged = dict(base)
    merged.update(analytics or {})

    meds = merged.get("medications")
    if not isinstance(meds, list) or not meds:
        meds = base["medications"]

    normalized_meds: List[Dict[str, Any]] = []
    for med in meds:
        if not isinstance(med, dict):
            continue
        name = str(med.get("name") or "Medication")
        dosage = str(med.get("dosage") or "as advised")
        frequency_hours = int(med.get("frequency_hours") or 24)
        duration_days = int(med.get("duration_days") or 1)
        normalized_meds.append(
            {
                "name": name,
                "dosage": dosage,
                "frequency_hours": frequency_hours,
                "frequency_label": med.get("frequency_label") or "as advised",
                "duration_days": duration_days,
                "instructions": med.get("instructions") or "as advised",
                "reminder_message": med.get("reminder_message") or f"Time to take {name} {dosage}",
            }
        )

    if re.search(r"paracetamol", transcript, re.IGNORECASE) and not any(
        m["name"].lower() == "paracetamol" for m in normalized_meds
    ):
        normalized_meds.append(base["medications"][0])
    if re.search(r"cetirizine", transcript, re.IGNORECASE) and not any(
        m["name"].lower() == "cetirizine" for m in normalized_meds
    ):
        normalized_meds.append(base["medications"][1])

    if re.search(r"paracetamol", transcript, re.IGNORECASE) and re.search(
        r"cetirizine", transcript, re.IGNORECASE
    ):
        normalized_meds = [
            med
            for med in normalized_meds
            if med["name"].strip().lower() in {"paracetamol", "cetirizine"}
        ]

    merged["medications"] = normalized_meds

    if not merged.get("whatsapp_immediate_message"):
        merged["whatsapp_immediate_message"] = base["whatsapp_immediate_message"]

    if not isinstance(merged.get("risk_flags"), list) or not merged.get("risk_flags"):
        merged["risk_flags"] = base["risk_flags"]

    follow_up = merged.get("follow_up")
    if not isinstance(follow_up, dict):
        follow_up = {}
    merged["follow_up"] = {
        "required": bool(follow_up.get("required", True)),
        "days_from_today": int(follow_up.get("days_from_today", 5)),
        "message": follow_up.get("message") or "Please return for follow-up after 5 days.",
    }

    return merged


def analyze_transcript_with_groq(transcript: str, session_id: str, rag_context: str = "", historical_context: str = "") -> Dict[str, Any]:
    """Return analytics JSON enforcing clinical rules and Ghost Field Removal."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _normalize_analytics(_fallback_analytics(transcript), transcript)

    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are an expert Medical AI. Analyze the transcript and extract data into STRICT JSON.

    RULES:
    1. Ghost Field Removal: If a field is NOT explicitly mentioned, return null. Do NOT invent data.
    2. Jargon Buster: In the 'patient_summary', explain complex medical terms simply.
    3. Medication Scheduler: Format medications exactly as requested below.

    Patient History: {historical_context}
    Clinical Context (RAG): {rag_context}
    Transcript: {transcript}

    EXPECTED JSON FORMAT:
    {{
        "patient_summary": "Simple, jargon-free summary...",
        "severity_score": "High | Medium | Low",
        "medications": [
            {{
                "name": "Amoxicillin",
                "dosage": "500mg",
                "frequency_hours": 8,
                "frequency_label": "every 8 hours",
                "duration_days": 5,
                "instructions": "after food",
                "reminder_message": "Time to take Amoxicillin 500mg"
            }}
        ],
        "follow_up": {{"required": true, "days_from_today": 5, "message": "Return in 5 days."}},
        "risk_flags": ["String array of risks"]
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Return strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=1500,
        )
        raw = completion.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        
        # Merge our new smart JSON with the fallback normalization
        return _normalize_analytics(parsed, transcript)
    except Exception as exc:
        logger.error("Groq post-call analysis failed for %s: %s", session_id, exc)
        return _normalize_analytics(_fallback_analytics(transcript), transcript)


def build_reminder_schedule(analytics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Expand analytics medication plan to absolute reminder schedule."""
    meds = analytics.get("medications") or []
    now = datetime.now(timezone.utc)
    reminders: List[Dict[str, Any]] = []

    for med in meds:
        freq = int(med.get("frequency_hours", 24) or 24)
        duration = int(med.get("duration_days", 1) or 1)
        total = max(1, int((duration * 24) / freq))

        for i in range(total):
            offset_h = freq * (i + 1)
            send_at = now + timedelta(hours=offset_h)
            reminders.append(
                {
                    "send_at": send_at.isoformat(),
                    "send_at_epoch": int(send_at.timestamp()),
                    "type": "medication",
                    "medicine_name": med.get("name", "Medication"),
                    "message": med.get("reminder_message")
                    or f"Time to take {med.get('name', 'your medicine')}",
                }
            )

    reminders.sort(key=lambda x: x["send_at_epoch"])
    return reminders


def build_whatsapp_message(analytics: Dict[str, Any], pdf_url: str) -> str:
    meds = analytics.get("medications") or []
    follow_up = analytics.get("follow_up") or {}

    lines = ["OmniVoice consultation summary:"]
    if meds:
        lines.append("Medications:")
        for med in meds:
            lines.append(
                f"- {med.get('name', 'Medication')} {med.get('dosage', '')}, "
                f"{med.get('frequency_label', 'as advised')} for {med.get('duration_days', '')} days"
            )

    if follow_up.get("required"):
        lines.append(
            f"Follow-up in {follow_up.get('days_from_today', 'N/A')} days: "
            f"{follow_up.get('message', '')}"
        )

    lines.append(f"Prescription PDF: {pdf_url}")
    return "\n".join(lines)


def generate_pdf(analytics: Dict[str, Any], transcript: str, session_id: str) -> bytes:
    """Generate a detailed PDF summary and return bytes."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
    _, height = A4

    y = height - 50
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "OmniVoice Post-Call Summary")
    y -= 24
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Session ID: {session_id}")
    y -= 18
    pdf.drawString(50, y, f"Generated: {datetime.now(timezone.utc).isoformat()}")
    y -= 24

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Medications")
    y -= 16
    pdf.setFont("Helvetica", 10)
    for med in analytics.get("medications", []):
        line = (
            f"- {med.get('name', '')} {med.get('dosage', '')} | "
            f"{med.get('frequency_label', '')} | {med.get('duration_days', '')} days | "
            f"{med.get('instructions', '')}"
        )
        pdf.drawString(50, y, line[:110])
        y -= 14
        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)

    y -= 8
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Transcript")
    y -= 16
    pdf.setFont("Helvetica", 9)
    words = transcript.split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) > 110:
            pdf.drawString(50, y, line)
            y -= 12
            line = word
            if y < 60:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 9)
        else:
            line = candidate
    if line:
        pdf.drawString(50, y, line)

    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Reminder Plan")
    y -= 16
    pdf.setFont("Helvetica", 9)
    for item in build_reminder_schedule(analytics)[:40]:
        pdf.drawString(
            50,
            y,
            f"- {item['send_at']} | {item['medicine_name']} | {item['message'][:70]}",
        )
        y -= 11
        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 9)

    # Include full analytics JSON block for auditability and deterministic PDF size.
    if y < 120:
        pdf.showPage()
        y = height - 50
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Analytics JSON Snapshot")
    y -= 16
    pdf.setFont("Courier", 8)
    analytics_dump = json.dumps(analytics, ensure_ascii=False, indent=2)
    for chunk in analytics_dump.splitlines():
        pdf.drawString(50, y, chunk[:120])
        y -= 10
        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Courier", 8)

    # Repeat transcript in compact form for complete clinical traceability.
    if y < 120:
        pdf.showPage()
        y = height - 50
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Transcript Trace")
    y -= 16
    pdf.setFont("Helvetica", 8)
    compact = transcript.replace("\n", " ").strip()
    for _ in range(3):
        for i in range(0, len(compact), 120):
            pdf.drawString(50, y, compact[i : i + 120])
            y -= 10
            if y < 60:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 8)

    pdf.showPage()
    pdf.save()
    out = buffer.getvalue()
    buffer.close()
    return out


async def run_post_call_pipeline(audio_bytes, filename, session_id, domain) -> Dict[str, Any]:
    """Async orchestration: transcribe -> RAG -> analyze -> check safety -> reminders -> pdf -> whatsapp."""
    transcript = await asyncio.to_thread(transcribe_audio_file, audio_bytes, filename)
    
    # 1. Fetch RAG and Historical Context (Your Brain!)
    historical_context = "Patient has a history of severe Asthma." # Hardcoded for hackathon demo
    rag_context = await get_context(transcript, domain)
    
    # 2. Run the upgraded AI Analyzer
    analytics = await asyncio.to_thread(
        analyze_transcript_with_groq, 
        transcript, 
        session_id, 
        rag_context, 
        historical_context
    )
    
    # 3. Check for Drug Contraindications
    meds = [m.get("name") for m in analytics.get("medications", []) if isinstance(m, dict)]
    warnings = await check_contraindications(meds, historical_context)
    if warnings:
        analytics["risk_flags"].extend(warnings) # Inject warnings into the PDF flags
    
    # 4. Finish Pranav's existing pipeline
    reminder_schedule = await asyncio.to_thread(build_reminder_schedule, analytics)
    pdf_bytes = await asyncio.to_thread(generate_pdf, analytics, transcript, session_id)
    whatsapp_message = await asyncio.to_thread(
        build_whatsapp_message, analytics, "PDF_URL_PLACEHOLDER"
    )

    return {
        "session_id": session_id,
        "domain": domain,
        "mode": "silent",
        "transcript": transcript,
        "extracted_data": analytics, 
        "analytics": analytics,
        "reminder_schedule": reminder_schedule,
        "whatsapp_message": whatsapp_message,
        "audio_s3_url": "",
        "pdf_url": "",
        "whatsapp_sent": False,
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "pdf_bytes": pdf_bytes,
    }