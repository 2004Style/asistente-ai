"""
Defines capabilities of different LLM models, such as context length or supported modalities.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ModelCapabilities(BaseModel):
    model_name: str
    context_length: int = Field(default=4096)
    supports_vision: bool = Field(default=False)
    supports_audio: bool = Field(default=False)
    supports_tools: bool = Field(default=False)
    modalities: List[str] = Field(default_factory=lambda: ["text"])

MODEL_CAPABILITIES_REGISTRY: Dict[str, ModelCapabilities] = {
    "gpt-4o-mini": ModelCapabilities(
        model_name="gpt-4o-mini",
        context_length=128000,
        supports_vision=True,
        supports_tools=True,
        modalities=["text", "image"]
    ),
    "gpt-4o": ModelCapabilities(
        model_name="gpt-4o",
        context_length=128000,
        supports_vision=True,
        supports_tools=True,
        modalities=["text", "image"]
    ),
    "gemini-1.5-flash": ModelCapabilities(
        model_name="gemini-1.5-flash",
        context_length=1000000,
        supports_vision=True,
        supports_audio=True,
        supports_tools=True,
        modalities=["text", "image", "audio"]
    ),
    "gemini-1.5-pro": ModelCapabilities(
        model_name="gemini-1.5-pro",
        context_length=2000000,
        supports_vision=True,
        supports_audio=True,
        supports_tools=True,
        modalities=["text", "image", "audio"]
    ),
    "gemini-2.5-flash": ModelCapabilities(
        model_name="gemini-2.5-flash",
        context_length=1000000,
        supports_vision=True,
        supports_audio=True,
        supports_tools=True,
        modalities=["text", "image", "audio"]
    ),
    "gemini-2.5-pro": ModelCapabilities(
        model_name="gemini-2.5-pro",
        context_length=2000000,
        supports_vision=True,
        supports_audio=True,
        supports_tools=True,
        modalities=["text", "image", "audio"]
    ),
    "gemini-2.0-flash": ModelCapabilities(
        model_name="gemini-2.0-flash",
        context_length=1000000,
        supports_vision=True,
        supports_audio=True,
        supports_tools=True,
        modalities=["text", "image", "audio"]
    ),
    "gemini-flash-latest": ModelCapabilities(
        model_name="gemini-flash-latest",
        context_length=1000000,
        supports_vision=True,
        supports_audio=True,
        supports_tools=True,
        modalities=["text", "image", "audio"]
    ),
    "claude-3-5-sonnet-latest": ModelCapabilities(
        model_name="claude-3-5-sonnet-latest",
        context_length=200000,
        supports_vision=True,
        supports_tools=True,
        modalities=["text", "image"]
    ),
    "llama3": ModelCapabilities(
        model_name="llama3",
        context_length=8192,
        supports_tools=True,
        modalities=["text"]
    )
}

def get_model_capabilities(model_name: str) -> ModelCapabilities:
    """Retrieve capabilities for a model, falling back to conservative defaults if unknown."""
    if model_name in MODEL_CAPABILITIES_REGISTRY:
        return MODEL_CAPABILITIES_REGISTRY[model_name]
    
    for key, capabilities in MODEL_CAPABILITIES_REGISTRY.items():
        if key in model_name:
            return capabilities
            
    return ModelCapabilities(
        model_name=model_name,
        context_length=4096,
        supports_vision=False,
        supports_tools=False,
        modalities=["text"]
    )
