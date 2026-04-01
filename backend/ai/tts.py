import os
import requests
import base64

class SarvamTTS:
    '''Wrapper for Sarvam AI Text-to-Speech REST API.'''
    def __init__(self, api_key: str = None, speaker: str = 'ritu', default_lang: str = 'kn-IN'):
        self.api_key = api_key or os.environ.get('SARVAM_API_KEY')
        if not self.api_key:
            raise ValueError('SARVAM_API_KEY is not set.')
            
        self.speaker = speaker
        self.default_lang = default_lang
        self.url = 'https://api.sarvam.ai/text-to-speech'
        self.headers = {
            'api-subscription-key': self.api_key,
            'Content-Type': 'application/json',
        }

    def synthesize(self, text: str, lang_code: str = None) -> bytes:
        '''Generates speech bytes (WAV base64 decoded).'''
        target_lang = lang_code or self.default_lang
        payload = {
            'inputs': [text],
            'target_language_code': target_lang,
            'speaker': self.speaker,
            'model': 'bulbul:v3',
            'enable_preprocessing': True,
        }

        try:
            resp = requests.post(self.url, json=payload, headers=self.headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            audio_b64 = data.get('audios', [None])[0]
            if not audio_b64:
                print('[Sarvam TTS] No audio returned')
                return None

            return base64.b64decode(audio_b64)
        except Exception as e:
            print(f'[Sarvam TTS Error] {e}')
            return None
