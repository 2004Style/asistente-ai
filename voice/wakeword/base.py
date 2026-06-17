"""
Common interface for Wake Word detectors.
"""
from abc import ABC, abstractmethod

class BaseWakeWordDetector(ABC):
    @abstractmethod
    async def detect(self, audio_data: bytes) -> bool:
        """Process a chunk of audio and return True if the wake word is detected."""
        pass
