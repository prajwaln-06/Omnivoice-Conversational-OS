import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _save_audio(session_id: str, timestamp: str, audio_bytes: bytes) -> str:
    base_dir = Path(__file__).resolve().parent.parent / "asr_feedback_audio"
    _ensure_dir(base_dir)
    filename = base_dir / f"{session_id}_{timestamp}.wav"
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    return str(filename)


def log_asr_feedback(
    session_id: str,
    original_transcript: str,
    corrected_transcript: str,
    correction_command: str,
    audio_bytes: Optional[bytes] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    timestamp = datetime.utcnow().isoformat().replace(":", "-")
    record = {
        "session_id": session_id,
        "original_transcript": original_transcript,
        "corrected_transcript": corrected_transcript,
        "correction_command": correction_command,
        "timestamp": timestamp,
        "metadata": metadata or {},
    }

    if audio_bytes:
        try:
            record["audio_path"] = _save_audio(session_id, timestamp, audio_bytes)
        except Exception as exc:
            logger.warning("[ASR Feedback] Failed to save audio: %s", exc)

    mongo_uri = os.getenv("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB", "omni_voice")
    if mongo_uri and MONGODB_AVAILABLE:
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            collection = client[mongo_db].asr_feedback_logs
            collection.insert_one(record)
            logger.info("[ASR Feedback] logged to MongoDB for session %s", session_id)
            return
        except Exception as exc:
            logger.warning("[ASR Feedback] MongoDB write failed: %s", exc)

    fallback_path = Path(__file__).resolve().parent.parent / "asr_feedback_logs.jsonl"
    _ensure_dir(fallback_path.parent)
    try:
        with open(fallback_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("[ASR Feedback] logged locally for session %s", session_id)
    except Exception as exc:
        logger.error("[ASR Feedback] local log failed: %s", exc)
