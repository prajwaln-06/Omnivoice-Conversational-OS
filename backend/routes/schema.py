from fastapi import FastAPI, APIRouter, UploadFile, File, Body
from pydantic import BaseModel
from typing import Optional

MOCK_MODE = True

router = APIRouter()

# ---------- Pydantic Models ----------

class SchemaBody(BaseModel):
    schema: Optional[dict] = None

class SchemaResponse(BaseModel):
    domain: str
    fields: list
    system_prompt: str

# ---------- Route ----------

@router.post("/upload-schema", response_model=SchemaResponse)
async def upload_schema(
    file: Optional[UploadFile] = File(None),
    body: Optional[SchemaBody] = None
):
    if MOCK_MODE:
        return SchemaResponse(
            domain="healthcare",
            fields=["patient_name", "symptoms", "diagnosis", "icd10_code", "prescription"],
            system_prompt="You are a medical scribe. Extract structured data from the doctor-patient conversation."
        )