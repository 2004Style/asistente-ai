"""
Speech‑to‑Text provider using local OpenAI Whisper package.
"""
import logging
import tempfile
import os
from voice.stt.base import BaseSTT

logger = logging.getLogger("WhisperLocalSTT")

class WhisperLocalSTT(BaseSTT):
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None
        self._initialized = False

    def _init_whisper(self):
        if self._initialized:
            return
        try:
            import whisper
            from runtime.paths import resolve_path
            model_dir = resolve_path("data/models/whisper")
            model_file = model_dir / f"{self.model_name}.pt"
            
            if model_file.exists():
                logger.info(f"Loading local OpenAI Whisper model from: {model_file}")
                self.model = whisper.load_model(str(model_file))
            else:
                logger.warning(f"Local Whisper model file {model_file} not found. Loading automatically via package cache...")
                self.model = whisper.load_model(self.model_name)
            self._initialized = True
        except ImportError:
            logger.warning("openai-whisper package not installed. Running in mock STT mode.")

    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio bytes using local Whisper."""
        self._init_whisper()
        if not self._initialized:
            return ""

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_name = tmp.name

        try:
            result = self.model.transcribe(tmp_name)
            return result.get("text", "").strip()
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return ""
        finally:
            try:
                os.remove(tmp_name)
            except Exception:
                pass
