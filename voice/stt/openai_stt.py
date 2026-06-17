"""
Speech‑to‑Text provider using OpenAI's hosted Whisper API.
"""
import base64
import json
import urllib.request
import urllib.error
import asyncio
import logging
from voice.stt.base import BaseSTT
from app.container import Container
from app.config.env import get_env

logger = logging.getLogger("OpenAISTT")

class OpenAISTT(BaseSTT):
    def __init__(self, model_name: str = "whisper-1"):
        # OpenAI hosted Whisper API only supports whisper-1
        self.model_name = "whisper-1"

    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        """Prepend a standard WAV header to raw PCM data so OpenAI can parse it as audio/wav."""
        num_samples = len(pcm_data) // (bits_per_sample // 8)
        subchunk2_size = num_samples * channels * (bits_per_sample // 8)
        chunk_size = 36 + subchunk2_size
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)

        header = bytearray()
        header.extend(b'RIFF')
        header.extend(chunk_size.to_bytes(4, 'little'))
        header.extend(b'WAVE')
        header.extend(b'fmt ')
        header.extend((16).to_bytes(4, 'little'))
        header.extend((1).to_bytes(2, 'little'))
        header.extend(channels.to_bytes(2, 'little'))
        header.extend(sample_rate.to_bytes(4, 'little'))
        header.extend(byte_rate.to_bytes(4, 'little'))
        header.extend(block_align.to_bytes(2, 'little'))
        header.extend(bits_per_sample.to_bytes(2, 'little'))
        header.extend(b'data')
        header.extend(subchunk2_size.to_bytes(4, 'little'))

        return bytes(header) + pcm_data

    async def transcribe(self, audio_data: bytes) -> str:
        """Upload and transcribe audio bytes using OpenAI's Whisper API."""
        logger.info("Transcribing audio using OpenAI Whisper API...")
        try:
            config = Container.resolve("config")
            
            # Resolve OpenAI API key: check environment first, then config.voice.api_key, then config.llm.api_key
            api_key = get_env("OPENAI_API_KEY")
            if not api_key:
                api_key = config.voice.api_key
            if not api_key and config.llm.provider == "openai":
                api_key = config.llm.api_key

            if not api_key:
                logger.warning("OpenAI API key not configured. Returning empty transcription.")
                return ""

            wav_data = self._pcm_to_wav(audio_data)

            # Build multipart/form-data payload
            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            body = []

            # File Part
            body.append(f'--{boundary}'.encode('utf-8'))
            body.append('Content-Disposition: form-data; name="file"; filename="audio.wav"'.encode('utf-8'))
            body.append(b'Content-Type: audio/wav\r\n')
            body.append(wav_data)
            body.append(b'')

            # Model Part
            body.append(f'--{boundary}'.encode('utf-8'))
            body.append('Content-Disposition: form-data; name="model"'.encode('utf-8'))
            body.append(b'')
            body.append(self.model_name.encode('utf-8'))
            body.append(b'')

            # Language Part
            body.append(f'--{boundary}'.encode('utf-8'))
            body.append('Content-Disposition: form-data; name="language"'.encode('utf-8'))
            body.append(b'')
            body.append(b'es')
            body.append(b'')

            body.append(f'--{boundary}--'.encode('utf-8'))
            body.append(b'')

            payload = b'\r\n'.join(body)

            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Authorization": f"Bearer {api_key}"
            }

            def _send_request():
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers=headers,
                    method="POST"
                )
                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        return json.loads(response.read().decode("utf-8"))
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode("utf-8")
                    logger.error(f"OpenAI Whisper STT API error ({e.code}): {error_body}")
                    raise
                except Exception as e:
                    logger.error(f"Failed to communicate with OpenAI Whisper STT: {e}")
                    raise

            res_data = await asyncio.to_thread(_send_request)
            text = res_data.get("text", "")
            return text.strip()
        except Exception as e:
            logger.error(f"OpenAI STT transcription failed: {e}")
            return ""
