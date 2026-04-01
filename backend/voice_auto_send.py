import argparse
import io
import os
import sys
import time
import uuid
import wave
from datetime import datetime

import pyaudio
from dotenv import load_dotenv
from groq import Groq

from ai.asr import SarvamASR
from ai.document_generator import generate_with_groq, render_document_to_pdf
from ai.llm import GroqLLM
from ai.tts import SarvamTTS

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Make whatsapp bridge wrapper importable
sys.path.append(os.path.join(os.path.dirname(__file__), "whatsapp-mcp", "whatsapp-mcp-server"))
from whatsapp import send_file, send_message  # noqa: E402

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 200
CHUNK_FRAMES = int(SAMPLE_RATE * CHUNK_MS / 1000)
SILENCE_THRESH = 500
SILENCE_SECS = 1.2
DEFAULT_AUDIO_HINT = os.getenv("OMNIVOICE_AUDIO_DEVICE_HINT", "OnePlus")


def log_step(message: str):
    print(f"[OmniVoice] {message}", flush=True)


def list_audio_devices(pa: pyaudio.PyAudio):
    log_step("Enumerating audio devices...")
    for i in range(pa.get_device_count()):
        dev = pa.get_device_info_by_index(i)
        name = dev.get("name", "Unknown")
        in_ch = int(dev.get("maxInputChannels", 0))
        out_ch = int(dev.get("maxOutputChannels", 0))
        rate = int(dev.get("defaultSampleRate", 0))
        print(f"  - idx={i:02d} in={in_ch} out={out_ch} rate={rate} name={name}")


def pick_device_index(pa: pyaudio.PyAudio, for_output: bool, preferred_hint: str | None) -> int | None:
    channel_key = "maxOutputChannels" if for_output else "maxInputChannels"
    matched = None

    if preferred_hint:
        hint = preferred_hint.lower()
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if int(dev.get(channel_key, 0)) <= 0:
                continue
            if hint in dev.get("name", "").lower():
                matched = i
                break

    if matched is not None:
        return matched

    for i in range(pa.get_device_count()):
        dev = pa.get_device_info_by_index(i)
        if int(dev.get(channel_key, 0)) > 0:
            return i
    return None


def detect_silence(audio_data: bytes, threshold: int = SILENCE_THRESH) -> bool:
    import array

    samples = array.array("h", audio_data)
    peak = max(abs(s) for s in samples) if samples else 0
    return peak < threshold


def record_utterance(preferred_input_hint: str | None = None) -> bytes | None:
    pa = pyaudio.PyAudio()

    target_idx = pick_device_index(pa, for_output=False, preferred_hint=preferred_input_hint)
    if target_idx is not None:
        in_name = pa.get_device_info_by_index(target_idx).get("name", "Unknown")
        log_step(f"Selected input device idx={target_idx} ({in_name})")
    else:
        log_step("No explicit input device found; using PyAudio default.")

    try:
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_FRAMES,
            input_device_index=target_idx,
        )
    except OSError:
        log_step("Input device open failed; retrying with system default input device.")
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_FRAMES,
        )

    log_step("Listening... speak your consultation now")
    frames = []
    silent_chunks = 0
    speaking = False
    max_silent = int(SILENCE_SECS * 1000 / CHUNK_MS)

    try:
        while True:
            chunk = stream.read(CHUNK_FRAMES, exception_on_overflow=False)
            is_silent = detect_silence(chunk)
            if not is_silent:
                speaking = True
                silent_chunks = 0
                frames.append(chunk)
            elif speaking:
                frames.append(chunk)
                silent_chunks += 1
                if silent_chunks >= max_silent:
                    break
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

    if not frames or not speaking:
        log_step("No speech segment detected in this turn.")
        return None

    log_step(f"Captured audio bytes: {len(b''.join(frames))}")
    return b"".join(frames)


def play_audio(audio_bytes: bytes, preferred_output_hint: str | None = None):
    buf = io.BytesIO(audio_bytes)
    with wave.open(buf, "rb") as wf:
        pa = pyaudio.PyAudio()

        target_idx = pick_device_index(pa, for_output=True, preferred_hint=preferred_output_hint)
        if target_idx is not None:
            out_name = pa.get_device_info_by_index(target_idx).get("name", "Unknown")
            log_step(f"Selected output device idx={target_idx} ({out_name})")
        else:
            log_step("No explicit output device found; using PyAudio default output.")

        try:
            stream = pa.open(
                format=pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=target_idx,
            )
        except OSError:
            log_step("Output device open failed; retrying with system default output device.")
            try:
                stream = pa.open(
                    format=pa.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                )
            except OSError as e:
                log_step(f"Audio playback failed: {e}")
                list_audio_devices(pa)
                pa.terminate()
                return

        log_step("Playing assistant speech...")
        data_chunk = wf.readframes(1024)
        while data_chunk:
            stream.write(data_chunk)
            data_chunk = wf.readframes(1024)
        stream.stop_stream()
        stream.close()
        pa.terminate()
        log_step("Playback complete.")


