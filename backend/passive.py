import argparse
import os
import sys
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Make whatsapp bridge wrapper importable
sys.path.append(os.path.join(os.path.dirname(__file__), "whatsapp-mcp", "whatsapp-mcp-server"))
try:
    from whatsapp import send_file, send_message
except ImportError:
    print("⚠️ WhatsApp MCP not found or failed to load. WhatsApp sending will be skipped.")
    send_file = None
    send_message = None

from ai.asr import SarvamASR
from ai.document_generator import generate_with_groq, render_document_to_pdf

def log_step(message: str):
    print(f"[\033[96mOmniVoice Passive\033[0m] {message}", flush=True)

def run_passive_pipeline(audio_path: str, domain: str, to_number: str):
    print("="*60)
    print(" 🎧 OMNIVOICE ENGINE - PASSIVE LISTENER MODE (TERMINAL DEMO) ")
    print("="*60)

    session_id = str(uuid.uuid4())
    log_step(f"Session ID initialized: {session_id}")
    log_step(f"Domain: {domain.upper()}")

    # 1. Read Audio File
    if not os.path.exists(audio_path):
        print(f"❌ Error: Audio file '{audio_path}' not found.")
        sys.exit(1)
        
    log_step(f"Reading audio file: {audio_path}")
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    # 2. Transcribe via Sarvam ASR
    log_step("Sending bytes to Sarvam ASR...")
    asr = SarvamASR()
    transcript = asr.transcribe(audio_bytes)
    
    if not transcript:
        print("❌ Error: Transcription failed or returned empty.")
        sys.exit(1)
        
    print(f"\n\033[92m[TRANSCRIPT]\033[0m\n{transcript}\n")

    # 3. Extract & Format via Groq LPU
    log_step("Sending transcript to Groq Lllama-3.3-70B for extraction...")
    # Passing empty extracted_data and dummy rag_context as this is a single-pass processing
    doc_data = generate_with_groq(
        transcript=transcript,
        extracted_data={}, 
        rag_context="RAG Context: Standard workflow.",
        domain=domain,
        session_id=session_id
    )
    print(f"\n\033[93m[EXTRACTED JSON]\033[0m\n{doc_data}\n")

    # 4. Render PDF
    log_step("Rendering PDF via ReportLab...")
    pdf_bytes = render_document_to_pdf(doc_data)
    
    # Save PDF locally so MCP can send it
    os.makedirs("output_pdfs", exist_ok=True)
    pdf_path = os.path.abspath(f"output_pdfs/{session_id}.pdf")
    
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    log_step(f"PDF saved locally to: {pdf_path}")

    # 5. Send to WhatsApp via MCP
    if to_number and send_message and send_file:
        log_step(f"Triggering WhatsApp MCP to {to_number}...")
        caption = f"OmniVoice {domain.capitalize()} Summary.\nSession: {session_id}"
        
        try:
            send_message(to=to_number, text=caption)
            send_file(to=to_number, file_path=pdf_path)
            log_step("✅ WhatsApp messages dispatched successfully!")
        except Exception as e:
            print(f"❌ WhatsApp sending failed: {e}")
    else:
        log_step("WhatsApp sending skipped (no number provided or MCP unavailable).")

    print("\n" + "="*60)
    print(" ✅ PASSIVE LISTENER WORKFLOW COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OmniVoice Passive Listener")
    parser.add_argument("--audio", required=True, help="Path to the pre-recorded .wav file")
    parser.add_argument("--domain", default="healthcare", help="Domain to process (e.g., healthcare, banking)")
    parser.add_argument("--to", help="WhatsApp number to send the PDF to (e.g., +919876543210)", default=os.getenv("OMNIVOICE_WHATSAPP_TO"))
    
    args = parser.parse_args()
    
    if not args.to:
        print("⚠️ Warning: No WhatsApp number provided. Pass --to +91xxxxxxxxxx to send the PDF.")

    run_passive_pipeline(args.audio, args.domain, args.to)