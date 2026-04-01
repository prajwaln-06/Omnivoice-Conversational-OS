import logging
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()

SESSION_STORE: Dict[str, Dict[str, Any]] = {}


class SessionDocument(BaseModel):
    session_id: str
    domain: str
    mode: Literal["conversational", "silent"] = "conversational"
    transcript: str = ""
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    analytics: Dict[str, Any] = Field(default_factory=dict)
    reminder_schedule: list = Field(default_factory=list)
    whatsapp_message: str = ""
    audio_s3_url: str = ""
    pdf_url: str = ""
    whatsapp_sent: bool = False
    status: Literal["pending_approval", "approved", "sent", "completed"] = "pending_approval"
    created_at: str


def create_session(session: Dict[str, Any]) -> Dict[str, Any]:
    SESSION_STORE[session["session_id"]] = session
    return session


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return SESSION_STORE.get(session_id)


def update_session(session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    session = SESSION_STORE.get(session_id)
    if not session:
        return None
    session.update(updates)
    SESSION_STORE[session_id] = session
    return session


@router.get("/session/{session_id}", response_model=SessionDocument)
async def get_session_route(session_id: str):
    try:
        session = get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionDocument(**session)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch session %s", session_id)
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {exc}")