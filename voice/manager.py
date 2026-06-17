"""
Coordinates speech recognition (STT), synthesis (TTS) and wake word detection.
"""
import logging
from typing import Optional, Any
from voice.stt.base import BaseSTT
from voice.tts.base import BaseTTS
from app.container import Container
from core.state_manager import AssistantState

# Globally import lightweight cloud STT engines to ensure PyInstaller detects them
from voice.stt.groq_stt import GroqSTT
from voice.stt.openai_stt import OpenAISTT
from voice.stt.google_stt import GoogleSTT

logger = logging.getLogger("VoiceManager")

def get_stt_provider(name: str, config: Optional[Any] = None) -> BaseSTT:
    """Factory function to get Speech-to-Text provider by name."""
    name = name.lower().strip()
    logger.info(f"Initializing STT provider: '{name}'")
    
    stt_model = config.stt_model if (config and hasattr(config, "stt_model") and config.stt_model) else "base"
    
    if name == "vosk":
        from voice.stt.vosk import VoskSTT
        return VoskSTT()
    elif name == "whisper_local":
        from voice.stt.whisper_local import WhisperLocalSTT
        return WhisperLocalSTT(model_name=stt_model)
    elif name == "faster_whisper":
        from voice.stt.faster_whisper import FasterWhisperSTT
        return FasterWhisperSTT(model_size=stt_model)
    elif name in ("gemini_stt", "gemini_live"):
        from voice.stt.gemini_stt import GeminiSTT
        return GeminiSTT(model_name=stt_model)
    elif name == "groq_stt":
        model = stt_model if stt_model and stt_model != "base" else "whisper-large-v3"
        return GroqSTT(model_name=model)
    elif name == "openai_stt":
        model = stt_model if stt_model and stt_model != "base" else "whisper-1"
        return OpenAISTT(model_name=model)
    elif name == "google_stt":
        return GoogleSTT()
    else:
        logger.warning(f"Unknown STT provider '{name}'. Falling back to VoskSTT.")
        from voice.stt.vosk import VoskSTT
        return VoskSTT()

def get_tts_provider(name: str, config: Optional[Any] = None) -> BaseTTS:
    """Factory function to get Text-to-Speech provider by name."""
    name = name.lower().strip()
    logger.info(f"Initializing TTS provider: '{name}'")
    
    tts_voice = config.tts_voice if (config and hasattr(config, "tts_voice") and config.tts_voice) else None
    
    if name == "piper":
        from voice.tts.piper import PiperTTS
        if tts_voice:
            return PiperTTS(model_path=tts_voice)
        return PiperTTS()
    elif name == "edge_tts":
        from voice.tts.edge_tts import EdgeTTS
        if tts_voice:
            return EdgeTTS(voice=tts_voice)
        return EdgeTTS()
    elif name == "elevenlabs":
        from voice.tts.elevenlabs import ElevenLabsTTS
        llm_config = None
        try:
            llm_config = Container.resolve("config")
        except Exception:
            pass
        # Check environment first, then config.voice.api_key, then config.llm.api_key
        from app.config.env import get_env
        api_key = get_env("VOICE_API_KEY") or get_env("ELEVENLABS_API_KEY")
        if not api_key and config and hasattr(config, "api_key") and config.api_key:
            api_key = config.api_key
        if not api_key and llm_config and hasattr(llm_config, "llm") and llm_config.llm.api_key:
            api_key = llm_config.llm.api_key
            
        if tts_voice:
            return ElevenLabsTTS(api_key=api_key, voice_id=tts_voice)
        return ElevenLabsTTS(api_key=api_key)
    elif name == "gemini_tts":
        from voice.tts.gemini_tts import GeminiTTS
        return GeminiTTS()
    elif name == "gemini_live":
        from voice.tts.gemini_live import GeminiLiveTTS
        if tts_voice:
            return GeminiLiveTTS(voice_name=tts_voice)
        return GeminiLiveTTS()
    else:
        logger.warning(f"Unknown TTS provider '{name}'. Falling back to PiperTTS.")
        from voice.tts.piper import PiperTTS
        return PiperTTS()

class VoiceManager:
    def __init__(self, config: Optional[Any] = None):
        # Resolve config from Container if not explicitly provided
        if config is None:
            try:
                config = Container.resolve("config").voice
            except Exception:
                config = None

        if config:
            self.stt = get_stt_provider(config.stt_provider, config)
            self.tts = get_tts_provider(config.tts_provider, config)
        else:
            from voice.stt.vosk import VoskSTT
            from voice.tts.piper import PiperTTS
            self.stt = VoskSTT()
            self.tts = PiperTTS()

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Process input speech audio and convert to text."""
        state_mgr = Container.resolve("state_manager")
        event_bus = Container.resolve("event_bus")

        logger.info("Starting speech-to-text transcription...")
        await state_mgr.transition_to(AssistantState.LISTENING)
        await event_bus.publish("voice_listening_start", {})

        try:
            text = await self.stt.transcribe(audio_data)
            logger.info(f"Speech transcribed: '{text}'")
            await event_bus.publish("voice_listening_success", {"text": text})
            return text
        except Exception as e:
            logger.error(f"Speech transcription failed: {e}")
            await event_bus.publish("voice_listening_error", {"error": str(e)})
            return ""
        finally:
            await state_mgr.transition_to(AssistantState.IDLE)

    async def synthesize_text(self, text: str) -> bytes:
        """Process output text response and convert to spoken audio bytes."""
        state_mgr = Container.resolve("state_manager")
        event_bus = Container.resolve("event_bus")

        logger.info("Starting text-to-speech synthesis...")
        await state_mgr.transition_to(AssistantState.SPEAKING)
        await event_bus.publish("voice_speaking_start", {"text": text})

        try:
            audio_data = await self.tts.synthesize(text)
            logger.info(f"Speech synthesized: {len(audio_data)} bytes")
            await event_bus.publish("voice_speaking_success", {"size": len(audio_data)})
            return audio_data
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            await event_bus.publish("voice_speaking_error", {"error": str(e)})
            return b""
        finally:
            # Note: Transition to AssistantState.IDLE is managed by the caller
            # (e.g. speak_text or trigger_push_to_talk) after audio playback is fully completed.
            pass
