import os
import sys
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ai.asr import SarvamASR
from ai.document_generator import generate_with_groq, render_document_to_pdf
from voice_auto_send import build_and_send_pdf_from_conversation, run_live_tts_conversation

logger = logging.getLogger(__name__)
router = APIRouter()

_WHATSAPP_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "whatsapp-mcp",
    "whatsapp-mcp-server",
)
if _WHATSAPP_SERVER_PATH not in sys.path:
    sys.path.append(_WHATSAPP_SERVER_PATH)

from whatsapp import send_file, send_message  # noqa: E402


GENERATED_DOCS_DIR = Path(__file__).resolve().parent.parent / "generated_docs"
GENERATED_DOCS_DIR.mkdir(parents=True, exist_ok=True)


class LiveAgentRequest(BaseModel):
    domain: str = "healthcare"
    recipient: Optional[str] = None
    max_turns: int = 8
    input_device_hint: Optional[str] = None
    output_device_hint: Optional[str] = None


def _normalize_recipient(phone: Optional[str]) -> str:
    if not phone:
        return ""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("91") and len(digits) == 12:
        return digits
    if len(digits) == 10:
        return f"91{digits}"
    return digits


def _build_pdf_url(path: str) -> str:
    filename = os.path.basename(path)
    return f"/api/agent/pdf/{filename}"


@router.post("/agent/live")
async def run_agent_live(body: LiveAgentRequest):
    try:
        conversation = run_live_tts_conversation(
            domain=body.domain,
            max_turns=body.max_turns,
            input_hint=body.input_device_hint,
            output_hint=body.output_device_hint,
        )

        if not conversation.get("transcript"):
            raise HTTPException(status_code=400, detail="No transcript captured from live session")

        recipient = _normalize_recipient(body.recipient or os.getenv("OMNIVOICE_WHATSAPP_TO", ""))
        result = build_and_send_pdf_from_conversation(conversation, recipient)

        return {
            "status": "success",
            "session_id": result.get("session_id"),
            "transcript": conversation.get("transcript", ""),
            "extracted_data": result.get("document_data", {}),
            "pdf_url": _build_pdf_url(result.get("pdf_path", "")),
            "whatsapp_sent": result.get("file_sent", False),
            "whatsapp_response": result.get("file_response", ""),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Live agent execution failed")
        raise HTTPException(status_code=500, detail=f"Live agent execution failed: {exc}")


@router.post("/agent/passive")
async def run_agent_passive(
    audio: UploadFile = File(...),
    domain: str = Form("healthcare"),
    recipient: str = Form(""),
):
    try:
        audio_bytes = await audio.read()
        session_id = str(uuid.uuid4())

        transcript = SarvamASR().transcribe(audio_bytes, filename=audio.filename or "audio.wav")
        if not transcript:
            raise HTTPException(status_code=400, detail="Could not transcribe uploaded audio")

        rag_context = "Conversation captured from OmniVoice passive uploaded audio workflow."
        extracted_seed = {
            "session_id": session_id,
            "conversation_turns": 1,
            "conversation_date": datetime.now().strftime("%d %B %Y"),
        }
        document_data = generate_with_groq(
            transcript=transcript,
            extracted_data=extracted_seed,
            rag_context=rag_context,
            domain=domain,
            session_id=session_id,
        )

        pdf_bytes = render_document_to_pdf(document_data, domain=domain)
        pdf_path = GENERATED_DOCS_DIR / f"omni_report_{session_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)

        normalized_to = _normalize_recipient(recipient or os.getenv("OMNIVOICE_WHATSAPP_TO", ""))
        intro_ok = False
        intro_msg = "Skipped: recipient missing"
        file_ok = False
        file_msg = "Skipped: recipient missing"

        if normalized_to:
            intro_ok, intro_msg = send_message(
                normalized_to,
                f"OmniVoice passive analysis is ready for session {session_id}. Sending PDF now.",
            )
            file_ok, file_msg = send_file(normalized_to, str(pdf_path))

        return {
            "status": "success",
            "session_id": session_id,
            "transcript": transcript,
            "extracted_data": document_data,
            "pdf_url": _build_pdf_url(str(pdf_path)),
            "whatsapp_sent": file_ok,
            "whatsapp_response": file_msg,
            "whatsapp_intro_sent": intro_ok,
            "whatsapp_intro_response": intro_msg,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Passive agent execution failed")
        raise HTTPException(status_code=500, detail=f"Passive agent execution failed: {exc}")


@router.get("/agent/pdf/{file_name}")
async def download_generated_pdf(file_name: str):
    safe_name = os.path.basename(file_name)
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    target = GENERATED_DOCS_DIR / safe_name
    if not target.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(path=str(target), filename=safe_name, media_type="application/pdf")
