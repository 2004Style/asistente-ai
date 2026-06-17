"""
Base class for large language model providers.

Defines the interface that all LLM implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import List
from llm.message import Message

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[Message], **kwargs) -> Message:
        """Generate a response from the LLM based on conversation messages."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the name of the model currently in use."""
        pass
