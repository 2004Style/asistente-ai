"""
Text‑to‑Speech provider using Google Cloud Text‑to‑Speech API.
"""
import base64
import json
import urllib.request
import urllib.error
import asyncio
import logging
from voice.tts.base import BaseTTS
from voice.tts.edge_tts import EdgeTTS
from app.container import Container

logger = logging.getLogger("GeminiTTS")

class GeminiTTS(BaseTTS):
    def __init__(self):
        self.fallback_tts = EdgeTTS()

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text using Google Cloud TTS or fall back to Piper mock."""
        try:
            config = Container.resolve("config")
            api_key = config.voice.api_key or config.llm.api_key
            if not api_key:
                logger.warning("Gemini API key not configured for TTS. Using EdgeTTS fallback.")
                try:
                    from runtime.daemon import launch_alert_window
                    launch_alert_window()
                except Exception as ex:
                    logger.error(f"Failed to launch alert window: {ex}")
                return await self.fallback_tts.synthesize(text)

            # Detect language code and voice dynamically
            voice_name = config.voice.tts_voice or "es-ES-Neural2-F"
            lang = "es-ES"
            if voice_name.startswith("en-"):
                lang = "en-US"
            elif voice_name.startswith("es-MX-"):
                lang = "es-MX"
            elif hasattr(config.app, "language") and config.app.language:
                if config.app.language.lower().startswith("en") and not config.voice.tts_voice:
                    lang = "en-US"
                    voice_name = "en-US-Neural2-F"

            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
            payload = {
                "input": {
                    "text": text
                },
                "voice": {
                    "languageCode": lang,
                    "name": voice_name
                },
                "audioConfig": {
                    "audioEncoding": "MP3"
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
                    logger.error(f"Google Cloud TTS API error ({e.code}): {error_body}")
                    raise
                except Exception as e:
                    logger.error(f"Failed to communicate with Google Cloud TTS: {e}")
                    raise

            logger.info("Synthesizing text using Google Cloud TTS API...")
            res_data = await asyncio.to_thread(_send_request)
            audio_content = res_data.get("audioContent", "")
            if audio_content:
                return base64.b64decode(audio_content)
        except Exception as e:
            logger.error(f"Gemini Cloud TTS failed: {e}")
            try:
                from runtime.daemon import launch_alert_window
                launch_alert_window()
            except Exception as ex:
                logger.error(f"Failed to launch alert window: {ex}")
            
        return await self.fallback_tts.synthesize(text)
