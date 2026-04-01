import os
from groq import Groq

SYSTEM_PROMPT = '''You are OmniVoice, a multilingual conversational AI assistant
for Indian enterprises. You understand Kannada, Hindi, English, and code-mixed combinations naturally.
IMPORTANT RULES:
1. Reply in the SAME language the user spoke. If they mix Kannada+English, mix back.
2. Keep responses SHORT — 1-3 sentences max. This is a voice conversation.
3. Be conversational and warm, not formal.
4. If the user speaks Kannada, reply in Kannada. Hindi -> Hindi. English -> English.
5. For code-mixed input, respond naturally in the same mix style.'''

EXTRACT_PROMPT = '''You are a structured data extractor. Given a transcript and domain schema fields,
extract the relevant information and return a valid JSON object only.
No explanation. No markdown. Just the JSON object.'''


class GroqLLM:
    """Wrapper for Groq LLM — conversational mode (Pranav's original)."""
    def __init__(self, api_key: str = None, model: str = 'llama-3.3-70b-versatile'):
        self.api_key = api_key or os.environ.get('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError('GROQ_API_KEY is not set.')
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.system_prompt = SYSTEM_PROMPT

    def generate_response(self, text: str, history: list = None) -> str:
        """Generates response with context window history."""
        if history is None:
            history = []
        messages = [{'role': 'system', 'content': self.system_prompt}] + history[-10:]
        messages.append({'role': 'user', 'content': text})
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                stream=False,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f'[Groq Error] {e}')
            return "Sorry, I couldn't process that. Please try again."

    def detect_reply_language_hint(self, text: str) -> str:
        """Returns TTS language code hint based on script characters."""
        for ch in text:
            cp = ord(ch)
            if 0x0C80 <= cp <= 0x0CFF:
                return 'kn-IN'
            if 0x0900 <= cp <= 0x097F:
                return 'hi-IN'
        return 'en-IN'


# ---------- Prajwal's analyze() — called by routes/analyze.py ----------

async def analyze(transcript: str, domain: str, schema_fields: list, rag_context: str) -> dict:
    """
    Extracts structured data from transcript using Groq.
    Called by routes/analyze.py — do not rename or change signature.
    """
    import json

    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        # Fallback mock if no key
        return {"error": "GROQ_API_KEY not set", "raw_transcript": transcript}

    client = Groq(api_key=api_key)

    fields_str = ", ".join(schema_fields) if schema_fields else "all relevant fields"
    context_block = f"\nRAG CONTEXT:\n{rag_context}\n" if rag_context else ""

    prompt = f"""
Domain: {domain}
Fields to extract: {fields_str}
{context_block}
Transcript:
{transcript}

Return a JSON object with the extracted fields only. No explanation. No markdown.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": EXTRACT_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_transcript": transcript, "llm_raw_output": raw}
    except Exception as e:
        return {"error": str(e), "raw_transcript": transcript}