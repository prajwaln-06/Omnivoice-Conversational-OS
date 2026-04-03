import os
import sys
import time
import uuid
import json
import asyncio
import pyaudio
import wave
import io
from datetime import datetime
from dotenv import load_dotenv

# Load keys
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Make whatsapp bridge wrapper importable
sys.path.append(os.path.join(os.path.dirname(__file__), "whatsapp-mcp", "whatsapp-mcp-server"))
from whatsapp import send_file, send_message  # noqa: E402

from ai.asr import SarvamASR
from ai.llm import GroqLLM
from ai.tts import SarvamTTS
from ai.document_generator import generate_with_groq, render_document_to_pdf

# Audio Constants
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 200
CHUNK_FRAMES = int(SAMPLE_RATE * CHUNK_MS / 1000)
SILENCE_THRESH = 300
SILENCE_SECS = 1.8

def log_step(msg: str):
    print(f"[OmniVoice] {msg}", flush=True)

def detect_silence(audio_data: bytes, threshold: int = SILENCE_THRESH) -> bool:
    import array
    samples = array.array("h", audio_data)
    peak = max(abs(s) for s in samples) if samples else 0
    return peak < threshold

def record_utterance() -> bytes | None:
    import keyboard
    pa = pyaudio.PyAudio()
    
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=2,  # AMD Audio Device
        frames_per_buffer=CHUNK_FRAMES,
    )
    
    print("\n🎙️ HOLD SPACE to speak, RELEASE to send. (Type 'q' + Enter to quit)", flush=True)
    
    # Wait for space press
    keyboard.wait('space')
    print("🔴 Recording...", flush=True)
    frames = []
    
    while keyboard.is_pressed('space'):
        chunk = stream.read(CHUNK_FRAMES, exception_on_overflow=False)
        frames.append(chunk)

    stream.stop_stream()
    stream.close()
    pa.terminate()
    print("✅ Done recording.", flush=True)

    if not frames:
        return None
    return b"".join(frames)

def play_audio(audio_bytes: bytes):
    buf = io.BytesIO(audio_bytes)
    with wave.open(buf, 'rb') as wf:
        pa = pyaudio.PyAudio()
        
        stream = pa.open(
            format=pa.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
        )
        
        data_chunk = wf.readframes(1024)
        while data_chunk:
            stream.write(data_chunk)
            data_chunk = wf.readframes(1024)
        stream.stop_stream()
        stream.close()
        pa.terminate()

def run_autonomous_session(recipient_phone: str, domain: str = "healthcare"):
    print("="*60)
    print(" 🚀 OmniVoice Autonomous Agent Started")
    print("="*60)
    
    asr = SarvamASR()
    llm = GroqLLM()
    tts = SarvamTTS()
    
    session_id = str(uuid.uuid4())
    history = []
    transcripts = []
    
    # On-the-go JSON state object for live analysis
    live_state = {
        "session_id": session_id,
        "domain": domain,
        "turns": 0,
        "extracted_entities": []
    }

    turn = 0
    try:
        while True:
            turn += 1
            pcm_data = record_utterance()
            if not pcm_data:
                continue
                
            log_step("Transcribing with Sarvam...")
            import wave, io
            wav_buf = io.BytesIO()
            with wave.open(wav_buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(pcm_data)
            wav_bytes = wav_buf.getvalue()
            user_text = asr.transcribe(wav_bytes, filename="utterance.wav")
            if not user_text:
                print("[OmniVoice] ⚠️ Empty transcript — speak louder or longer", flush=True)
                continue
                
            print(f"👤 You: {user_text}")
            transcripts.append(f"User: {user_text}")
            
            # Check for stop keywords in English, Hindi, or Kannada
            stop_words = ["end conversation", "stop session", "stop", "mugi", "khatam"]
            if any(word in user_text.lower() for word in stop_words):
                log_step("Stop keyword detected. Ending session.")
                break

            log_step("Groq analyzing & generating reply...")
            reply = llm.generate_response(user_text, history)
            
            # Update Live JSON State
            live_state["turns"] = turn
            live_state["extracted_entities"].append({"turn": turn, "user_input": user_text})
            
            print(f"🤖 OmniVoice: {reply}")
            transcripts.append(f"Assistant: {reply}")
            
            history.append({'role': 'user', 'content': user_text})
            history.append({'role': 'assistant', 'content': reply})
            
            lang = llm.detect_reply_language_hint(reply)
            log_step(f"Synthesizing audio ({lang})...")
            audio_bytes = tts.synthesize(reply, lang_code=lang)
            if audio_bytes:
                play_audio(audio_bytes)

    except KeyboardInterrupt:
        log_step("Session stopped manually via Ctrl+C.")

    # --- SESSION END: PDF Generation & WhatsApp ---
    full_transcript = "\n".join(transcripts)
    if not full_transcript.strip():
        print("No conversation captured. Exiting.")
        return

    print("\n" + "="*60)
    log_step("Session Ended. Generating PDF Report...")
    
    document_data = generate_with_groq(
        transcript=full_transcript,
        extracted_data=live_state, 
        rag_context="Live autonomous session capture.",
        domain=domain,
        session_id=session_id
    )
    
    print(f"[JSON_DATA] {json.dumps(document_data)}", flush=True)

    log_step("Rendering PDF...")
    pdf_bytes = render_document_to_pdf(document_data, domain=domain)
    
    output_dir = os.path.join(os.path.dirname(__file__), "generated_docs")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"omni_report_{session_id}.pdf")
    
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    log_step(f"PDF saved locally at: {pdf_path}")

    # Send via WhatsApp MCP
    if recipient_phone:
        log_step(f"Sending document to WhatsApp ({recipient_phone})...")
        intro_ok, intro_msg = send_message(recipient_phone, f"OmniVoice Session {session_id} ended. Here is your summary report:")
        file_ok, file_msg = send_file(recipient_phone, pdf_path)
        log_step(f"WhatsApp Status: Message={intro_ok}, File={file_ok}")

if __name__ == '__main__':
    # Grab recipient from .env or override here
    WHATSAPP_RECIPIENT = os.getenv("OMNIVOICE_WHATSAPP_TO", "")
    if not WHATSAPP_RECIPIENT:
        print("⚠️ Warning: OMNIVOICE_WHATSAPP_TO not set in .env. Document will save locally but won't send.")
        
    run_autonomous_session(recipient_phone=WHATSAPP_RECIPIENT, domain="healthcare")