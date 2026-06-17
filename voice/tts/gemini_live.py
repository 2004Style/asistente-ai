"""
Text‑to‑Speech provider using Gemini's native audio generation API.
"""
import base64
import json
import urllib.request
import urllib.error
import asyncio
import logging
from voice.tts.base import BaseTTS
from voice.tts.edge_tts import EdgeTTS
from app.container import Container

logger = logging.getLogger("GeminiLiveTTS")

class GeminiLiveTTS(BaseTTS):
    def __init__(self, voice_name: str = "Charon", model: str = "gemini-2.5-flash-preview-tts"):
        self.voice_name = voice_name
        self.model = model
        self.fallback_tts = EdgeTTS()

    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        """Prepend a standard WAV header to raw PCM data so it can be played natively."""
        num_samples = len(pcm_data) // (bits_per_sample // 8)
        subchunk2_size = num_samples * channels * (bits_per_sample // 8)
        chunk_size = 36 + subchunk2_size
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)

        header = bytearray()
        header.extend(b'RIFF')                                # ChunkID
        header.extend(chunk_size.to_bytes(4, 'little'))       # ChunkSize
        header.extend(b'WAVE')                                # Format
        header.extend(b'fmt ')                                # Subchunk1ID
        header.extend((16).to_bytes(4, 'little'))             # Subchunk1Size (16 for PCM)
        header.extend((1).to_bytes(2, 'little'))              # AudioFormat (1 for PCM)
        header.extend(channels.to_bytes(2, 'little'))         # NumChannels
        header.extend(sample_rate.to_bytes(4, 'little'))      # SampleRate
        header.extend(byte_rate.to_bytes(4, 'little'))        # ByteRate
        header.extend(block_align.to_bytes(2, 'little'))      # BlockAlign
        header.extend(bits_per_sample.to_bytes(2, 'little'))  # BitsPerSample
        header.extend(b'data')                                # Subchunk2ID
        header.extend(subchunk2_size.to_bytes(4, 'little'))   # Subchunk2Size

        return bytes(header) + pcm_data

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text using Gemini's native audio generation API."""
        try:
            config = Container.resolve("config")
            
            # Prioritize voice.api_key and reject OpenRouter keys
            api_key = config.voice.api_key
            if not api_key:
                llm_key = config.llm.api_key
                if llm_key and llm_key.startswith("AIzaSy"):
                    api_key = llm_key

            if not api_key:
                logger.warning("Direct Google Gemini API key not configured (or OpenRouter key cannot be used for native Live TTS). Using EdgeTTS fallback.")
                try:
                    from runtime.daemon import launch_alert_window
                    launch_alert_window()
                except Exception as ex:
                    logger.error(f"Failed to launch alert window: {ex}")
                return await self.fallback_tts.synthesize(text)

            # Determine the model to use. Use configured model or fallback.
            # Avoid overriding with standard LLM chat models (like gpt-4o or gemini-2.0-flash without -tts)
            model_to_use = self.model
            llm_model = config.llm.model
            if llm_model and ("-tts" in llm_model or "native-audio" in llm_model):
                model_to_use = llm_model

            # Clean model name to avoid double "models/" prefix
            clean_model = model_to_use
            if clean_model.startswith("models/"):
                clean_model = clean_model[7:]

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"Lee el siguiente texto en voz alta de manera natural, sin agregar comentarios tuyos:\n{text}"
                    }]
                }],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": self.voice_name
                            }
                        }
                    }
                }
            }

            headers = {
                "Content-Type": "application/json"
            }

            def _send_request():
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                try:
                    with urllib.request.urlopen(req, timeout=30) as response:
                        return json.loads(response.read().decode("utf-8"))
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode("utf-8")
                    logger.error(f"Gemini Live TTS API error ({e.code}): {error_body}")
                    raise
                except Exception as e:
                    logger.error(f"Failed to communicate with Gemini Live TTS: {e}")
                    raise

            logger.info(f"Synthesizing text natively via Gemini Live model: {clean_model} voice: {self.voice_name}...")
            res_data = await asyncio.to_thread(_send_request)
            
            # Extract the audio bytes from parts
            parts = res_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    audio_b64 = part["inlineData"].get("data", "")
                    mime_type = part["inlineData"].get("mimeType", "")
                    if audio_b64:
                        raw_pcm = base64.b64decode(audio_b64)
                        
                        # Parse sample rate from mimeType if possible, e.g. "rate=24000"
                        sample_rate = 24000
                        if "rate=" in mime_type:
                            try:
                                rate_part = mime_type.split("rate=")[1]
                                rate_str = "".join(c for c in rate_part if c.isdigit())
                                if rate_str:
                                    sample_rate = int(rate_str)
                            except Exception as e:
                                logger.warning(f"Could not parse sample rate from mimeType '{mime_type}': {e}")
                        
                        return self._pcm_to_wav(raw_pcm, sample_rate=sample_rate)
                        
            logger.warning("No audio inlineData returned in Gemini Live response.")
        except Exception as e:
            logger.error(f"Gemini Live TTS failed: {e}")
            try:
                from runtime.daemon import launch_alert_window
                launch_alert_window()
            except Exception as ex:
                logger.error(f"Failed to launch alert window: {ex}")

        return await self.fallback_tts.synthesize(text)
