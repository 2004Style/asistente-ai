"""
Base classes and interfaces for tools and actions within the assistant.
"""
from abc import ABC, abstractmethod
from typing import Any
from tools.manifest import ToolManifest

class BaseTool(ABC):
    manifest: ToolManifest

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool logic with keyword arguments matching the manifest arguments_schema."""
        pass