def normalize_recipient(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("91") and len(digits) == 12:
        return digits
    if len(digits) == 10:
        return f"91{digits}"
    return digits


def _generate_interviewer_reply(client: Groq, history: list[dict], user_text: str) -> str:
    system_prompt = (
        "You are OmniVoice, a voice conversation assistant for healthcare intake. "
        "You must keep this as a real back-and-forth conversation. "
        "Rules: ask exactly one clear follow-up question in each reply unless user says they want to stop. "
        "Be concise (1-3 sentences), empathetic, and practical. "
        "Language policy: always reply in the SAME language/style as the latest user message. "
        "If the user uses Kannada, reply in Kannada. Hindi -> Hindi. English -> English. "
        "If the user uses code-mix (for example Kannada+English or Hindi+English), reply in the same mix style. "
        "Do not translate to pure English unless the user spoke pure English. "
        "Collect: symptoms, duration, severity, medications, allergies, and next-step preference. "
        "If user says end conversation or stop, reply with a brief closing sentence only."
    )

    messages = [{"role": "system", "content": system_prompt}] + history[-12:]
    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.5,
        max_tokens=180,
    )
    return response.choices[0].message.content.strip()


def _infer_tts_lang_code(text: str) -> str:
    """Infer TTS language code from script detection.
    Sarvam handles code-mixed content natively, so we just detect primary script."""
    for ch in text:
        cp = ord(ch)
        # Kannada Unicode range
        if 0x0C80 <= cp <= 0x0CFF:
            return "kn-IN"
        # Devanagari (covers Hindi, Marathi, etc.)
        if 0x0900 <= cp <= 0x097F:
            return "hi-IN"
    # Default to English if no native scripts detected
    return "en-IN"


def run_live_tts_conversation(
    domain: str = "healthcare",
    max_turns: int = 12,
    input_hint: str | None = None,
    output_hint: str | None = None,
) -> dict:
    """Function 1: Live ASR->Groq->TTS loop that captures full conversation for document generation."""
    asr = SarvamASR()
    llm = GroqLLM()
    tts = SarvamTTS()
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    history = []
    transcripts: list[str] = []
    session_id = str(uuid.uuid4())

    log_step("Live conversation started.")
    log_step("Say 'end conversation' or press Ctrl+C to finish and build the PDF.")
    log_step(f"Domain: {domain} | Max turns: {max_turns}")
    log_step(f"Input hint: {input_hint or '(auto)'} | Output hint: {output_hint or '(auto)'}")
    log_step("Language support: Kannada, Hindi, English, and code-mixed (Sarvam auto-detect enabled)")
    pa_debug = pyaudio.PyAudio()
    list_audio_devices(pa_debug)
    pa_debug.terminate()

    greeting = "Hello, I am OmniVoice. You can speak to me in Kannada, Hindi, English, or any mix. What issue are you facing today?"
    print(f"OmniVoice: {greeting}")
    transcripts.append(f"Assistant: {greeting}")
    history.append({"role": "assistant", "content": greeting})
    try:
        t0 = time.time()
        log_step("TTS synthesis started for greeting.")
        greeting_audio = tts.synthesize(greeting, lang_code="en-IN")
        log_step(f"TTS synthesis finished in {time.time() - t0:.2f}s")
        if greeting_audio:
            play_audio(greeting_audio, preferred_output_hint=output_hint)
    except Exception:
        pass

    turn = 0
    try:
        while turn < max_turns:
            turn += 1
            log_step(f"Turn {turn}/{max_turns} started.")
            pcm_data = record_utterance(preferred_input_hint=input_hint)
            if not pcm_data:
                log_step("No speech detected, retrying same conversation loop.")
                continue

            log_step("ASR transcription started (Sarvam auto-detect mode for code-mixed speech).")
            t0 = time.time()
            user_text = asr.transcribe(pcm_data, language_code="unknown")
            log_step(f"ASR transcription finished in {time.time() - t0:.2f}s | Text: {user_text}")
            if not user_text:
                log_step("Could not transcribe this turn.")
                continue

            print(f"You: {user_text}")
            transcripts.append(f"User: {user_text}")

            if "end conversation" in user_text.lower() or "stop" in user_text.lower():
                break

            log_step("Groq response generation started.")
            t0 = time.time()
            reply = _generate_interviewer_reply(groq_client, history, user_text)
            log_step(f"Groq response generated in {time.time() - t0:.2f}s")
            print(f"OmniVoice: {reply}")
            transcripts.append(f"Assistant: {reply}")

            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": reply})

            lang = _infer_tts_lang_code(reply)
            log_step(f"Detected TTS language: {lang} (Sarvam will handle code-mixed content)")
            log_step("TTS synthesis started for assistant reply.")
            t0 = time.time()
            audio = tts.synthesize(reply, lang_code=lang)
            log_step(f"TTS synthesis finished in {time.time() - t0:.2f}s")
            if audio:
                play_audio(audio, preferred_output_hint=output_hint)
            else:
                log_step("No TTS audio returned for this turn.")
    except KeyboardInterrupt:
        log_step("Conversation interrupted. Finalizing with captured transcript...")

    return {
        "session_id": session_id,
        "domain": domain,
        "history": history,
        "transcript": "\n".join(transcripts),
        "turns": len(transcripts),
    }


