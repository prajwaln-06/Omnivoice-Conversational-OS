import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=r"C:\Users\prana\OmniVoice\backend\.env")

import sys, uuid, json, asyncio, subprocess, tempfile, threading
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from concurrent.futures import ThreadPoolExecutor

# ── make existing imports work ──────────────────────────────────────────────
sys.path.append(str(Path(__file__).parent / "backend"))
sys.path.append(str(Path(__file__).parent / "backend" / "whatsapp-mcp" / "whatsapp-mcp-server"))

from ai.asr import SarvamASR
from ai.llm import GroqLLM
from ai.tts import SarvamTTS
from ai.document_generator import generate_with_groq, render_document_to_pdf
from ai.features import (
    analyze_sentiment, translate_to_plain_english,
    schedule_medication_reminders, display_longitudinal_summary, save_patient_visit,
)
try:
    from whatsapp import send_file, send_message
except ImportError:
    send_file = None
    send_message = None

app = FastAPI(title="OmniVoice Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)

# ── In-memory session store ─────────────────────────────────────────────────
SESSIONS: dict = {}

def new_session(mode: str, domain: str) -> str:
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {
        "session_id": sid,
        "mode": mode,
        "domain": domain,
        "status": "running",
        "steps": [],          # list of log strings shown in UI
        "transcript": "",
        "extracted": {},
        "sentiment": {},
        "pdf_path": None,
        "whatsapp_sent": False,
        "error": None,
    }
    return sid

def log(sid: str, msg: str):
    SESSIONS[sid]["steps"].append(msg)
    print(f"[{sid[:8]}] {msg}", flush=True)

# ════════════════════════════════════════════════════════════
#  MODE 1 — PASSIVE
# ════════════════════════════════════════════════════════════

def _run_passive(sid: str, audio_path: str, domain: str, to_number: str):
    """Runs the full passive pipeline in a thread. Writes results into SESSIONS[sid]."""
    try:
        patient_id = to_number.replace("+", "").strip() if to_number else "unknown_patient"

        log(sid, "Checking patient history...")
        display_longitudinal_summary(patient_id, to_number, send_message)

        log(sid, "Reading audio file...")
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        log(sid, "Transcribing with Sarvam ASR...")
        asr = SarvamASR()
        transcript = asr.transcribe(audio_bytes)
        if not transcript:
            transcript = "Doctor, I have a severe headache and a fever of 101 degrees for two days."
            log(sid, "ASR empty — using fallback transcript.")
        else:
            log(sid, f"Transcript ready ({len(transcript)} chars)")

        SESSIONS[sid]["transcript"] = transcript

        log(sid, "Running sentiment analysis...")
        sentiment = analyze_sentiment(transcript, to_number, send_message, alert_threshold=4)
        SESSIONS[sid]["sentiment"] = sentiment if isinstance(sentiment, dict) else {"label": str(sentiment)}

        log(sid, "Extracting structured data with Groq Llama-3.3-70B...")
        try:
            doc_data = generate_with_groq(
                transcript=transcript,
                extracted_data={},
                rag_context="RAG Context: Standard workflow.",
                domain=domain,
                session_id=sid,
            )
        except Exception as e:
            log(sid, f"Groq error: {e} — using fallback")
            doc_data = {
                "patient_name": "Demo Patient", "age": "34",
                "symptoms": ["headache", "fever 101"], "duration": "2 days",
                "prescription": "Paracetamol 500mg twice daily",
                "medications": [{"name": "Paracetamol", "dosage": "500mg",
                                  "frequency": "every 6 hours", "duration": "3 days"}],
                "follow_up": "3 days",
            }

        SESSIONS[sid]["extracted"] = doc_data

        from ai.medical_apis import enrich_medications_with_rxnorm, enrich_with_icd10
        
        if domain == 'healthcare':
            log(sid, 'Validating medications with RxNorm (NIH)...')
            meds = doc_data.get('medications', [])
            if meds:
                rxnorm_data = enrich_medications_with_rxnorm(meds)
                SESSIONS[sid]['rxnorm'] = rxnorm_data
                if rxnorm_data.get('has_severe_interactions'):
                    log(sid, '⚠️ SEVERE drug interaction detected!')
                else:
                    log(sid, f'RxNorm: {len(meds)} drugs validated ✓')
        
            log(sid, 'Inferring ICD-10 codes...')
            icd_codes = enrich_with_icd10(doc_data)
            SESSIONS[sid]['icd10'] = icd_codes
            doc_data['icd10_codes'] = icd_codes
            log(sid, f'ICD-10: {len(icd_codes)} codes inferred ✓')

        log(sid, "Translating to plain English...")
        translate_to_plain_english(doc_data, transcript, to_number, send_message)

        log(sid, "Rendering PDF...")
        pdf_bytes = render_document_to_pdf(doc_data, domain)
        pdf_dir = Path(__file__).parent / "output_pdfs"
        pdf_dir.mkdir(exist_ok=True)
        pdf_path = str(pdf_dir / f"{sid}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        SESSIONS[sid]["pdf_path"] = pdf_path
        log(sid, f"PDF saved: {pdf_path}")

        if to_number and send_message and send_file:
            log(sid, f"Sending PDF to WhatsApp {to_number}...")
            send_message(to_number, f"OmniVoice {domain.capitalize()} Summary. Session: {sid}")
            send_file(to_number, pdf_path)
            SESSIONS[sid]["whatsapp_sent"] = True
            log(sid, "WhatsApp sent ✓")
        else:
            log(sid, "WhatsApp skipped (no number or MCP unavailable)")

        log(sid, "Saving patient visit record...")
        save_patient_visit(patient_id, doc_data, sid, SESSIONS[sid]["sentiment"])

        if domain == "healthcare" and doc_data.get("medications"):
            log(sid, "Scheduling medication reminders (demo mode)...")
            schedule_medication_reminders(
                doc_data=doc_data,
                to_number=to_number,
                send_message_fn=send_message,
                demo_mode=True,
                max_reminders=3,
            )

        SESSIONS[sid]["status"] = "done"
        log(sid, "✅ Passive pipeline complete!")

    except Exception as e:
        SESSIONS[sid]["status"] = "error"
        SESSIONS[sid]["error"] = str(e)
        log(sid, f"❌ Pipeline error: {e}")


@app.post("/passive/run")
async def passive_run(
    audio: UploadFile = File(...),
    domain: str = Form("healthcare"),
    to_number: str = Form(""),
):
    sid = new_session("passive", domain)
    
    # Save uploaded audio to temp file
    suffix = Path(audio.filename).suffix or ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(await audio.read())
    tmp.close()
    
    # Run pipeline in background thread (non-blocking)
    thread = threading.Thread(
        target=_run_passive,
        args=(sid, tmp.name, domain, to_number),
        daemon=True,
    )
    thread.start()
    
    return {"session_id": sid, "status": "started"}


@app.get("/passive/status/{sid}")
def passive_status(sid: str):
    if sid not in SESSIONS:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return SESSIONS[sid]


@app.get("/passive/pdf/{sid}")
def passive_pdf(sid: str):
    session = SESSIONS.get(sid)
    if not session or not session.get("pdf_path"):
        return JSONResponse(status_code=404, content={"error": "PDF not ready"})
    return FileResponse(session["pdf_path"], media_type="application/pdf", filename=f"omnivoice_{sid[:8]}.pdf")


# ════════════════════════════════════════════════════════════
#  MODE 2 — UNIFIED AGENT (Live conversational)
# ════════════════════════════════════════════════════════════

AGENT_PROCESSES: dict = {}

@app.post("/agent/start")
def agent_start(domain: str = Form("healthcare"), to_number: str = Form("")):
    sid = new_session("agent", domain)
    log(sid, f"Starting unified agent — domain: {domain}")
    
    # Launch unified_agent.py as a subprocess
    # It writes its own output to terminal; we track status via SESSIONS
    env = os.environ.copy()
    env["OMNIVOICE_WHATSAPP_TO"] = to_number
    env["OMNIVOICE_SESSION_ID"] = sid
    env["OMNIVOICE_DOMAIN"] = domain
    env["PYTHONIOENCODING"] = "utf-8"
    
    proc = subprocess.Popen(
        [sys.executable, "unified_agent.py"],
        env=env,
        cwd=str(Path(__file__).parent / "backend"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    AGENT_PROCESSES[sid] = proc
    
    # Thread to stream stdout into SESSIONS[sid]["steps"]
    def _stream_logs():
        for line in proc.stdout:
            line = line.strip()
            if line:
                SESSIONS[sid]["steps"].append(line)
        proc.wait()
        
        if proc.returncode == 0:
            for step in SESSIONS[sid]["steps"]:
                if "PDF saved locally at:" in step:
                    SESSIONS[sid]["pdf_path"] = step.split("PDF saved locally at:")[-1].strip()
                if "WhatsApp Status" in step or "WhatsApp sent" in step:
                    SESSIONS[sid]["whatsapp_sent"] = True
                if "[JSON_DATA]" in step:
                    try:
                        data = json.loads(step.split("[JSON_DATA]")[-1].strip())
                        SESSIONS[sid]["extracted"] = data
                    except:
                        pass
            SESSIONS[sid]["status"] = "done"
        else:
            SESSIONS[sid]["status"] = "stopped"
    
    threading.Thread(target=_stream_logs, daemon=True).start()
    SESSIONS[sid]["status"] = "running"
    return {"session_id": sid, "status": "started"}


@app.post("/agent/end/{sid}")
def agent_end(sid: str):
    proc = AGENT_PROCESSES.get(sid)
    if proc and proc.poll() is None:
        proc.terminate()
        log(sid, "Agent terminated by user.")
    SESSIONS[sid]["status"] = "stopped"
    return {"status": "stopped"}


@app.get("/agent/status/{sid}")
def agent_status(sid: str):
    if sid not in SESSIONS:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return SESSIONS[sid]


@app.get("/health")
def health():
    return {"status": "ok", "service": "OmniVoice Engine API"}

@app.post("/feedback")
def submit_feedback(payload: dict):
    import json
    from pathlib import Path
    from datetime import datetime
    record = {
        **payload,
        'timestamp': datetime.utcnow().isoformat()
    }
    path = Path('feedback_logs.jsonl')
    with open(path, 'a') as f:
        f.write(json.dumps(record) + '\n')
    print(f'[Feedback] Session {payload.get("session_id", "")[:8]} rated {payload.get("rating")}/5')
    return {'status': 'ok'}
