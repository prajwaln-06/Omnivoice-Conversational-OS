from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routes import schema, transcribe, analyze, approve, session

app = FastAPI(title="OmniVoice API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schema.router,     prefix="/api")
app.include_router(transcribe.router, prefix="/api")
app.include_router(analyze.router,    prefix="/api")
app.include_router(approve.router,    prefix="/api")
app.include_router(session.router,    prefix="/api")

@app.get("/")
def root():
    return {"status": "OmniVoice API is live"}