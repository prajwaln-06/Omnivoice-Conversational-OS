import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ai.asr import SarvamASR
from ai.post_call_analyzer import analyze_transcript_with_groq
from ai.rag import get_context
from aws.s3_handler import upload_audio
from rag_pipeline.rag import check_contraindications
from routes.session import create_session

logger = logging.getLogger(__name__)
router = APIRouter()


class TranscribeResponse(BaseModel):
    session_id: str
    transcript: str
    language: str
    audio_s3_url: str
    analysis: Optional[dict] = None


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(audio: UploadFile = File(...), domain: str = Form(...), mode: str = Form("conversational")):
    try:
        audio_bytes = await audio.read()
        session_id = str(uuid4())
        filename = audio.filename or 'audio.wav'

        try:
            transcript = SarvamASR().transcribe(audio_bytes, filename=filename)
        except Exception as exc:
            logger.warning("ASR failed for %s: %s", session_id, exc)
            transcript = ""

        analysis = None
        if mode.strip().lower() in {"silent", "passive"}:
            rag_context = await get_context(transcript, domain)
            analysis = analyze_transcript_with_groq(
                transcript=transcript,
                session_id=session_id,
                rag_context=rag_context,
                historical_context="",
            )

            med_names = [
                m.get("name")
                for m in analysis.get("medications", [])
                if isinstance(m, dict)
            ]
            warnings = await check_contraindications(med_names, "")
            if warnings:
                analysis.setdefault("risk_flags", []).extend(warnings)

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
                "extracted_data": analysis or {},
                "analytics": analysis or {},
                "analysis": analysis or {},
                "reminder_schedule": [],
                "whatsapp_message": "",
                "audio_s3_url": audio_s3_url,
                "pdf_url": "",
                "whatsapp_sent": False,
                "status": "completed" if analysis else "pending_approval",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return TranscribeResponse(
            session_id=session_id,
            transcript=transcript,
            language=language,
            audio_s3_url=audio_s3_url,
            analysis=analysis,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Transcribe route failed")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")


@router.post("/passive-listen", response_model=TranscribeResponse)
async def passive_listen_audio(audio: UploadFile = File(...), domain: str = Form(...)):
    """Receive a full audio file in passive mode and return transcript plus structured analysis."""
    return await transcribe_audio(audio=audio, domain=domain, mode="passive")
