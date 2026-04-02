import os
import wave
import io
import tempfile
import requests

try:
    import audioop
except ImportError:
    import audioop_lts as audioop  # Python 3.13+

class SarvamASR:
    '''Wrapper for Sarvam AI Speech-to-Text REST API.'''
    def __init__(self, api_key: str = None, sample_rate: int = 16000, channels: int = 1):
        self.api_key = api_key or os.environ.get('SARVAM_API_KEY')
        if not self.api_key:
            raise ValueError('SARVAM_API_KEY is not set.')

        self.target_rate = sample_rate
        self.target_channels = channels
        self.url = 'https://api.sarvam.ai/speech-to-text'
        self.headers = {'api-subscription-key': self.api_key}

    def _normalize_wav(self, audio_data: bytes) -> bytes:
        '''
        Converts any WAV to 16kHz, mono, 16-bit PCM — what Sarvam requires.
        Handles stereo->mono, sample-rate conversion, and bit-depth normalization.
        '''
        buf_in = io.BytesIO(audio_data)
        with wave.open(buf_in, 'rb') as wf:
            src_channels  = wf.getnchannels()
            src_sampwidth = wf.getsampwidth()   # bytes per sample
            src_rate      = wf.getframerate()
            pcm           = wf.readframes(wf.getnframes())

        # --- 1. Normalize bit depth to 16-bit (2 bytes) ---
        if src_sampwidth == 1:                      # 8-bit unsigned -> 16-bit
            pcm = audioop.bias(pcm, 1, -128)        # unsigned -> signed
            pcm = audioop.lin2lin(pcm, 1, 2)
            src_sampwidth = 2
        elif src_sampwidth == 3:                    # 24-bit -> 16-bit
            pcm = audioop.lin2lin(pcm, 3, 2)
            src_sampwidth = 2
        elif src_sampwidth == 4:                    # 32-bit -> 16-bit
            pcm = audioop.lin2lin(pcm, 4, 2)
            src_sampwidth = 2

        # --- 2. Stereo -> Mono (FIX: tomono requires 4 args: fragment, width, lfactor, rfactor) ---
        if src_channels == 2:
            pcm = audioop.tomono(pcm, src_sampwidth, 0.5, 0.5)
            src_channels = 1

        # --- 3. Resample to target rate (e.g., 48kHz -> 16kHz) ---
        if src_rate != self.target_rate:
            pcm, _ = audioop.ratecv(
                pcm, src_sampwidth, src_channels,
                src_rate, self.target_rate, None
            )

        # --- 4. Wrap back into a valid WAV container ---
        buf_out = io.BytesIO()
        with wave.open(buf_out, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.target_rate)
            wf.writeframes(pcm)
        return buf_out.getvalue()

    def _is_wav(self, data: bytes) -> bool:
        return data[:4] == b'RIFF'

    def _is_mp3(self, data: bytes) -> bool:
        return data[:3] == b'ID3' or data[:2] == b'\xff\xfb'

    def transcribe(
        self,
        audio_data: bytes,
        model: str = 'saarika:v2.5',
        language_code: str = 'unknown',
        filename: str = 'audio.wav',
    ) -> str:
        '''Sends audio to Sarvam REST API and returns transcript.'''

        if self._is_mp3(audio_data):
            ext, content_type = '.mp3', 'audio/mpeg'
            file_bytes = audio_data                 # MP3 sent as-is
        elif self._is_wav(audio_data):
            print('[Sarvam ASR] Normalizing WAV to 16kHz mono 16-bit...')
            file_bytes  = self._normalize_wav(audio_data)
            ext, content_type = '.wav', 'audio/wav'
        else:
            # Unknown format — assume raw PCM, wrap in WAV
            file_bytes  = self._normalize_wav(audio_data)
            ext, content_type = '.wav', 'audio/wav'

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
                resp = requests.post(
                    self.url, headers=self.headers,
                    files=files, data=data, timeout=60
                )
                resp.raise_for_status()
                transcript = resp.json().get('transcript', '')

        except Exception as e:
            print(f'[Sarvam ASR Error] {e}')

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return transcript.strip()