"""
High‑level controller for voice input and output.

Listens to microphone input, detects speech activity (VAD), transcribes via STT,
sends text to the assistant, and synthesizes/plays the response.
"""
import asyncio
import logging
import math
import re
from typing import Optional
from app.container import Container
from core.state_manager import AssistantState

logger = logging.getLogger("VoiceController")

class VoiceController:
    def __init__(self):
        self.active = False
        self.pyaudio = None
        self.audio_stream = None
        self._loop_task = None

    def _init_audio(self) -> bool:
        if self.pyaudio is not None:
            return True
        try:
            import pyaudio
            self.pyaudio = pyaudio.PyAudio()
            return True
        except ImportError:
            logger.warning("pyaudio is not installed. VoiceController cannot start microphone loop.")
            return False

    async def start_voice_loop(self):
        """Starts a background loop listening to microphone input."""
        if self.active:
            return
            
        self.active = True
        logger.info("Starting background voice loop...")
        
        has_audio = self._init_audio()
        if not has_audio:
            self.active = False
            return

        try:
            import pyaudio
            # 16000Hz, 1 channel, 16-bit PCM (standard for STT models)
            self.audio_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1600 # 0.1s chunks
            )
            logger.info("Microphone stream opened. Listening for speech activity...")
            
            # Start VAD recording loop
            self._loop_task = asyncio.create_task(self._recording_loop())
        except Exception as e:
            logger.error(f"Error starting microphone stream: {e}")
            self.active = False

    def stop_voice_loop(self):
        self.active = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            self._loop_task = None
            
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None
        if self.pyaudio:
            try:
                self.pyaudio.terminate()
            except Exception:
                pass
            self.pyaudio = None
    async def _recording_loop(self):
        """VAD loop to record audio chunks when speaking, and process them when silence is detected."""
        import pyaudio
        import struct
        import math

        # VAD Parameters
        noise_floor = 200.0   # Initial background noise floor estimate
        base_threshold = 750  # Minimum threshold to avoid triggering on background noise/fans
        silence_timeout = 0.8 # seconds of silence to trigger end-of-speech
        max_duration = 15.0   # max recording duration in seconds
        
        audio_buffer = []
        is_recording = False
        silence_timer = 0.0
        recording_timer = 0.0
        speech_chunks = 0     # Count chunks where actual speech was active
        was_speaking = False
        was_purging = False

        while self.active:
            try:
                # 1. Resolve State
                try:
                    state_mgr = Container.resolve("state_manager")
                    current_state = state_mgr.state
                except Exception:
                    current_state = AssistantState.IDLE

                is_waiting_confirm = False
                try:
                    confirm_mgr = Container.resolve("confirmation_manager")
                    is_waiting_confirm = len(confirm_mgr._pending_confirmations) > 0
                except Exception:
                    pass

                # If the assistant is speaking, planning, or executing (and not waiting for confirmation),
                # we must purge all available frames from the stream and not record.
                should_purge = (current_state == AssistantState.SPEAKING) or (
                    current_state in (AssistantState.PLANNING, AssistantState.EXECUTING) and not is_waiting_confirm
                )

                if current_state == AssistantState.SPEAKING:
                    was_speaking = True

                if should_purge:
                    is_recording = False
                    audio_buffer = []
                    speech_chunks = 0
                    was_purging = True
                    
                    if self.audio_stream and self.audio_stream.is_active():
                        try:
                            available = self.audio_stream.get_read_available()
                            if available > 0:
                                self.audio_stream.read(available, exception_on_overflow=False)
                        except Exception:
                            pass
                    
                    await asyncio.sleep(0.1)
                    continue

                # 2. Transformed state check: if we just transitioned from purging, clear buffer and cooldown
                if was_purging:
                    was_purging = False
                    logger.info("Transitioned from non-listening to listening state. Purging stream...")
                    if self.audio_stream and self.audio_stream.is_active():
                        try:
                            available = self.audio_stream.get_read_available()
                            if available > 0:
                                self.audio_stream.read(available, exception_on_overflow=False)
                        except Exception:
                            pass
                    
                    if was_speaking:
                        was_speaking = False
                        # Sleep 300ms to allow audio playback tail to completely settle
                        await asyncio.sleep(0.3)
                    continue

                # 3. Read 0.1s of audio data from stream (non-blocking read)
                if self.audio_stream is None or not self.audio_stream.is_active():
                    await asyncio.sleep(0.1)
                    continue

                # To prevent blocking, we check how many frames are available to read
                try:
                    available = self.audio_stream.get_read_available()
                except Exception:
                    available = 0
                    
                if available < 1600:
                    await asyncio.sleep(0.05)
                    continue
                    
                try:
                    data = self.audio_stream.read(1600, exception_on_overflow=False)
                except Exception as e:
                    logger.warning(f"Failed to read from audio stream: {e}")
                    await asyncio.sleep(0.05)
                    continue
                    
                if not data:
                    await asyncio.sleep(0.05)
                    continue

                # Compute RMS volume to detect speech activity in pure Python
                count = len(data) // 2
                if count > 0:
                    shorts = struct.unpack(f"<{count}h", data)
                    sum_squares = sum(x * x for x in shorts)
                    rms = math.sqrt(sum_squares / count)
                else:
                    rms = 0
                
                # Update adaptive noise floor slowly when not recording
                if not is_recording:
                    # Slow exponential moving average to adapt to room noise floor
                    noise_floor = 0.98 * noise_floor + 0.02 * rms
                    threshold = max(base_threshold, noise_floor * 2.2)
                else:
                    # Keep using the threshold established before recording started
                    pass
                
                # Check if speaking
                is_active_speech = rms > threshold

                if is_recording:
                    audio_buffer.append(data)
                    recording_timer += 0.1
                    
                    if not is_active_speech:
                        silence_timer += 0.1
                    else:
                        silence_timer = 0.0 # speech heard, reset silence timer
                        speech_chunks += 1
                        
                    # Stop recording if silence timeout or max duration is reached
                    if silence_timer >= silence_timeout or recording_timer >= max_duration:
                        # Only process if we have a minimum duration of actual speech chunks
                        # 4 chunks = 0.4 seconds of cumulative active speech (ignores quick transient clicks/coughs)
                        if speech_chunks >= 4:
                            logger.info(f"Speech finished ({speech_chunks} active chunks). Processing recorded audio...")
                            recorded_audio = b"".join(audio_buffer)
                            # Process audio in background so we don't block the microphone loop
                            asyncio.create_task(self.process_audio_response(recorded_audio))
                        else:
                            logger.info(f"Discarding recording: only {speech_chunks} active speech chunks (likely noise/click).")
                        
                        # Reset recording state
                        is_recording = False
                        audio_buffer = []
                        speech_chunks = 0
                else:
                    if is_active_speech:
                        logger.info(f"Speech detected (RMS: {rms:.1f} > Thresh: {threshold:.1f}). Starting recording...")
                        is_recording = True
                        audio_buffer = [data]
                        silence_timer = 0.0
                        recording_timer = 0.1
                        speech_chunks = 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in VAD recording loop: {e}")
                await asyncio.sleep(0.1)

    async def process_audio_response(self, audio_data: bytes):
        """Send audio to STT, run chat assistant, and speak the final response."""
        try:
            voice_mgr = Container.resolve("voice_manager")
            assistant = Container.resolve("assistant")
            
            # 1. Transcribe
            user_text = await voice_mgr.transcribe_audio(audio_data)
            if not user_text:
                return

            # Clean common Whisper/STT hallucinations or noise artifacts
            import re
            clean_text = user_text.lower().strip()
            clean_text = re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()?¿¡]', '', clean_text).strip()
            
            ignored_phrases = {
                "", "gracias", "gracias por ver", "gracias por ver este video", "gracias por ver el video",
                "gracias por ver este vídeo", "gracias por ver el vídeo", "subtítulos por amara.org",
                "subtítulos por la comunidad de amara.org", "blank_audio", "[blank_audio]", "gracias.",
                "gracias por su atención", "continuará", "todos los derechos reservados", "suscríbete",
                "suscríbete a mi canal", "amaraorg", "amara", "transcripción por amara"
            }
            if clean_text in ignored_phrases or len(clean_text) < 2:
                logger.warning(f"Ignored false speech transcription: '{user_text}'")
                return

            logger.info(f"User voice input: '{user_text}'")

            # 2. Intercept if there is a pending confirmation
            try:
                confirm_mgr = Container.resolve("confirmation_manager")
                if len(confirm_mgr._pending_confirmations) > 0:
                    from security.confirmation import try_resolve_confirmation_by_text
                    resolved = await try_resolve_confirmation_by_text(user_text)
                    if resolved:
                        logger.info("Pending confirmation resolved via voice text.")
                        return  # Resumed task will handle speaking and finishing the request
            except Exception as e:
                logger.error(f"Failed to check/resolve pending confirmation via voice: {e}")

            # 3. Converse (this triggers Assistant thinking -> executes tool if needed -> returns final text)
            # Daemon will automatically trigger async speech synthesis from chat_endpoint/websocket
            # But here we are calling assistant.chat directly from the voice loop, so we should speak it!
            response_text = await assistant.chat(user_text)
            
            # 4. Speak the final response
            from runtime.daemon import speak_text
            if response_text:
                await speak_text(response_text)

        except Exception as e:
            logger.error(f"Error processing voice response: {e}", exc_info=True)

    async def trigger_push_to_talk(self, mock_audio: Optional[bytes] = None) -> Optional[bytes]:
        """Trigger a single recording session, transcribe, run chat assistant, and return TTS audio response."""
        voice_mgr = Container.resolve("voice_manager")
        assistant = Container.resolve("assistant")
        state_mgr = Container.resolve("state_manager")

        audio_input = mock_audio or b"\x00" * 32000 # 1 second of mock silence
        
        try:
            user_text = await voice_mgr.transcribe_audio(audio_input)
            if not user_text:
                logger.warning("No speech detected.")
                return None

            response_text = await assistant.chat(user_text)
            audio_output = await voice_mgr.synthesize_text(response_text)
            return audio_output
        finally:
            try:
                await state_mgr.transition_to(AssistantState.IDLE)
            except Exception:
                pass
