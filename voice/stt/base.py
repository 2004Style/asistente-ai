"""
Common interface for Speech‑to‑Text providers.
"""
from abc import ABC, abstractmethod

class BaseSTT(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe raw audio bytes into text."""
        pass