def build_and_send_pdf_from_conversation(conversation: dict, recipient: str) -> dict:
    """Function 2: Generate a true PDF from conversation text and send it via WhatsApp MCP."""
    session_id = conversation.get("session_id") or str(uuid.uuid4())
    domain = conversation.get("domain", "healthcare")
    transcript = conversation.get("transcript", "")

    if not transcript.strip():
        raise ValueError("Conversation transcript is empty. Cannot build PDF.")

    document_data = conversation.get("document_data")
    if not document_data:
        log_step("Document generation started from full transcript.")
        t0 = time.time()
        extracted_data = {
            "session_id": session_id,
            "conversation_turns": conversation.get("turns", 0),
            "conversation_date": datetime.now().strftime("%d %B %Y"),
        }
        rag_context = "Conversation captured from OmniVoice live interactive session."
        document_data = generate_with_groq(
            transcript=transcript,
            extracted_data=extracted_data,
            rag_context=rag_context,
            domain=domain,
            session_id=session_id,
        )
        log_step(f"Document generation finished in {time.time() - t0:.2f}s")

    log_step("Rendering PDF bytes.")
    pdf_bytes = render_document_to_pdf(document_data, domain=domain)
    if not pdf_bytes.startswith(b"%PDF"):
        raise RuntimeError("Generated file is not a valid PDF payload.")
    log_step(f"PDF render complete. Size={len(pdf_bytes)} bytes")

    output_dir = os.path.join(os.path.dirname(__file__), "generated_docs")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"omni_report_{session_id}.pdf")

    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    log_step(f"PDF saved at: {pdf_path}")

    normalized_to = normalize_recipient(recipient)
    intro_ok, intro_msg = send_message(
        normalized_to,
        f"OmniVoice report generated for session {session_id}. Sending PDF now.",
    )
    log_step(f"WhatsApp intro message status: {intro_ok} | {intro_msg}")
    file_ok, file_msg = send_file(normalized_to, pdf_path)
    log_step(f"WhatsApp PDF file status: {file_ok} | {file_msg}")

    return {
        "session_id": session_id,
        "pdf_path": pdf_path,
        "caption_sent": intro_ok,
        "caption_response": intro_msg,
        "file_sent": file_ok,
        "file_response": file_msg,
    }


def main():
    parser = argparse.ArgumentParser(description="Live TTS conversation -> Groq PDF -> WhatsApp sender")
    parser.add_argument("--to", required=False, default=os.getenv("OMNIVOICE_WHATSAPP_TO", ""), help="Recipient phone number")
    parser.add_argument("--domain", default="healthcare", help="Domain for document generation")
    parser.add_argument("--max-turns", type=int, default=12, help="Maximum conversation turns")
    parser.add_argument("--input-device-hint", default=os.getenv("OMNIVOICE_INPUT_DEVICE_HINT", DEFAULT_AUDIO_HINT), help="Preferred input device name hint")
    parser.add_argument("--output-device-hint", default=os.getenv("OMNIVOICE_OUTPUT_DEVICE_HINT", DEFAULT_AUDIO_HINT), help="Preferred output device name hint")
    args = parser.parse_args()

    if not args.to:
        raise SystemExit("Recipient missing. Pass --to +91xxxxxxxxxx or set OMNIVOICE_WHATSAPP_TO in .env")

    conversation = run_live_tts_conversation(
        domain=args.domain,
        max_turns=args.max_turns,
        input_hint=args.input_device_hint,
        output_hint=args.output_device_hint,
    )

    if not conversation.get("transcript"):
        raise SystemExit("No captured conversation transcript. Nothing to document.")

    print("\nGenerating PDF and sending to WhatsApp...")
    result = build_and_send_pdf_from_conversation(conversation, args.to)

    print("\n----- RESULT -----")
    print(f"session_id: {result['session_id']}")
    print(f"pdf_path: {result['pdf_path']}")
    print(f"caption_sent: {result['caption_sent']}")
    print(f"caption_response: {result['caption_response']}")
    print(f"file_sent: {result['file_sent']}")
    print(f"file_response: {result['file_response']}")


if __name__ == "__main__":
    start = time.time()
    main()
    print(f"Done in {time.time() - start:.2f}s")
