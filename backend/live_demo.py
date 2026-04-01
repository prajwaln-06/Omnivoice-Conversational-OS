import os
import sys
import pyaudio
import wave
import io
import asyncio
from dotenv import load_dotenv

# Load keys from .env
load_dotenv()

from ai.asr import SarvamASR
from ai.llm import GroqLLM
from ai.tts import SarvamTTS

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 200
CHUNK_FRAMES = int(SAMPLE_RATE * CHUNK_MS / 1000)
SILENCE_THRESH = 500
SILENCE_SECS = 1.2

def detect_silence(audio_data: bytes, threshold: int = SILENCE_THRESH) -> bool:
    import array
    samples = array.array('h', audio_data)
    peak = max(abs(s) for s in samples) if samples else 0
    return peak < threshold

def record_utterance() -> bytes:
    pa = pyaudio.PyAudio()
    
    # Dynamically find the OnePlus Buds microphone
    target_idx = None
    for i in range(pa.get_device_count()):
        dev = pa.get_device_info_by_index(i)
        if dev.get('maxInputChannels', 0) > 0 and 'OnePlus' in dev.get('name', ''):
            target_idx = i
            break
            
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
        # Fall back to default microphone when preferred device is unavailable.
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_FRAMES,
        )
        target_idx = None
    print(f"\n🎙️  Listening via OnePlus Buds (Device {target_idx})... (speak now)", flush=True)
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
        return None

    print(f"   -> Captured {len(frames) * CHUNK_MS}ms of audio", flush=True)
    return b"".join(frames)
    
def play_audio(audio_bytes: bytes):
    buf = io.BytesIO(audio_bytes)
    with wave.open(buf, 'rb') as wf:
        pa = pyaudio.PyAudio()
        
        # Dynamically find the OnePlus Buds speaker/headset
        target_idx = None
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if dev.get('maxOutputChannels', 0) > 0 and 'OnePlus' in dev.get('name', ''):
                target_idx = i
                break
                
        if target_idx is not None:
            print(f"   [Audio Route] Auto-selected OnePlus Output (Device {target_idx})")
            
        try:
            stream = pa.open(
                format=pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=target_idx,
            )
        except OSError:
            # Fall back to default speaker when preferred output route fails.
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

async def run_pipeline():
    print("="*55)
    print("  OmniVoice Modular AI Live Demo")
    print("="*55)
    print("Press Ctrl+C to quit.\n")
    
    asr = SarvamASR()
    llm = GroqLLM()
    tts = SarvamTTS()
    history = []
    turn = 0
    
    while True:
        turn += 1
        print(f"\n── Turn {turn} " + "─"*40)
        pcm_data = record_utterance()
        if not pcm_data:
            continue
            
        print("   🔍 Transcribing...")
        transcript = asr.transcribe(pcm_data)
        if not transcript:
            print("   (could not transcribe)")
            continue
            
        print(f"   👤 You said  : {transcript}")
        
        print("   🧠 OmniVoice is thinking...")
        reply = llm.generate_response(transcript, history)
        
        history.append({'role': 'user', 'content': transcript})
        history.append({'role': 'assistant', 'content': reply})
        print(f"   🤖 OmniVoice : {reply}")
        
        lang = llm.detect_reply_language_hint(reply)
        print(f"   🔊 Speaking ({lang})...")
        
        audio_bytes = tts.synthesize(reply, lang_code=lang)
        if audio_bytes:
            play_audio(audio_bytes)
        else:
            print("   [Failed to generate audio playback]")

if __name__ == '__main__':
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
