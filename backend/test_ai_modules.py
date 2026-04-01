import os
import sys
import pyaudio
import wave
import io
from dotenv import load_dotenv

# Load keys from .env for testing
load_dotenv()

from ai.asr import SarvamASR
from ai.llm import GroqLLM
from ai.tts import SarvamTTS

def test_pipeline():
    print("="*50)
    print("Testing Modular AI Components")
    print("="*50)
    
    llm = GroqLLM()
    tts = SarvamTTS()

    test_prompt = "Hello! Please reply in English and say exactly: 'The modular AI components are working perfectly.'"
    print(f"\n1. Testing Groq LLM...")
    print(f"   Prompt: {test_prompt}")
    
    reply = llm.generate_response(test_prompt)
    print(f"   Reply : {reply}")
    
    if not reply or "Sorry" in reply:
        print("   -> [FAILED] LLM Test")
        return

    print(f"\n2. Testing Sarvam TTS...")
    lang = llm.detect_reply_language_hint(reply)
    print(f"   Detected Lang: {lang}")
    audio_bytes = tts.synthesize(reply, lang_code=lang)
    
    if not audio_bytes:
        print("   -> [FAILED] TTS did not return audio.")
        return
        
    print(f"   Success! Received {len(audio_bytes)} bytes of audio.")
    
    print("\n3. Testing Playback (Playing the generated audio)...")
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
        
    print("\n[SUCCESS] AI Modules are working! 🎉")

if __name__ == '__main__':
    test_pipeline()
