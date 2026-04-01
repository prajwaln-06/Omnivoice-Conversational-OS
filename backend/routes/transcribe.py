import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ai.asr import SarvamASR
from ai.asr_feedback import log_asr_feedback
from ai.post_call_analyzer import analyze_transcript_with_groq, filter_small_talk
from ai.rag import get_context
from ai.sentiment import IndicBERTSentiment
from aws.s3_handler import upload_audio
from rag_pipeline.rag import check_contraindications
from routes.session import create_session, get_session, update_session

logger = logging.getLogger(__name__)
router = APIRouter()
sentiment_model = IndicBERTSentiment()


def _normalize_field_path(path: str) -> list[str]:
    return [segment.strip() for segment in path.split(".") if segment.strip()]


def _get_nested_value(document: Any, field_path: str) -> Any:
    current = document
    for segment in _normalize_field_path(field_path):
        if isinstance(current, list) and segment.isdigit():
            idx = int(segment)
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
        elif isinstance(current, dict):
            current = current.get(segment)
        else:
            return None
        if current is None:
            return None
    return current


def _set_nested_value(document: Any, field_path: str, value: Any) -> bool:
    current = document
    segments = _normalize_field_path(field_path)
    if not segments:
        return False
    for index, segment in enumerate(segments):
        is_last = index == len(segments) - 1
        if isinstance(current, list) and segment.isdigit():
            idx = int(segment)
            if idx < 0 or idx >= len(current):
                return False
            if is_last:
                current[idx] = value
                return True
            current = current[idx]
        elif isinstance(current, dict):
            if is_last:
                current[segment] = value
                return True
            if segment not in current or not isinstance(current[segment], (dict, list)):
                return False
            current = current[segment]
        else:
            return False
    return False


def _parse_correction_value(text: str, field_path: str) -> Any:
    normalized = text.strip().lower()
    number_match = re.search(r"(?:change|update|set|correct|to)\s*(?:it\s*)?(?:to\s*)?([\d\.]+\s*(?:mg|ml|g|units|hour|hours|day|days|tablet|tablets|capsule|capsules)?)", normalized)
    if number_match:
        value = number_match.group(1).strip()
    else:
        fallback = re.findall(r"([\d\.]+\s*(?:mg|ml|g|units|hour|hours|day|days|tablet|tablets|capsule|capsules)?)", normalized)
        value = fallback[-1].strip() if fallback else normalized

    if field_path.endswith("dosage") and re.fullmatch(r"\d+(?:\.\d+)?", value):
        return f"{value}mg"
    if field_path.endswith("frequency_hours") and re.fullmatch(r"\d+(?:\.\d+)?", value):
        return int(float(value))
    if field_path.endswith("duration_days") and re.fullmatch(r"\d+(?:\.\d+)?", value):
        return int(float(value))
    return value


def _build_sentiment_context(sentiment: Dict[str, Any]) -> str:
    label = sentiment.get("label", "neutral")
    score = float(sentiment.get("score", 0.0))
    empathetic = sentiment.get("empathy_flag", False)
    context = f"Patient emotional state: {label} (score: {score:.2f})."
    if empathetic:
        context += " The patient is emotionally sensitive, so the WhatsApp message should be empathetic and reassuring."
    return context


class TranscribeResponse(BaseModel):
    session_id: str
    transcript: str
    language: str
    audio_s3_url: str
    analysis: Optional[dict] = None
    sentiment: Optional[dict] = None


class FieldCorrectionResponse(BaseModel):
    session_id: str
    field_path: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    correction_transcript: str
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

        cleaned_transcript = filter_small_talk(transcript)
        sentiment = await asyncio.to_thread(sentiment_model.analyze, cleaned_transcript)
        analysis = None

        if mode.strip().lower() in {"silent", "passive"}:
            rag_task = asyncio.create_task(get_context(cleaned_transcript, domain))
            sentiment_task = asyncio.create_task(asyncio.to_thread(sentiment_model.analyze, cleaned_transcript))
            rag_context, sentiment = await asyncio.gather(rag_task, sentiment_task)

            sentiment_context = _build_sentiment_context(sentiment)
            analysis = await asyncio.to_thread(
                analyze_transcript_with_groq,
                cleaned_transcript,
                session_id,
                rag_context,
                "",
                sentiment_context,
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
                "sentiment": sentiment,
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
            sentiment=sentiment,
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


@router.post("/field-correct", response_model=FieldCorrectionResponse)
async def field_correct_audio(
    session_id: str = Form(...),
    field_path: str = Form(...),
    correction_audio: UploadFile = File(...),
):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    audio_bytes = await correction_audio.read()
    try:
        correction_transcript = SarvamASR().transcribe(audio_bytes, filename=correction_audio.filename or "correction.wav")
    except Exception as exc:
        logger.warning("Correction ASR failed for %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail="Failed to transcribe correction audio")

    target_bucket = session.get("extracted_data", {})
    old_value = _get_nested_value(target_bucket, field_path)
    bucket_name = "extracted_data"

    if old_value is None:
        target_bucket = session.get("analysis", {})
        old_value = _get_nested_value(target_bucket, field_path)
        bucket_name = "analysis"

    if old_value is None:
        raise HTTPException(status_code=404, detail=f"Field '{field_path}' not found for correction")

    new_value = _parse_correction_value(correction_transcript, field_path)
    if new_value is None:
        raise HTTPException(status_code=400, detail="Could not parse corrected value from audio")

    if not _set_nested_value(target_bucket, field_path, new_value):
        raise HTTPException(status_code=500, detail="Failed to update the target field")

    update_session(session_id, {bucket_name: target_bucket})
    log_asr_feedback(
        session_id,
        session.get("transcript", ""),
        correction_transcript,
        field_path,
        audio_bytes=audio_bytes,
        metadata={"old_value": old_value, "new_value": new_value, "bucket": bucket_name},
    )

    return FieldCorrectionResponse(
        session_id=session_id,
        field_path=field_path,
        old_value=old_value,
        new_value=new_value,
        correction_transcript=correction_transcript,
        analysis=session.get("analysis"),
    )
