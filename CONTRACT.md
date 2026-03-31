# OMNIVOICE ENGINE — COMPLETE PROJECT CONTEXT
# Team Penguins | Hack'A'War Hackathon | April 2026
# Paste this at the start of any new conversation to resume work.

═══════════════════════════════════════════════════════
## 1. WHO WE ARE
═══════════════════════════════════════════════════════

Team: Team Penguins
College: M.S. Ramaiah Institute of Technology (MSRIT)
Department: CSE (AI & ML)
Hackathon: Hack'A'War — Track 3: Voice AI — Build for Bharat (3.5)
Status: SHORTLISTED ✅

Team Members:
- Pranav R Mane — AI/ML & NLP Lead
- Prajwal N — Backend & Real-Time Infrastructure
- Dakshita S — Frontend & UI/UX
- Sinchana Jeppu — RAG & Document Pipeline

═══════════════════════════════════════════════════════
## 2. WHAT WE ARE BUILDING
═══════════════════════════════════════════════════════

Product: OmniVoice Engine
Tagline: Domain-Agnostic Conversational OS for Bharat
One-line problem: Every professional conversation in India 
(doctor, banker, lawyer) ends with someone manually writing 
everything down. OmniVoice eliminates that entirely.

Core differentiator:
- Handles Kannada-Hindi-English code-mixed speech natively
- Goes from spoken conversation → structured JSON → 
  enterprise action automatically
- Schema-driven: drop one JSON file = new domain, zero code changes
- Sub-800ms end-to-end latency via Groq LPU

═══════════════════════════════════════════════════════
## 3. THE DEMO FLOW (WHAT WE SHOW JUDGES)
═══════════════════════════════════════════════════════

Step 1: React UI shows a schema drop zone
Step 2: Drop healthcare_schema.json → UI transforms into 
        healthcare assistant with two mode cards
Step 3: MODE 1 (Conversational VoiceBot)
        - User speaks Kannada-English code-mix 
          (e.g. "Doctor naanu fever iddene, 101 temperature")
        - Live transcript appears
        - Groq asks intelligent follow-up questions via TTS
        - Session ends → structured JSON extracted
        - Doctor clicks Approve → PDF generated → 
          sent to WhatsApp via MCP
Step 4: MODE 2 (Silent Listener)
        - Upload pre-recorded doctor-patient audio
        - System transcribes + extracts prescription automatically
        - Editable ApprovalCard appears
        - Doctor approves → PDF sent to patient WhatsApp via MCP
Step 5: Drop banking_schema.json → show fintech version briefly
Step 6: Close with "One JSON file. Any domain. That's the OS."

Total demo time: 6 minutes

═══════════════════════════════════════════════════════
## 4. TECH STACK
═══════════════════════════════════════════════════════

Frontend:   React 18 (Vite), Tailwind CSS v3, Framer Motion v11,
            MediaRecorder API
Backend:    FastAPI (Python 3.11+), Motor (async MongoDB),
            boto3 (AWS)
AI/ML:      Sarvam Saaras v3 ASR (primary),
            OpenAI Whisper (fallback),
            Groq Llama 3.3 70B (inference),
            ChromaDB (local RAG),
            sentence-transformers all-MiniLM-L6-v2
Database:   MongoDB Atlas
AWS:        S3 (audio + PDF storage, AES256 SSE),
            CloudFront (PDF delivery CDN),
            DynamoDB (schema metadata cache),
            Lambda (optional event triggers)
Agentic:    WhatsApp MCP (for message delivery — 
            NOT Twilio, handled externally by Pranav)
Docs/PDF:   ReportLab, BytesIO

═══════════════════════════════════════════════════════
## 5. THE MASTER DATA CONTRACT
═══════════════════════════════════════════════════════

This is the single shared object everyone's code touches.
DO NOT deviate from this shape:

{
  "session_id": "uuid-v4-string",
  "domain": "healthcare | banking",
  "mode": "conversational | silent",
  "transcript": "string",
  "extracted_data": {
    // fields vary by domain schema
    // healthcare example:
    "patient_name": "string",
    "age": "string",
    "symptoms": ["array", "of", "strings"],
    "duration": "string",
    "fever_temp": "string",
    "prescription": "string",
    "follow_up": "string"
  },
  "status": "pending_approval | approved | sent",
  "audio_s3_url": "string",
  "pdf_url": "https://DIST.cloudfront.net/prescriptions/id.pdf",
  "whatsapp_sent": false,
  "created_at": "ISO datetime string"
}

═══════════════════════════════════════════════════════
## 6. API CONTRACT (5 ENDPOINTS)
═══════════════════════════════════════════════════════

POST /api/upload-schema
  In:  JSON schema file
  Out: { domain, fields, system_prompt }

POST /api/transcribe
  In:  multipart { audio: file, domain: str, mode: str }
  Out: { session_id, transcript, language, audio_s3_url }
  language values: "kn-IN" | "hi-IN" | "en-IN" | "mixed"

