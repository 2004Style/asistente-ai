"""
Offline STT implementation using Vosk.
Vosk supports multiple languages and runs without an Internet connection.
"""
import logging
from voice.stt.base import BaseSTT

logger = logging.getLogger("VoskSTT")

class VoskSTT(BaseSTT):
    def __init__(self, model_path: str = "data/models/vosk-model-es"):
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self._initialized = False

    def _init_vosk(self):
        if self._initialized:
            return
        try:
            from runtime.paths import resolve_path
            resolved_path = str(resolve_path(self.model_path))
            from vosk import Model, KaldiRecognizer
            logger.info(f"Loading Vosk model from {resolved_path}")
            self.model = Model(resolved_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            self._initialized = True
        except ImportError:
            logger.warning("vosk python package is not installed. Running in mock STT mode.")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")

    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio bytes using Vosk or mock fallback."""
        self._init_vosk()
        if not self._initialized:
            # Mock fallback
            logger.info("Mocking audio transcription...")
            return ""
            
        try:
            import json
            from vosk import KaldiRecognizer
            # Create a fresh recognizer instance to avoid carrying over state/history from previous turns
            rec = KaldiRecognizer(self.model, 16000)
            rec.AcceptWaveform(audio_data)
            res = json.loads(rec.Result())
            return res.get("text", "").strip()
        except Exception as e:
            logger.error(f"Error during Vosk transcription: {e}")
            return ""

