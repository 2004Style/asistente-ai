"""
Configuration loader utilities.

Loads YAML files and environment variables into Python data structures.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

from app.config.schema import (
    Config, AppConfig, LLMConfig, VoiceConfig,
    MemoryConfig, SecurityConfig, PlatformsConfig, ToolsConfig
)
from app.config.env import get_env

def get_project_root() -> Path:
    """Find the root directory of the project."""
    return Path(__file__).parent.parent.parent.resolve()

def resolve_env_vars(data: Any) -> Any:
    """Recursively resolve strings starting with 'env:' using environment variables."""
    if isinstance(data, dict):
        return {k: resolve_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_env_vars(item) for item in data]
    elif isinstance(data, str) and data.startswith("env:"):
        env_var = data[4:]
        return get_env(env_var) or ""
    return data

def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file. Returns empty dict if file is missing or empty."""
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                return resolve_env_vars(data)
            return {}
    except Exception:
        return {}

def load_config() -> Config:
    """Load all configurations and merge them with environment variables."""
    from runtime.paths import CONFIG_DIR
    configs_dir = CONFIG_DIR

    # Load each configuration YAML
    app_data = load_yaml(configs_dir / "app.yml")
    llm_data = load_yaml(configs_dir / "llm.yml")
    voice_data = load_yaml(configs_dir / "voice.yml")
    memory_data = load_yaml(configs_dir / "memory.yml")
    security_data = load_yaml(configs_dir / "security.yml")
    platforms_data = load_yaml(configs_dir / "platforms.yml")
    tools_data = load_yaml(configs_dir / "tools.yml")

    # Env overrides
    # LLM API Key env overrides
    provider_key = get_env("PROVIDER_API_KEY")
    if provider_key:
        llm_data["api_key"] = provider_key
    else:
        # Fallback to provider-specific keys (e.g. GEMINI_API_KEY, OPENAI_API_KEY)
        provider = llm_data.get("provider", "openai").lower()
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openrouter": "OPENROUTER_API_KEY"
        }
        active_env_var = env_key_map.get(provider)
        env_key = get_env(active_env_var) if active_env_var else None
        if env_key:
            llm_data["api_key"] = env_key
        else:
            if not llm_data.get("api_key"):
                openai_key = get_env("OPENAI_API_KEY")
                if openai_key:
                    llm_data["api_key"] = openai_key

    # Voice API Key env overrides
    voice_key = get_env("VOICE_API_KEY")
    if voice_key:
        voice_data["api_key"] = voice_key
    else:
        # Fallback to ELEVENLABS_API_KEY
        elevenlabs_key = get_env("ELEVENLABS_API_KEY")
        if elevenlabs_key:
            voice_data["api_key"] = elevenlabs_key
    
    db_url = get_env("DATABASE_URL")
    if db_url:
        # If database URL is sqlite:///data/db/assistant.db, extract the path or keep the URL
        if db_url.startswith("sqlite:///"):
            memory_data["db_path"] = db_url.replace("sqlite:///", "")
        else:
            memory_data["db_path"] = db_url

    # Instantiate config classes
    return Config(
        app=AppConfig(**app_data),
        llm=LLMConfig(**llm_data),
        voice=VoiceConfig(**voice_data),
        memory=MemoryConfig(**memory_data),
        security=SecurityConfig(**security_data),
        platforms=PlatformsConfig(**platforms_data),
        tools=ToolsConfig(**tools_data)
    )
