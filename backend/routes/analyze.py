import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# --- YOUR NEW IMPORTS ---
from ai.post_call_analyzer import analyze_transcript_with_groq
# Assuming check_contraindications is in the same file as get_context
from ai.rag import get_context
from rag_pipeline.rag import check_contraindications
# ------------------------

from routes.schema import get_schema
from routes.session import get_session, update_session

logger = logging.getLogger(__name__)
router = APIRouter()

class AnalyzeRequest(BaseModel):
    session_id: str
    domain: str

class AnalyzeResponse(BaseModel):
    session_id: str
    extracted_data: dict

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_session(body: AnalyzeRequest):
    try:
        # --- PRAJWAL'S DB LOGIC (DO NOT TOUCH) ---
        session = get_session(body.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        schema = get_schema(body.domain)
        if not schema:
            raise HTTPException(status_code=404, detail=f"Schema not loaded for domain '{body.domain}'")
        # -----------------------------------------

        transcript = session.get("transcript", "")
        
        # 1. Fetch Longitudinal History (Mocked for the hackathon demo)
        historical_context = "Patient has a history of severe Asthma."

        # 2. Get your Medical RAG Context
        rag_context = await get_context(transcript, body.domain)
        
        # 3. Call YOUR upgraded analyzer instead of the old one
        extracted_data = await analyze_transcript_with_groq(
            transcript=transcript,
            session_id=body.session_id,
            rag_context=rag_context,
            historical_context=historical_context
        )

        # 4. Check for drug conflicts (Your Safety Feature!)
        med_names = [m.get("name") for m in extracted_data.get("medications", []) if isinstance(m, dict)]
        warnings = await check_contraindications(med_names, historical_context)
        
        if warnings:
            if "risk_flags" not in extracted_data:
                extracted_data["risk_flags"] = []
            extracted_data["risk_flags"].extend(warnings)

        # --- PRAJWAL'S DB LOGIC (DO NOT TOUCH) ---
        update_session(body.session_id, {"extracted_data": extracted_data})
        return AnalyzeResponse(session_id=body.session_id, extracted_data=extracted_data)
        # -----------------------------------------

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Analyze route failed")
        raise HTTPException(status_code=500, detail=f"Analyze failed: {exc}")