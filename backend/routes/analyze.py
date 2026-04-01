import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai.llm import analyze as analyze_with_groq
from ai.rag import get_context
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
        session = get_session(body.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        schema = get_schema(body.domain)
        if not schema:
            raise HTTPException(status_code=404, detail=f"Schema not loaded for domain '{body.domain}'")

        transcript = session.get("transcript", "")
        rag_context = await get_context(transcript, body.domain)
        extracted_data = await analyze_with_groq(
            transcript=transcript,
            domain=body.domain,
            schema_fields=schema.get("fields", []),
            rag_context=rag_context,
        )

        update_session(body.session_id, {"extracted_data": extracted_data})
        return AnalyzeResponse(session_id=body.session_id, extracted_data=extracted_data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Analyze route failed")
        raise HTTPException(status_code=500, detail=f"Analyze failed: {exc}")