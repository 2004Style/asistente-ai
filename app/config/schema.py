"""
Pydantic schemas for configuration files.

Defines structured models to validate and parse configuration data.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    name: str = Field(default="rbot")
    language: str = Field(default="es")
    ui_mode: str = Field(default="text")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)

class LLMConfig(BaseModel):
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.7)
    api_key: Optional[str] = Field(default=None)
    api_base: Optional[str] = Field(default=None)

class VoiceConfig(BaseModel):
    enabled: bool = Field(default=False)
    stt_provider: str = Field(default="vosk")
    tts_provider: str = Field(default="piper")
    push_to_talk: bool = Field(default=True)
    stt_model: Optional[str] = Field(default="base")
    tts_voice: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)

class MemoryConfig(BaseModel):
    db_path: str = Field(default="data/db/assistant.db")
    short_term_limit: int = Field(default=20)
    vector_store_type: str = Field(default="sqlite")

class SecurityConfig(BaseModel):
    min_permission_level: str = Field(default="low")
    require_confirmation: bool = Field(default=True)

class PlatformsConfig(BaseModel):
    default_platform: str = Field(default="linux")
    desktop_environment: str = Field(default="hyprland")

class ToolsConfig(BaseModel):
    enabled_tools: List[str] = Field(default_factory=lambda: [
        "list_windows",
        "list_apps",
        "list_workspaces",
        "read_file",
        "list_notes"
    ])

class Config(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    platforms: PlatformsConfig = Field(default_factory=PlatformsConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
