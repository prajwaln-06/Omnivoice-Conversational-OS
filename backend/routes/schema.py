import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()

_SCHEMA_STORE: Dict[str, Dict[str, Any]] = {}


class SchemaBody(BaseModel):
    domain: str = Field(..., description="Domain name such as healthcare or banking")
    schema_payload: Dict[str, Any] = Field(..., alias="schema")


class SchemaResponse(BaseModel):
    domain: str
    fields: List[str]
    system_prompt: str


def get_schema(domain: str) -> Optional[Dict[str, Any]]:
    return _SCHEMA_STORE.get(domain)


def _extract_fields(schema: Dict[str, Any]) -> List[str]:
    props = schema.get("properties", {})
    if isinstance(props, dict) and props:
        return list(props.keys())

    fields = schema.get("fields", [])
    if isinstance(fields, list):
        return [str(f) for f in fields]

    return []


@router.post("/upload-schema", response_model=SchemaResponse)
async def upload_schema(
    request: Request,
    file: Optional[UploadFile] = File(None),
):
    try:
        if file is not None:
            payload = await file.read()
            loaded = json.loads(payload.decode("utf-8"))
            domain = loaded.get("domain")
            schema = loaded.get("schema") or loaded
        else:
            body_dict = await request.json()
            body = SchemaBody.model_validate(body_dict)
            domain = body.domain
            schema = body.schema_payload

        if not domain or not isinstance(schema, dict):
            raise HTTPException(status_code=400, detail="Invalid schema payload")

        fields = _extract_fields(schema)
        system_prompt = schema.get("system_prompt") or (
            f"You are a structured extractor for {domain}. Return only valid JSON."
        )

        _SCHEMA_STORE[domain] = {
            "domain": domain,
            "fields": fields,
            "system_prompt": system_prompt,
            "schema": schema,
        }

        return SchemaResponse(domain=domain, fields=fields, system_prompt=system_prompt)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to upload schema")
        raise HTTPException(status_code=500, detail=f"Schema upload failed: {exc}")