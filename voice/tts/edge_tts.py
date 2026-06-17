"""
Text‑to‑Speech provider using Microsoft Edge translation API.
"""
import logging
from voice.tts.base import BaseTTS
from voice.tts.piper import PiperTTS

logger = logging.getLogger("EdgeTTS")

class EdgeTTS(BaseTTS):
    def __init__(self, voice: str = "es-ES-AlvaroNeural"):
        self.voice = voice
        self.fallback_tts = PiperTTS()

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text using edge-tts or fall back to Piper mock."""
        try:
            import edge_tts
            import tempfile
            import os
            
            logger.info(f"Synthesizing text using edge-tts voice: {self.voice}")
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_name = tmp.name
                
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(tmp_name)
            
            with open(tmp_name, "rb") as f:
                data = f.read()
                
            os.remove(tmp_name)
            return data
        except ImportError:
            logger.warning("edge-tts package not installed. Falling back to Piper mock sound bytes.")
        except Exception as e:
            logger.error(f"EdgeTTS synthesis failed: {e}")
            
        return await self.fallback_tts.synthesize(text)
