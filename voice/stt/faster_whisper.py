"""
Speech‑to‑Text provider implementing faster-whisper.
"""
import logging
from voice.stt.base import BaseSTT

logger = logging.getLogger("FasterWhisperSTT")

class FasterWhisperSTT(BaseSTT):
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self._initialized = False

    def _init_whisper(self):
        if self._initialized:
            return
        try:
            from faster_whisper import WhisperModel
            from runtime.paths import resolve_path
            model_dir = resolve_path(f"data/models/faster-whisper/{self.model_size}")
            
            if model_dir.exists() and (model_dir / "model.bin").exists():
                logger.info(f"Loading local faster-whisper model from: {model_dir}")
                self.model = WhisperModel(str(model_dir), device="cpu", compute_type="int8")
            else:
                logger.warning(f"Local faster-whisper model directory {model_dir} not found. Loading automatically...")
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            self._initialized = True
        except ImportError:
            logger.warning("faster-whisper package not installed. Running in mock STT mode.")

    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio bytes using faster-whisper or mock fallback."""
        self._init_whisper()
        if not self._initialized:
            return ""

        try:
            import io
            # faster-whisper transcribes from file path or binary buffer
            segments, info = self.model.transcribe(io.BytesIO(audio_data), beam_size=5)
            text = "".join(seg.text for seg in segments)
            return text.strip()
        except Exception as e:
            logger.error(f"Error in faster-whisper transcription: {e}")
            return ""
