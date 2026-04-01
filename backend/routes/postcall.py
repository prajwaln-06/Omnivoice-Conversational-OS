import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ai.post_call_analyzer import build_whatsapp_message, run_post_call_pipeline
from aws.s3_handler import upload_audio, upload_pdf
from routes.session import create_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/postcall/analyze")
async def postcall_analyze(audio: UploadFile = File(...), domain: str = Form(...)):
    try:
        audio_bytes = await audio.read()
        session_id = str(uuid4())

        result = await run_post_call_pipeline(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.wav",
            session_id=session_id,
            domain=domain,
        )

        try:
            result["audio_s3_url"] = upload_audio(audio_bytes, session_id)
        except Exception as exc:
            logger.warning("Audio upload failed for %s: %s", session_id, exc)
            result["audio_s3_url"] = f"s3://upload-failed/audio/{session_id}.wav"

        pdf_bytes = result.pop("pdf_bytes", b"")
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="PDF generation returned empty bytes")

        try:
            pdf_url = upload_pdf(pdf_bytes, session_id)
        except Exception as exc:
            logger.warning("PDF upload failed for %s: %s", session_id, exc)
            pdf_url = f"s3://upload-failed/prescriptions/{session_id}.pdf"

        result["pdf_url"] = pdf_url
        result["whatsapp_message"] = build_whatsapp_message(result.get("analytics", {}), pdf_url)
        result["status"] = "pending_approval"
        result["created_at"] = datetime.now(timezone.utc).isoformat()

        create_session(result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Post-call pipeline failed")
        raise HTTPException(status_code=500, detail=f"Post-call analyze failed: {exc}")
