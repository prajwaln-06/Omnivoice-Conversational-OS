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

class GroqLLM:
    '''Wrapper for Groq LLM.'''
    def __init__(self, api_key: str = None, model: str = 'llama-3.3-70b-versatile'):
        self.api_key = api_key or os.environ.get('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError('GROQ_API_KEY is not set.')
            
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.system_prompt = SYSTEM_PROMPT
        
    def generate_response(self, text: str, history: list = None) -> str:
        '''Generates response with context window history.'''
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
        '''Returns TTS language code hint based on script characters.'''
        for ch in text:
            cp = ord(ch)
            if 0x0C80 <= cp <= 0x0CFF:
                return 'kn-IN'
            if 0x0900 <= cp <= 0x097F:
                return 'hi-IN'
        return 'en-IN'
