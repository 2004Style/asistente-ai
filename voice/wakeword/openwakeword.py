"""
Wake word detector using openwakeword local models.
"""
import logging
from voice.wakeword.base import BaseWakeWordDetector

logger = logging.getLogger("OpenWakeWordDetector")

class OpenWakeWordDetector(BaseWakeWordDetector):
    def __init__(self, model_path: str = ""):
        self.model_path = model_path
        self._initialized = False
        self.oww_model = None

    def _init_model(self):
        if self._initialized:
            return
        try:
            from openwakeword.model import Model
            logger.info("Initializing openwakeword models...")
            # Load default models (e.g. alexa or custom)
            self.oww_model = Model()
            self._initialized = True
        except ImportError:
            logger.warning("openwakeword package is not installed. Running in mock wake word mode.")

    async def detect(self, audio_data: bytes) -> bool:
        """Analyze audio chunk for wake word."""
        self._init_model()
        if not self._initialized:
            return False

        try:
            # openwakeword processes 16-bit PCM 16000Hz numpy arrays
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            prediction = self.oww_model.predict(audio_array)
            # Check prediction values
            for model_name, score in prediction.items():
                if score > 0.5:
                    logger.info(f"Wake word detected: '{model_name}' (score={score})")
                    return True
        except Exception as e:
            logger.error(f"Error in openwakeword processing: {e}")
            
        return False