POST /api/analyze
  In:  { session_id, domain }
  Out: { session_id, extracted_data }

POST /api/approve
  In:  { session_id, extracted_data }
  Out: { pdf_url, whatsapp_sent: true }
  Note: WhatsApp sent via MCP externally, not in this route

GET /api/session/{session_id}
  Out: full session document

═══════════════════════════════════════════════════════
## 7. FOLDER STRUCTURE
═══════════════════════════════════════════════════════

omnivoice-engine/
├── backend/
│   ├── main.py
│   ├── .env
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   ├── transcribe.py
│   │   ├── analyze.py
│   │   ├── approve.py
│   │   └── session.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── asr.py          ← Pranav
│   │   ├── llm.py          ← Pranav
│   │   └── rag.py          ← Pranav
│   ├── rag_pipeline/
│   │   ├── __init__.py
│   │   ├── pdf_generator.py ← Sinchana
│   │   ├── schemas/
│   │   │   ├── healthcare_schema.json ← Sinchana
│   │   │   └── banking_schema.json    ← Sinchana
│   │   ├── symptoms_db.txt  ← Sinchana
│   │   └── loan_products.txt ← Sinchana
│   └── aws/
│       ├── __init__.py
│       └── s3_handler.py   ← Prajwal
└── frontend/
    └── src/
        ├── App.jsx
        ├── api/
        │   └── client.js
        └── components/
            ├── SchemaDropper.jsx
            ├── ModeSelector.jsx
            ├── ConversationUI.jsx
            ├── SilentListener.jsx
            └── ApprovalCard.jsx

═══════════════════════════════════════════════════════
## 8. MODULE INTERFACES (EXACT FUNCTION SIGNATURES)
═══════════════════════════════════════════════════════

# ai/asr.py
async def transcribe(audio_bytes: bytes) -> dict:
    # returns:
    # { "transcript": str, "language": str, "source": "sarvam|whisper" }
    # Primary: Sarvam Saaras v3
    # Fallback: OpenAI Whisper
    # language normalized to: kn-IN, hi-IN, en-IN, mixed

# ai/llm.py
async def analyze(
    transcript: str,
    domain: str,
    schema_fields: list,
    rag_context: str
) -> dict:
    # returns extracted_data dict
    # ONLY fields present in schema_fields
    # null for unknown values, never invented values
    # uses Groq llama-3.3-70b-versatile
    # forces JSON output, no markdown

# ai/rag.py
async def get_context(query: str, domain: str) -> str:
    # returns "RELEVANT CONTEXT:\n• chunk1\n• chunk2"
    # returns "" on any failure (silent fail)
    # ChromaDB persistent at ./chroma_db/{domain}

# rag_pipeline/pdf_generator.py
def generate_prescription_pdf(session_data: dict) -> bytes:
    # returns PDF as bytes via BytesIO
    # NEVER writes to disk
    # session_data shape = master data contract above

═══════════════════════════════════════════════════════
## 9. DESIGN SYSTEM
═══════════════════════════════════════════════════════

Theme: Deep Space / Hacker Terminal

Colors:
  Background:    #020617 (deepest navy)
  Card surface:  #0f172a
  Card border:   1px solid rgba(34,211,238,0.2)
  Glassmorphism: backdrop-blur-md bg-white/5
  Cyan (primary): #22d3ee
  Emerald (success): #10b981
  Amber (processing): #f59e0b
  Pink (accent): #f472b6
  Error: #ef4444

Fonts:
  JetBrains Mono — JSON/code display, schema fields
  Plus Jakarta Sans — headers, body text

Framer Motion pattern:
  variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  }
  transition: { duration: 0.4, ease: "easeOut" }

═══════════════════════════════════════════════════════
## 10. SCHEMA FILE SHAPES
═══════════════════════════════════════════════════════

Both schema files follow this structure:
{
  "domain": "healthcare | banking",
  "display_name": "string",
  "icon": "emoji",
  "color": "#hex",
  "fields": [
    {
      "name": "snake_case_field_name",
      "type": "string | array",
      "label": "Human Readable Label",
      "required": true | false
    }
  ],
  "system_prompt": "LLM instruction string",
  "whatsapp_template": "Message with {field_name} placeholders",
  "rag_documents": ["filename.txt"]
}

Healthcare fields:
  patient_name, age, symptoms (array), duration,
  fever_temp, prescription, follow_up

Banking fields:
  customer_name, loan_type, loan_amount, monthly_income,
  tenure_years, emi_estimate, employment_type, action_required

═══════════════════════════════════════════════════════
## 11. AWS CONFIGURATION
═══════════════════════════════════════════════════════

Bucket: omnivoice-demo
Region: ap-south-1 (Mumbai)
Encryption: AES256 SSE on ALL uploads
Audio key pattern: audio/{session_id}.wav
PDF key pattern: prescriptions/{session_id}.pdf
CloudFront URL: https://{CF_DOMAIN}/prescriptions/{id}.pdf

