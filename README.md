# OmniVoice
OmniVoice is a Dual-Mode Conversational OS for Bharat. It handles code-mixed Indian speech (Kannada-English) using Sarvam ASR and Groq Llama 3.3 to turn conversations into structured data in &lt;800ms. Featuring Autonomous Agent and Ambient Copilot modes, it automates enterprise workflows via MCP.

## Quick Integrated Run

1. Copy `frontend/.env.example` to `frontend/.env`.
2. From project root, run `./run_full_stack.ps1`.
3. Open `http://localhost:5173` for UI and `http://localhost:8000/docs` for API.

## Integration Notes

- Frontend API base URL is controlled by `VITE_API_BASE_URL`.
- Frontend mock mode is controlled by `VITE_MOCK_MODE`.
- Schema selection/upload in the dashboard is sent to backend before mode selection so `/api/analyze` can use the loaded schema.
