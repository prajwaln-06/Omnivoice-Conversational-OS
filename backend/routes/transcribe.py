from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel

MOCK_MODE = True

router = APIRouter()

# ---------- Pydantic Models ----------

class TranscribeResponse(BaseModel):
    session_id: str
    transcript: str
    language: str
    audio_s3_url: str

# ---------- Route ----------

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    domain: str = Form(...),
    mode: str = Form(...)
):
    if MOCK_MODE:
        return TranscribeResponse(
            session_id="mock-session-uuid-1234",
            transcript="Patient reports severe headache for 3 days. Doctor notes possible migraine.",
            language="en-IN",
            audio_s3_url="https://omnivoice-demo.s3.ap-south-1.amazonaws.com/audio/mock-session-uuid-1234.wav"
        )