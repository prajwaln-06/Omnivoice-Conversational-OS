# OmniVoice Engine
**A Domain-Agnostic, Dual-Mode Conversational OS for Bharat.**

OmniVoice eliminates manual paperwork in Indian enterprises (healthcare, banking) by turning complex, code-mixed conversations into structured JSON and actionable workflows in under 800ms.

Built by **Team Penguins** for the Hack'A'War Hackathon.

## Key Features
* **Natively Code-Mixed:** Powered by Sarvam ASR, it flawlessly understands Kannada-Hindi-English mixed speech (e.g., *"Doctor naanu fever iddene, 101 temperature"*).
* **Domain-Agnostic OS:** Drop a JSON schema (e.g., `healthcare_schema.json`) into the UI, and the entire app instantly morphs into a medical assistant. Drop a banking schema, it becomes a loan officer. Zero code changes required.
* **Dual-Mode Intelligence:**
  * **Mode 1 (Conversational Agent):** Active AI Assistant that dynamically prompts for symptoms and interactions.
  * **Mode 2 (Ambient Copilot):** Passive listener that processes uploaded consultation audio.
* **Agentic Workflows:** Automatically extracts data, generates a PDF receipt, and securely makes actions via MCP.

---

## Tech Stack
* **Frontend:** React 18, Next.js, Tailwind CSS
* **Backend:** FastAPI (Python 3.11+)
* **AI/ML:** Sarvam Saaras v3 (ASR & TTS), Groq Llama 3.3 70B (Extraction), ChromaDB (Local RAG)

---

## Initialization & Local Setup

### 1. Prerequisites
Ensure you have the following installed on your local machine:
* **Python 3.10+**
* **Node.js 18+**
* **Git**

### 2. Environment Variables
You need to configure the environment variables for both the backend and frontend.

**Backend Setup:**
1. Navigate to the `backend/` directory.
2. Copy the example environment file: `cp .env.example .env` (or create a `.env` manually)
3. Fill in your keys in `backend/.env`:
```env
SARVAM_API_KEY=your_sarvam_key
GROQ_API_KEY=your_groq_key
```

**Frontend Setup:**
1. Navigate to the `frontend/` directory.
2. Create a `.env` file (you can copy `.env.example` if it exists).
3. Open `frontend/.env` and ensure the internal variables are set:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Running the Application

There are bundled PowerShell scripts in the root of the project that handle installing all dependencies and starting both servers concurrently.

### Step-by-Step Execution (Easiest Method):

1. Open a PowerShell terminal and navigate to the project root:
   ```powershell
   cd OmniVoice
   ```

2. Run the full stack starter script:
   ```powershell
   ./run_full_stack.ps1
   ```
   *What this script does:*
   - Automatically installs frontend dependencies using `npm install`.
   - Automatically installs backend dependencies using `pip install -r requirements.txt`.
   - Opens two new PowerShell windows: one running the FastAPI backend on port `8000` and the other running the React frontend on port `5173`/`3000`.

3. Access the application:
   - **Frontend UI:** Open your browser and go to http://localhost:5173
   - **Backend API Docs:** Go to http://localhost:8000/docs to view the interactive FastAPI swagger documentation.

### Manual Execution (Alternative)

If you prefer to start the servers manually without the script, follow these steps:

**Terminal 1 — Backend:**
```bash
cd backend
python -m pip install -r requirements.txt
# Run the FastAPI server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
# Run the development server
npm run dev
```

---

## Testing the Application

1. Open the UI at `http://localhost:5173`.
2. Use the **Dashboard** or UI settings to provide the domain format (e.g. HealthCare).
3. Choose either **Passive Context** to analyze existing audio files or **Agent Interaction** to talk dynamically with the system.
4. Check the terminal outputs in your running script windows for detailed real-time logs (ASR transcripts, latency metrics, and API validations).
