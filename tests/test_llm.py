"""
Unit tests for the LLM providers and request router.
"""
import pytest
from app.config.schema import LLMConfig
from llm.router import get_llm_provider
from llm.message import Message

def test_llm_router_instantiation():
    # Test OpenAI
    cfg_openai = LLMConfig(provider="openai", model="gpt-4", temperature=0.5)
    provider_openai = get_llm_provider(cfg_openai)
    assert provider_openai.get_model_name() == "gpt-4"

    # Test Gemini
    cfg_gemini = LLMConfig(provider="gemini", model="gemini-1.5", temperature=0.1)
    provider_gemini = get_llm_provider(cfg_gemini)
    assert provider_gemini.get_model_name() == "gemini-1.5"

    # Test DeepSeek
    cfg_deepseek = LLMConfig(provider="deepseek", model="deepseek-chat", temperature=0.7)
    provider_deepseek = get_llm_provider(cfg_deepseek)
    assert provider_deepseek.get_model_name() == "deepseek-chat"

    # Test Groq
    cfg_groq = LLMConfig(provider="groq", model="llama-3.3-70b-versatile", temperature=0.7)
    provider_groq = get_llm_provider(cfg_groq)
    assert provider_groq.get_model_name() == "llama-3.3-70b-versatile"

@pytest.mark.anyio
async def test_mock_fallback_generate():
    # OpenAI provider with empty API key triggers mock response
    cfg = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="")
    provider = get_llm_provider(cfg)
    
    msg = Message(role="user", content="ping")
    response = await provider.generate([msg])
    
    assert response.role == "assistant"
    assert "MOCK RESPONSE" in response.content
    assert "ping" in response.content

    # DeepSeek provider with empty API key
    cfg_ds = LLMConfig(provider="deepseek", model="deepseek-chat", api_key="")
    prov_ds = get_llm_provider(cfg_ds)
    resp_ds = await prov_ds.generate([msg])
    assert resp_ds.role == "assistant"
    assert "MOCK RESPONSE" in resp_ds.content
    assert "ping" in resp_ds.content

    # Groq provider with empty API key
    cfg_gr = LLMConfig(provider="groq", model="llama-3.3-70b-versatile", api_key="")
    prov_gr = get_llm_provider(cfg_gr)
    resp_gr = await prov_gr.generate([msg])
    assert resp_gr.role == "assistant"
    assert "MOCK RESPONSE" in resp_gr.content
    assert "ping" in resp_gr.content

def test_llm_env_overrides(monkeypatch):
    from app.config.loader import load_config
    from unittest.mock import patch
    
    # Clear unified keys to test the provider-specific fallback mechanism
    monkeypatch.delenv("PROVIDER_API_KEY", raising=False)
    monkeypatch.delenv("VOICE_API_KEY", raising=False)
    
    # Mock provider-specific and general keys in env
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-secret")
    
    with patch("app.config.loader.load_yaml") as mock_load:
        def side_effect(path):
            if "llm.yml" in str(path):
                return {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": ""}
            return {}
        mock_load.side_effect = side_effect
        
        cfg = load_config()
        assert cfg.llm.provider == "gemini"
        assert cfg.llm.api_key == "gemini-test-secret"

