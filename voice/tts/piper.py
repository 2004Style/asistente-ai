"""
Offline TTS using Piper voices.
"""
import os
import subprocess
import tempfile
import logging
from voice.tts.base import BaseTTS

logger = logging.getLogger("PiperTTS")

class PiperTTS(BaseTTS):
    def __init__(self, model_path: str = "data/models/es_ES-carlfm-x_low.onnx"):
        self.model_path = model_path

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text into speech using Piper or a mock WAV fallback."""
        from runtime.paths import resolve_path
        resolved_path = str(resolve_path(self.model_path))
        if not os.path.exists(resolved_path):
            logger.warning(f"Piper model not found at {resolved_path}. Returning mock WAV sound bytes.")
            return self._generate_mock_wav()

        # Write to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            tmp_name = tmpfile.name

        try:
            # Command to run piper:
            # echo "text" | piper --model model.onnx --output_file out.wav
            cmd = ["piper", "--model", resolved_path, "--output_file", tmp_name]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.communicate(input=text.encode("utf-8"))
            
            if proc.returncode == 0:
                with open(tmp_name, "rb") as f:
                    audio_bytes = f.read()
                return audio_bytes
            else:
                logger.error(f"Piper process failed with return code {proc.returncode}")
        except Exception as e:
            logger.error(f"Failed to execute Piper CLI: {e}")
        finally:
            try:
                os.remove(tmp_name)
            except Exception:
                pass
                
        return self._generate_mock_wav()

    def _generate_mock_wav(self) -> bytes:
        """Create a mock 1-second silent WAV file header & dummy bytes."""
        # Standard 44-byte WAV header for mono, 16000Hz, 16-bit PCM
        header = bytearray(44)
        header[0:4] = b'RIFF'
        header[4:8] = (32000 + 36).to_bytes(4, 'little') # size
        header[8:12] = b'WAVE'
        header[12:16] = b'fmt '
        header[16:20] = (16).to_bytes(4, 'little') # subchunk1 size
        header[20:22] = (1).to_bytes(2, 'little') # audio format (PCM)
        header[22:24] = (1).to_bytes(2, 'little') # num channels
        header[24:28] = (16000).to_bytes(4, 'little') # sample rate
        header[28:32] = (32000).to_bytes(4, 'little') # byte rate
        header[32:34] = (2).to_bytes(2, 'little') # block align
        header[34:36] = (16).to_bytes(2, 'little') # bits per sample
        header[36:40] = b'data'
        header[40:44] = (32000).to_bytes(4, 'little') # subchunk2 size
        
        # 32000 bytes of silence (zeros)
        data = bytes(32000)
        return bytes(header) + data
