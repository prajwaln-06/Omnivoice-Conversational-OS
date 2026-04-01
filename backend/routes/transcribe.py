import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ai.asr import SarvamASR
from aws.s3_handler import upload_audio
from routes.session import create_session

logger = logging.getLogger(__name__)
router = APIRouter()


class TranscribeResponse(BaseModel):
    session_id: str
    transcript: str
    language: str
    audio_s3_url: str


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(audio: UploadFile = File(...), domain: str = Form(...), mode: str = Form(...)):
    try:
        audio_bytes = await audio.read()
        session_id = str(uuid4())

        try:
            transcript = SarvamASR().transcribe(audio_bytes)
        except Exception as exc:
            logger.warning("ASR failed for %s: %s", session_id, exc)
            transcript = ""

        try:
            audio_s3_url = upload_audio(audio_bytes, session_id)
        except Exception as exc:
            logger.warning("Audio upload failed for %s: %s", session_id, exc)
            audio_s3_url = f"s3://upload-failed/audio/{session_id}.wav"

        language = "kn-IN" if any(0x0C80 <= ord(ch) <= 0x0CFF for ch in transcript) else "en-IN"

        create_session(
            {
                "session_id": session_id,
                "domain": domain,
                "mode": mode,
                "transcript": transcript,
                "extracted_data": {},
                "analytics": {},
                "reminder_schedule": [],
                "whatsapp_message": "",
                "audio_s3_url": audio_s3_url,
                "pdf_url": "",
                "whatsapp_sent": False,
                "status": "pending_approval",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return TranscribeResponse(
            session_id=session_id,
            transcript=transcript,
            language=language,
            audio_s3_url=audio_s3_url,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Transcribe route failed")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")