from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

MOCK_MODE = True

router = APIRouter()

# ---------- Pydantic Models ----------

class SessionDocument(BaseModel):
    session_id: str
    domain: str
    mode: str
    transcript: str
    extracted_data: dict
    status: str
    audio_s3_url: str
    pdf_url: Optional[str] = None
    whatsapp_sent: bool
    created_at: str

# ---------- Route ----------

@router.get("/session/{session_id}", response_model=SessionDocument)
async def get_session(session_id: str):
    if MOCK_MODE:
        return SessionDocument(
            session_id=session_id,
            domain="healthcare",
            mode="silent",
            transcript="Patient reports severe headache for 3 days.",
            extracted_data={
                "patient_name": "Ravi Kumar",
                "diagnosis": "Migraine without aura",
                "icd10_code": "G43.009"
            },
            status="approved",
            audio_s3_url=f"https://omnivoice-demo.s3.ap-south-1.amazonaws.com/audio/{session_id}.wav",
            pdf_url=f"https://your-cloudfront-domain.cloudfront.net/prescriptions/{session_id}.pdf",
            whatsapp_sent=True,
            created_at="2025-01-01T10:00:00Z"
        )