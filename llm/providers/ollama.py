"""
Alias of the Local provider specifically for Ollama instances.
"""
from llm.providers.local import LocalProvider

class OllamaProvider(LocalProvider):
    """Ollama LLM provider implementing LocalProvider's connection protocols."""
    pass
