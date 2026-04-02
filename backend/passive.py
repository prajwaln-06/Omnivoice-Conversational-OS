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

# ── Feature Pack 1 ──────────────────────────────────────────────────────────
from ai.features import (
    schedule_medication_reminders,
    translate_to_plain_english,
    analyze_sentiment,
    display_longitudinal_summary,
    save_patient_visit,
)

def log_step(message: str):
    print(f"[\033[96mOmniVoice Passive\033[0m] {message}", flush=True)

def run_passive_pipeline(audio_path: str, domain: str, to_number: str):
    print("="*60)
    print(" 🎧 OMNIVOICE ENGINE - PASSIVE LISTENER MODE (TERMINAL DEMO) ")
    print("="*60)

    session_id = str(uuid.uuid4())
    log_step(f"Session ID initialized: {session_id}")
    log_step(f"Domain: {domain.upper()}")

    # ── Patient ID (derived from WhatsApp number for longitudinal tracking) ──
    patient_id = to_number.replace("+", "").strip() if to_number else "unknown_patient"

    # ── FEATURE 4 (PRE-VISIT): Show history if returning patient ────────────
    log_step("Checking patient history...")
    is_returning = display_longitudinal_summary(patient_id, to_number, send_message)
    if is_returning:
        log_step("Returning patient detected. History displayed above.")
    else:
        log_step("New patient — no prior records.")

    # 1. Read Audio File
    if not os.path.exists(audio_path):
        print(f"Error: Audio file '{audio_path}' not found.")
        sys.exit(1)

    log_step(f"Reading audio file: {audio_path}")
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    # 2. Transcribe via Sarvam ASR
    log_step("Sending bytes to Sarvam ASR...")
    asr = SarvamASR()
    transcript = asr.transcribe(audio_bytes)

    if not transcript:
        log_step("Sarvam returned empty transcript. Falling back to Local Demo Cache...")
        transcript = "Doctor, I have a severe headache and a fever of 101 degrees for two days."

    print(f"\n\033[92m[TRANSCRIPT]\033[0m\n{transcript}\n")

    # ── FEATURE 3: Sentiment Analysis ───────────────────────────────────────
    log_step("Running sentiment analysis on transcript...")
    sentiment = analyze_sentiment(transcript, to_number, send_message, alert_threshold=4)

    # 3. Extract & Format via Groq LPU
    log_step("Sending transcript to Groq Llama-3.3-70B for extraction...")
    try:
        doc_data = generate_with_groq(
            transcript=transcript,
            extracted_data={},
            rag_context="RAG Context: Standard workflow.",
            domain=domain,
            session_id=session_id
        )
    except Exception as e:
        log_step(f"Groq API Error ({e}). Using Local Failsafe Cache...")
        doc_data = {
            "patient_name": "Demo Patient",
            "age": "34",
            "symptoms": ["headache", "fever 101"],
            "duration": "2 days",
            "prescription": "Paracetamol 500mg twice daily",
            "medications": [
                {"name": "Paracetamol", "dosage": "500mg",
                 "frequency": "every 6 hours", "duration": "3 days"}
            ],
            "follow_up": "3 days"
        }

    print(f"\n\033[93m[EXTRACTED JSON]\033[0m\n{doc_data}\n")

    # ── FEATURE 2: Plain English Translator ─────────────────────────────────
    log_step("Translating to plain English for patient...")
    translate_to_plain_english(doc_data, transcript, to_number, send_message)

    # 4. Render PDF
    log_step("Rendering PDF via ReportLab...")
    try:
        pdf_bytes = render_document_to_pdf(doc_data, domain)
    except Exception as e:
        print(f"PDF Generation failed: {e}")
        sys.exit(1)

    os.makedirs("output_pdfs", exist_ok=True)
    pdf_path = os.path.abspath(f"output_pdfs/{session_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    log_step(f"PDF saved locally to: {pdf_path}")

    # 5. Send PDF to WhatsApp
    if to_number and send_message and send_file:
        log_step(f"Triggering WhatsApp send to {to_number}...")
        caption = f"OmniVoice {domain.capitalize()} Summary.\nSession: {session_id}"

        try:
            ok, msg = send_message(to_number, caption)
            log_step("Caption sent." if ok else f"Caption failed: {msg}")

            ok, msg = send_file(to_number, pdf_path)
            log_step("PDF sent via WhatsApp!" if ok else f"PDF send failed: {msg}")

        except Exception as e:
            print(f"WhatsApp sending failed: {e}")
            print("Make sure your whatsapp-bridge is running on http://localhost:8080")
    else:
        log_step("WhatsApp sending skipped (no number provided or MCP unavailable).")

    # ── FEATURE 4 (POST-VISIT): Save this visit to patient record ───────────
    log_step("Saving visit to longitudinal patient record...")
    save_patient_visit(patient_id, doc_data, session_id, sentiment)

    # ── FEATURE 1: Medication Scheduler ─────────────────────────────────────
    if domain == "healthcare":
        log_step("Scheduling medication reminders...")
        schedule_medication_reminders(
            doc_data=doc_data,
            to_number=to_number,
            send_message_fn=send_message,
            demo_mode=True,   # True = hours become minutes for demo
            max_reminders=3,  # send 3 reminders per medication
        )

    print("\n" + "="*60)
    print(" PASSIVE LISTENER WORKFLOW COMPLETE")
    print("="*60)
    print(" Medication reminders running in background (daemon threads)")
    print(" Patient record saved to: patient_records/")
    print("="*60 + "\n")

    # Keep process alive for background reminder threads
    if domain == "healthcare" and doc_data.get("medications"):
        log_step("Keeping process alive for medication reminder threads...")
        log_step("Press Ctrl+C to exit when done.\n")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log_step("Exiting. Goodbye!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OmniVoice Passive Listener")
    parser.add_argument("--audio", required=True, help="Path to the pre-recorded .wav file")
    parser.add_argument("--domain", default="healthcare", help="Domain to process (e.g., healthcare, banking)")
    parser.add_argument("--to", help="WhatsApp number to send the PDF to (e.g., +919876543210)", default=os.getenv("OMNIVOICE_WHATSAPP_TO"))

    args = parser.parse_args()

    if not args.to:
        print("Warning: No WhatsApp number provided. Pass --to +91xxxxxxxxxx to send the PDF.")

    run_passive_pipeline(args.audio, args.domain, args.to)