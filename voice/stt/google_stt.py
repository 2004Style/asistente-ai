"""
Speech‑to‑Text provider using Google Cloud Speech-to-Text API.
"""
import base64
import json
import urllib.request
import urllib.error
import asyncio
import logging
from voice.stt.base import BaseSTT
from app.container import Container

logger = logging.getLogger("GoogleSTT")

class GoogleSTT(BaseSTT):
    def __init__(self, language_code: str = "es-ES"):
        self.language_code = language_code

    async def transcribe(self, audio_data: bytes) -> str:
        """Upload and transcribe audio bytes using Google Cloud Speech-to-Text API."""
        logger.info("Transcribing audio using Google Cloud Speech-to-Text API...")
        try:
            config = Container.resolve("config")
            
            # Resolve Google API key
            api_key = config.voice.api_key
            if not api_key:
                llm_key = config.llm.api_key
                if llm_key and llm_key.startswith("AIzaSy"):
                    api_key = llm_key

            if not api_key:
                logger.warning("Google Cloud API key not configured for STT. Returning empty transcription.")
                return ""

            # Base64 encode the raw PCM audio bytes
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")

            url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"
            payload = {
                "config": {
                    "encoding": "LINEAR16",
                    "sampleRateHertz": 16000,
                    "languageCode": self.language_code
                },
                "audio": {
                    "content": audio_b64
                }
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
                    logger.error(f"Google Cloud Speech-to-Text API error ({e.code}): {error_body}")
                    raise
                except Exception as e:
                    logger.error(f"Failed to communicate with Google Cloud Speech-to-Text: {e}")
                    raise

            res_data = await asyncio.to_thread(_send_request)
            results = res_data.get("results", [])
            if not results:
                return ""
            
            # Concatenate transcripts from all parts
            transcripts = []
            for result in results:
                alternatives = result.get("alternatives", [])
                if alternatives:
                    transcripts.append(alternatives[0].get("transcript", ""))
            
            return " ".join(transcripts).strip()
        except Exception as e:
            logger.error(f"Google Cloud STT transcription failed: {e}")
            return ""
