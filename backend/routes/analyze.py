from fastapi import APIRouter
from pydantic import BaseModel

MOCK_MODE = True

router = APIRouter()

# ---------- Pydantic Models ----------

class AnalyzeRequest(BaseModel):
    session_id: str
    domain: str

class AnalyzeResponse(BaseModel):
    session_id: str
    extracted_data: dict

# ---------- Route ----------

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_session(body: AnalyzeRequest):
    if MOCK_MODE:
        return AnalyzeResponse(
            session_id=body.session_id,
            extracted_data={
                "patient_name": "Ravi Kumar",
                "symptoms": ["headache", "nausea", "light sensitivity"],
                "diagnosis": "Migraine without aura",
                "icd10_code": "G43.009",
                "prescription": "Sumatriptan 50mg, once daily"
            }
        )