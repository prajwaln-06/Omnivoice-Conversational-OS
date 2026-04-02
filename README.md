#  OmniVoice Engine
**A Domain-Agnostic, Dual-Mode Conversational OS for Bharat.**

OmniVoice eliminates manual paperwork in Indian enterprises (healthcare, banking) by turning complex, code-mixed conversations into structured JSON and actionable workflows in under 800ms. 

Built by **Team Penguins** for the Hack'A'War Hackathon.

##  Key Features
* **Natively Code-Mixed:** Powered by Sarvam ASR, it flawlessly understands Kannada-Hindi-English mixed speech (e.g., *"Doctor naanu fever iddene, 101 temperature"*).
* **Domain-Agnostic OS:** Drop a JSON schema (e.g., `healthcare_schema.json`) into the UI, and the entire app instantly morphs into a medical assistant. Drop a banking schema, it becomes a loan officer. Zero code changes required.
* **Dual-Mode Intelligence:**
  * **Mode 1 (Conversational):** Active VoiceBot that asks intelligent follow-up questions.
  * **Mode 2 (Ambient Copilot):** Passive listener that processes uploaded consultation audio.
* **Agentic Workflows:** Automatically extracts data, generates a PDF receipt via Claude/ReportLab, and securely routes it to the patient via WhatsApp MCP.

---

## Tech Stack
* **Frontend:** React 18 (Vite), Tailwind CSS v3, Framer Motion
* **Backend:** FastAPI (Python 3.11+), Async MongoDB (Motor)
* **AI/ML:** Sarvam Saaras v3 (ASR), Groq Llama 3.3 70B (Extraction), ChromaDB (Local RAG)
* **Cloud & Storage:** AWS S3 (AES256 Encrypted), CloudFront (CDN)

---

## Initialization & Local Setup

### 1. Prerequisites
Ensure you have the following installed on your local machine:
* **Python 3.11+**
* **Node.js 18+**
* **Git**

### 2. Environment Variables
You need to configure the environment variables for both the backend and frontend.

**Backend Setup:**
1. Navigate to the `backend/` directory.
2. Copy the example environment file: `cp .env.example .env`
3. Fill in your keys in `backend/.env`:
```env
SARVAM_API_KEY=your_sarvam_key
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
MONGODB_URI=your_mongo_connection_string
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=ap-south-1
S3_BUCKET=omnivoice-demo
CF_DOMAIN=your_cloudfront_domain
