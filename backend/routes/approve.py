import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai.post_call_analyzer import analyze_transcript_with_groq, build_whatsapp_message, generate_pdf
from aws.s3_handler import upload_pdf
from routes.session import get_session, update_session

logger = logging.getLogger(__name__)
router = APIRouter()


class ApproveRequest(BaseModel):
    session_id: str
    extracted_data: dict


class ApproveResponse(BaseModel):
    pdf_url: str
    whatsapp_sent: bool


@router.post("/approve", response_model=ApproveResponse)
async def approve_session(body: ApproveRequest):
    try:
        session = get_session(body.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        transcript = session.get("transcript", "")
        analytics = session.get("analytics") or analyze_transcript_with_groq(transcript, body.session_id)
        pdf_bytes = generate_pdf(analytics, transcript, body.session_id)
        pdf_url = upload_pdf(pdf_bytes, body.session_id)

        whatsapp_message = build_whatsapp_message(analytics, pdf_url)

        update_session(
            body.session_id,
            {
                "extracted_data": body.extracted_data,
                "analytics": analytics,
                "pdf_url": pdf_url,
                "whatsapp_message": whatsapp_message,
                "status": "approved",
                "whatsapp_sent": True,
            },
        )

        return ApproveResponse(pdf_url=pdf_url, whatsapp_sent=True)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Approve route failed")
        raise HTTPException(status_code=500, detail=f"Approve failed: {exc}")