AWS services in use:
  S3 — audio storage + PDF storage
  CloudFront — PDF delivery CDN
  DynamoDB — schema metadata cache
  Lambda — optional event triggers

═══════════════════════════════════════════════════════
## 12. ENVIRONMENT VARIABLES
═══════════════════════════════════════════════════════

# AI Keys (Pranav)
SARVAM_API_KEY=
GROQ_API_KEY=
OPENAI_API_KEY=

# AWS (Prajwal)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-south-1
S3_BUCKET=omnivoice-demo
CF_DOMAIN=

# Database (Prajwal)
MONGODB_URI=

# WhatsApp MCP handled externally by Pranav
# No Twilio keys needed

═══════════════════════════════════════════════════════
## 13. WHAT IS DONE vs WHAT IS PENDING
═══════════════════════════════════════════════════════

DONE:
✅ Full project architecture decided
✅ Master data contract finalized
✅ API contracts finalized
✅ Folder structure decided
✅ All 4 agent prompts written and refined
✅ Demo flow scripted (6 minutes)
✅ Judge Q&A prepared
✅ Design system decided

PENDING (build tomorrow):
⬜ asr.py (Pranav)
⬜ llm.py (Pranav)
⬜ rag.py (Pranav)
⬜ main.py + all routes mock-first (Prajwal)
⬜ s3_handler.py (Prajwal)
⬜ Real route implementations (Prajwal)
⬜ api/client.js (Dakshita)
⬜ SchemaDropper.jsx (Dakshita)
⬜ ModeSelector.jsx (Dakshita)
⬜ ConversationUI.jsx (Dakshita)
⬜ SilentListener.jsx (Dakshita)
⬜ ApprovalCard.jsx (Dakshita)
⬜ healthcare_schema.json (Sinchana)
⬜ banking_schema.json (Sinchana)
⬜ symptoms_db.txt (Sinchana)
⬜ loan_products.txt (Sinchana)
⬜ pdf_generator.py (Sinchana)
⬜ rag.py vector store (Sinchana)
⬜ demo_audio_script.txt + recording (Sinchana)
⬜ WhatsApp MCP integration (Pranav)

═══════════════════════════════════════════════════════
## 14. CRITICAL RULES (NEVER VIOLATE THESE)
═══════════════════════════════════════════════════════

1. Master data contract shape never changes without 
   telling all 4 members
2. Prajwal's mock server must be up by Hour 4
3. Each module is independently testable from terminal
4. If anything takes >90 mins — hardcode it and move on
5. pdf_generator always returns bytes, never writes to disk
6. rag.py never crashes — returns "" on any failure
7. llm.py never invents fields outside schema_fields
8. All AWS uploads include ServerSideEncryption='AES256'
9. MOCK_MODE=true in frontend until backend confirmed working
10. No Twilio — WhatsApp via MCP only

═══════════════════════════════════════════════════════
## 15. INTEGRATION CHECKPOINTS
═══════════════════════════════════════════════════════

Hour 8 checkpoint — verify all of these:
□ asr.py returns correct dict from terminal
□ llm.py returns correct dict from terminal
□ Mock server up, all 5 endpoints responding
□ SchemaDropper renders and parses JSON
□ healthcare_schema.json + banking_schema.json committed

Hour 16 checkpoint — full demo run:
□ Drop schema → UI transforms
□ Mode 1: speak → transcript → JSON extracted
□ Mode 1: approve → PDF generated → WhatsApp fires
□ Mode 2: upload audio → prescription extracted
□ Mode 2: approve → PDF sent

═══════════════════════════════════════════════════════
## 16. THE WINNING ARGUMENT (memorize this)
═══════════════════════════════════════════════════════

Problem:     "Professional conversations in India end 
              with manual paperwork. We end that."

Differentiator: "We don't output text. 
                 We output completed workflows."

Schema pitch: "One JSON file IS the entire domain. 
               Drop healthcare — it's a medical assistant.
               Drop banking — it's a loan officer.
               Zero code changes. That's the OS."

AWS answer:  "S3 for secure storage, CloudFront for 
              pan-India delivery, DynamoDB for schema 
              caching, Lambda for event triggers. 
              AWS is the infrastructure backbone."

Code-mix answer: "Try Whisper on 'naanu ek loan 
                  tegeyo bardide.' It fails. 
                  Sarvam doesn't. That's our moat."

═══════════════════════════════════════════════════════
## 17. INDIVIDUAL AGENT PROMPTS
═══════════════════════════════════════════════════════

If you need the full agent prompt for a specific member,
ask: "Give me [MEMBER NAME]'s agent prompt"

Members: Pranav, Prajwal, Dakshita, Sinchana

═══════════════════════════════════════════════════════

CURRENT STATUS: Ready to build. 
NEXT ACTION: Each member opens their agent, 
             pastes their prompt, and starts coding.

If continuing from a previous conversation, 
tell the new agent:
"We have completed planning. Now help me build 
[SPECIFIC FILE]. Here is the full project context above."