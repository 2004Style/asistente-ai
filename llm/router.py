"""
Routes requests to the appropriate LLM provider based on configuration.
"""
from app.config.schema import LLMConfig
from llm.base import BaseLLMProvider
from llm.providers.openai import OpenAIProvider
from llm.providers.local import LocalProvider
from llm.providers.gemini import GeminiProvider
from llm.providers.anthropic import AnthropicProvider
from llm.providers.openrouter import OpenRouterProvider
from llm.providers.ollama import OllamaProvider
from llm.providers.deepseek import DeepSeekProvider
from llm.providers.groq import GroqProvider

def get_llm_provider(config: LLMConfig) -> BaseLLMProvider:
    """Factory function to get the appropriate LLM provider based on config."""
    provider_name = config.provider.lower()
    api_key = config.api_key or ""
    
    if provider_name == "openai":
        return OpenAIProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature
        )
    elif provider_name == "gemini":
        return GeminiProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature
        )
    elif provider_name == "anthropic":
        return AnthropicProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature
        )
    elif provider_name == "deepseek":
        return DeepSeekProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature
        )
    elif provider_name == "groq":
        return GroqProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature
        )
    elif provider_name == "openrouter":
        return OpenRouterProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature
        )
    elif provider_name == "ollama":
        return OllamaProvider(
            host=config.api_base or "http://localhost:11434",
            model=config.model,
            temperature=config.temperature
        )
    elif provider_name == "local":
        return LocalProvider(
            host=config.api_base or "http://localhost:11434",
            model=config.model,
            temperature=config.temperature
        )
    else:
        # Fallback to OpenAI
        return OpenAIProvider(
            api_key=api_key,
            model=config.model,
            temperature=config.temperature
        )
