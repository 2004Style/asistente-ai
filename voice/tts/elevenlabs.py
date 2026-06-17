"""
Text‑to‑Speech provider using ElevenLabs API.
"""
import json
import urllib.request
import urllib.error
import asyncio
import logging
from typing import List
from voice.tts.base import BaseTTS
from voice.tts.edge_tts import EdgeTTS

logger = logging.getLogger("ElevenLabsTTS")

class ElevenLabsTTS(BaseTTS):
    def __init__(self, api_key: str = "", voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.fallback_tts = EdgeTTS()

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text using ElevenLabs API or fall back to Piper mock."""
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured. Falling back to EdgeTTS fallback.")
            try:
                from runtime.daemon import launch_alert_window
                launch_alert_window()
            except Exception as ex:
                logger.error(f"Failed to launch alert window: {ex}")
            return await self.fallback_tts.synthesize(text)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
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
                    return response.read()
            except Exception as e:
                raise e

        try:
            logger.info(f"Synthesizing text using ElevenLabs voice: {self.voice_id}")
            audio_data = await asyncio.to_thread(_send_request)
            return audio_data
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            try:
                from runtime.daemon import launch_alert_window
                launch_alert_window()
            except Exception as ex:
                logger.error(f"Failed to launch alert window: {ex}")
            return await self.fallback_tts.synthesize(text)
