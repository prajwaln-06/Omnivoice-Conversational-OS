import os
import wave
import io
import tempfile
import requests

class SarvamASR:
    '''Wrapper for Sarvam AI Speech-to-Text REST API.'''
    def __init__(self, api_key: str = None, sample_rate: int = 16000, channels: int = 1):
        self.api_key = api_key or os.environ.get('SARVAM_API_KEY')
        if not self.api_key:
            raise ValueError('SARVAM_API_KEY is not set.')
            
        self.sample_rate = sample_rate
        self.channels = channels
        self.url = 'https://api.sarvam.ai/speech-to-text'
        self.headers = {'api-subscription-key': self.api_key}

    def _pcm_to_wav_bytes(self, pcm_data: bytes) -> bytes:
        '''Wraps raw PCM bytes in a WAV container.'''
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm_data)
        return buf.getvalue()

    def _is_wav(self, audio_data: bytes) -> bool:
        return audio_data[:4] == b'RIFF'

    def _is_mp3(self, audio_data: bytes) -> bool:
        return audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb'

    def _get_audio_file_metadata(self, audio_data: bytes, filename: str) -> tuple[str, str]:
        name = (filename or '').lower()
        if name.endswith('.mp3') or self._is_mp3(audio_data):
            return '.mp3', 'audio/mpeg'
        if name.endswith('.wav') or self._is_wav(audio_data):
            return '.wav', 'audio/wav'
        return '', ''

    def transcribe(
        self,
        audio_data: bytes,
        model: str = 'saarika:v2.5',
        language_code: str = 'unknown',
        filename: str = 'audio.wav',
    ) -> str:
        '''Sends audio to Sarvam REST API and returns transcript.'''
        ext, content_type = self._get_audio_file_metadata(audio_data, filename)
        if not ext:
            file_bytes = self._pcm_to_wav_bytes(audio_data)
            ext = '.wav'
            content_type = 'audio/wav'
        else:
            file_bytes = audio_data

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        transcript = ''
        try:
            with open(tmp_path, 'rb') as f:
                files = {'file': (f'audio{ext}', f, content_type)}
                data  = {
                    'model': model,
                    'language_code': language_code,
                    'with_timestamps': 'false',
                }
                resp = requests.post(self.url, headers=self.headers, files=files, data=data, timeout=30)
                resp.raise_for_status()
                transcript = resp.json().get('transcript', '')
        except Exception as e:
            print(f'[Sarvam ASR Error] {e}')
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return transcript.strip()
