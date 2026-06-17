"""
Speech‑to‑Text provider using Google Gemini's multimodal audio transcription API.
"""
import base64
import json
import urllib.request
import urllib.error
import asyncio
import logging
from voice.stt.base import BaseSTT
from app.container import Container

from typing import Optional

logger = logging.getLogger("GeminiSTT")

class GeminiSTT(BaseSTT):
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name

    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        """Prepend a standard WAV header to raw PCM data so Gemini can parse it as audio/wav."""
        num_samples = len(pcm_data) // (bits_per_sample // 8)
        subchunk2_size = num_samples * channels * (bits_per_sample // 8)
        chunk_size = 36 + subchunk2_size
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)

        header = bytearray()
        header.extend(b'RIFF')                                # ChunkID
        header.extend(chunk_size.to_bytes(4, 'little'))       # ChunkSize
        header.extend(b'WAVE')                                # Format
        header.extend(b'fmt ')                                # Subchunk1ID
        header.extend((16).to_bytes(4, 'little'))             # Subchunk1Size (16 for PCM)
        header.extend((1).to_bytes(2, 'little'))              # AudioFormat (1 for PCM)
        header.extend(channels.to_bytes(2, 'little'))         # NumChannels
        header.extend(sample_rate.to_bytes(4, 'little'))      # SampleRate
        header.extend(byte_rate.to_bytes(4, 'little'))        # ByteRate
        header.extend(block_align.to_bytes(2, 'little'))      # BlockAlign
        header.extend(bits_per_sample.to_bytes(2, 'little'))  # BitsPerSample
        header.extend(b'data')                                # Subchunk2ID
        header.extend(subchunk2_size.to_bytes(4, 'little'))   # Subchunk2Size

        return bytes(header) + pcm_data

    async def transcribe(self, audio_data: bytes) -> str:
        """Upload and transcribe audio bytes using Gemini generateContent inline data API."""
        logger.info("Transcribing audio using Gemini API...")
        try:
            config = Container.resolve("config")
            
            # Prioritize voice.api_key and reject OpenRouter keys
            api_key = config.voice.api_key
            if not api_key:
                llm_key = config.llm.api_key
                if llm_key and llm_key.startswith("AIzaSy"):
                    api_key = llm_key

            if not api_key:
                logger.warning("Direct Google Gemini API key not configured (or OpenRouter key cannot be used for direct Gemini STT). Returning empty transcription.")
                return ""
                
            # Convert raw PCM bytes to WAV format before sending
            wav_data = self._pcm_to_wav(audio_data)
            audio_b64 = base64.b64encode(wav_data).decode("utf-8")
            
            # Determine which model to use
            model = self.model_name
            if not model:
                model = config.voice.stt_model
            
            if not model or model == "base":
                model = "gemini-2.5-flash"
                
            # Fallback/override from LLM model if default gemini-2.5-flash is targeted
            if model == "gemini-2.5-flash":
                llm_model = config.llm.model
                if llm_model and ("gemini-1.5" in llm_model or "gemini-2.0" in llm_model or "gemini-2.5" in llm_model) and not ("openrouter" in llm_model or "sk-or" in llm_model):
                    model = llm_model
            
            # Map defunct/404 models to gemini-2.5-flash
            if "gemini-1.5-flash" in model and "8b" not in model:
                model = "gemini-2.5-flash"
                
            # Clean model name to avoid double "models/" prefix
            clean_model = model
            if clean_model.startswith("models/"):
                clean_model = clean_model[7:]

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "audio/wav",
                                "data": audio_b64
                            }
                        },
                        {
                            "text": "Transcribe the audio exactly. Output only the transcription text and nothing else."
                        }
                    ]
                }]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            def _send_request():
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        return json.loads(response.read().decode("utf-8"))
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode("utf-8")
                    logger.error(f"Gemini STT API error ({e.code}): {error_body}")
                    raise
                except Exception as e:
                    logger.error(f"Failed to communicate with Gemini STT: {e}")
                    raise

            res_data = await asyncio.to_thread(_send_request)
            text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
        except Exception as e:
            logger.error(f"Gemini STT transcription failed: {e}")
            return ""

