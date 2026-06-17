"""
Common interface for Text‑to‑Speech providers.
"""
from abc import ABC, abstractmethod

class BaseTTS(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Synthesize text into audio bytes."""
        pass
