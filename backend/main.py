# backend/main.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from routes.schema import router as schema_router
from routes.transcribe import router as transcribe_router
from routes.analyze import router as analyze_router
from routes.approve import router as approve_router
from routes.session import router as session_router
from routes.postcall import router as postcall_router

app = FastAPI(
    title="OmniVoice Engine API",
    description="Domain-Agnostic Conversational OS for Bharat",
    version="1.0.0"
)

# CORS — allow everything for hackathon
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(schema_router, prefix="/api", tags=["Schema"])
app.include_router(transcribe_router, prefix="/api", tags=["Transcribe"])
app.include_router(analyze_router, prefix="/api", tags=["Analyze"])
app.include_router(approve_router, prefix="/api", tags=["Approve"])
app.include_router(session_router, prefix="/api", tags=["Session"])
app.include_router(postcall_router, prefix="/api", tags=["PostCall"])

@app.get("/")
async def root():
    return {
        "status": "OmniVoice Engine running",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/upload-schema",
            "POST /api/transcribe",
            "POST /api/passive-listen",
            "POST /api/analyze",
            "POST /api/approve",
            "GET  /api/session/{id}",
            "POST /api/postcall/analyze",
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}