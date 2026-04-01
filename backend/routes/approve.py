from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

MOCK_MODE = True

router = APIRouter()

# ---------- Pydantic Models ----------

class ApproveRequest(BaseModel):
    session_id: str
    extracted_data: dict

class ApproveResponse(BaseModel):
    pdf_url: str
    whatsapp_sent: bool

# ---------- Route ----------

@router.post("/approve", response_model=ApproveResponse)
async def approve_session(body: ApproveRequest):
    if MOCK_MODE:
        mock_pdf_url = (
            f"https://your-cloudfront-domain.cloudfront.net"
            f"/prescriptions/{body.session_id}.pdf"
        )
        return ApproveResponse(
            pdf_url=mock_pdf_url,
            whatsapp_sent=True
        )