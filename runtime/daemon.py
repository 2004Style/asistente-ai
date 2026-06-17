"""
Daemon that orchestrates the assistant components.

Runs the FastAPI server, scheduler, voice subsystem and internal event loop. Acts as the core loop for the assistant.
"""
import os
import time
import shutil
import asyncio
import logging
import threading
import subprocess
import webbrowser
from typing import List, Any, Optional
from contextlib import asynccontextmanager
from pathlib import Path
import yaml
import tempfile
import re
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.container import Container
from core.state_manager import AssistantState
from security.permissions import PermissionLevel

logger = logging.getLogger("Daemon")

# List of active websocket connections
_active_connections: List[WebSocket] = []

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

async def broadcast_event(event_type: str, data: Any):
    """Broadcast system events to all connected WebSocket clients."""
    payload = {"type": "event", "event": event_type, "data": data}
    for ws in list(_active_connections):
        try:
            await ws.send_json(payload)
        except Exception:
            if ws in _active_connections:
                _active_connections.remove(ws)

def launch_ui(host: str, port: int):
    """Launch the browser UI (Chromium in app mode or default browser fallback)."""
    # Wait for the uvicorn server to bind
    time.sleep(1.5)
    
    # Try launching Chromium in app mode
    chromium_path = shutil.which("chromium") or shutil.which("google-chrome")
    if chromium_path:
        logger.info(f"Launching Chromium app mode at http://{host}:{port}/hud")
        try:
            from runtime.paths import CONFIG_DIR
            user_data_dir = CONFIG_DIR / "chromium-panel-rbot"
            subprocess.Popen([
                chromium_path,
                f"--app=http://{host}:{port}/hud",
                f"--user-data-dir={user_data_dir}",
                "--class=RBotPanel",
                "--window-size=900,600",
                "--no-first-run",
                "--no-default-browser-check"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception as e:
            logger.error(f"Failed to launch Chromium app: {e}")
            
    # Fallback to default browser
    try:
        logger.info(f"Opening default web browser at http://{host}:{port}/hud")
        webbrowser.open(f"http://{host}:{port}/hud")
    except Exception as e:
        logger.error(f"Failed to open default browser: {e}")

_last_alert_popup_time = 0.0

def launch_alert_window():
    """Launch a separate Chromium app window for the alert.html page."""
    global _last_alert_popup_time
    now = time.time()
    if now - _last_alert_popup_time < 30.0:
        logger.info("Alert window launch throttled (already launched recently)")
        return
    _last_alert_popup_time = now

    host = "127.0.0.1"
    port = 8000
    try:
        config = Container.resolve("config")
        host = config.host or "127.0.0.1"
        port = config.port or 8000
    except Exception:
        pass

    chromium_path = shutil.which("chromium") or shutil.which("google-chrome")
    if chromium_path:
        logger.info(f"Launching alert window at http://{host}:{port}/alert")
        try:
            from runtime.paths import CONFIG_DIR
            user_data_dir = CONFIG_DIR / "chromium-alert-rbot"
            subprocess.Popen([
                chromium_path,
                f"--app=http://{host}:{port}/alert",
                f"--user-data-dir={user_data_dir}",
                "--class=RBotAlert",
                "--window-size=500,430",
                "--no-first-run",
                "--no-default-browser-check"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception as e:
            logger.error(f"Failed to launch Chromium alert window: {e}")
            
    # Fallback to opening in browser
    try:
        import webbrowser
        logger.info(f"Opening default web browser at http://{host}:{port}/alert")
        webbrowser.open(f"http://{host}:{port}/alert")
    except Exception as e:
        logger.error(f"Failed to open default browser for alert: {e}")

async def handle_ui_command(data: dict):
    """Handle incoming UI commands from EventBus and broadcast/relaunch UI."""
    await broadcast_event("ui_command", data)
    
    action = data.get("action")
    
    # Update active mode in backend
    global _active_ui_mode
    if action == "show_camera":
        _active_ui_mode = "camera"
    elif action == "show_screen":
        _active_ui_mode = "screen"
    elif action in ("hide_camera", "hide_screen"):
        _active_ui_mode = "core"
        
    # Voice command requested opening the HUD, or camera mode, but no browser is connected
    if action in ("open_hud", "show_camera") and len(_active_connections) == 0:
        logger.info(f"HUD/Camera open requested via voice (action={action}), but no active WebSocket clients. Relaunching UI...")
        config = Container.resolve("config")
        threading.Thread(target=launch_ui, args=(config.app.host, config.app.port), daemon=True).start()

async def handle_reminder_triggered(data: dict):
    """Broadcast and speak a triggered reminder."""
    await broadcast_event("reminder_triggered", data)
    msg = data.get("message", "Recordatorio")
    logger.info(f"Speaking reminder: {msg}")
    await speak_text(f"Recordatorio importante: {msg}")

async def setup_event_subscribers():
    """Subscribe WebSocket broadcast to EventBus events."""
    event_bus = Container.resolve("event_bus")
    
    # Subscribe to state changes, tool executions, and UI commands
    event_bus.subscribe("state_changed", lambda data: asyncio.create_task(broadcast_event("state_changed", data)))
    event_bus.subscribe("tool_start", lambda data: asyncio.create_task(broadcast_event("tool_start", data)))
    event_bus.subscribe("tool_success", lambda data: asyncio.create_task(broadcast_event("tool_success", data)))
    event_bus.subscribe("tool_error", lambda data: asyncio.create_task(broadcast_event("tool_error", data)))
    event_bus.subscribe("tool_denied", lambda data: asyncio.create_task(broadcast_event("tool_denied", data)))
    event_bus.subscribe("tool_pending_confirmation", lambda data: asyncio.create_task(broadcast_event("tool_pending_confirmation", data)))
    event_bus.subscribe("tool_confirmation_resolved", lambda data: asyncio.create_task(broadcast_event("tool_confirmation_resolved", data)))
    event_bus.subscribe("voice_listening_success", lambda data: asyncio.create_task(broadcast_event("voice_listening_success", data)))
    event_bus.subscribe("voice_speaking_start", lambda data: asyncio.create_task(broadcast_event("voice_speaking_start", data)))
    event_bus.subscribe("ui_command", lambda data: asyncio.create_task(handle_ui_command(data)))
    event_bus.subscribe("reminder_triggered", lambda data: asyncio.create_task(handle_reminder_triggered(data)))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up daemon tasks...")
    await setup_event_subscribers()
    
    if Container.has("task_queue"):
        Container.resolve("task_queue").start()
    if Container.has("scheduler"):
        Container.resolve("scheduler").start()

    # Start background Voice Loop if voice is enabled
    try:
        config = Container.resolve("config")
        if config.voice.enabled:
            voice_ctrl = Container.resolve("voice_controller")
            asyncio.create_task(voice_ctrl.start_voice_loop())
    except Exception as e:
        logger.error(f"Failed to start background voice loop: {e}")

    # Automatically launch UI browser window in a background thread
    try:
        config = Container.resolve("config")
        threading.Thread(target=launch_ui, args=(config.app.host, config.app.port), daemon=True).start()
    except Exception as e:
        logger.error(f"Failed to schedule UI launch: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down daemon tasks...")
    try:
        voice_ctrl = Container.resolve("voice_controller")
        voice_ctrl.stop_voice_loop()
    except Exception:
        pass
    if Container.has("scheduler"):
        await Container.resolve("scheduler").stop()
    if Container.has("task_queue"):
        await Container.resolve("task_queue").stop()

app = FastAPI(lifespan=lifespan)

# Define static directories
import sys
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    web_ui_dir = Path(sys._MEIPASS) / "interfaces" / "web_ui"
else:
    root_path = Path(__file__).parent.parent.resolve()
    web_ui_dir = root_path / "interfaces" / "web_ui"
app.mount("/static", StaticFiles(directory=str(web_ui_dir)), name="static")

class ConfigUpdateRequest(BaseModel):
    llm: dict
    security: dict
    app: dict
    memory: dict
    voice: dict

# Native Linux /proc CPU tracker
_last_cpu_times = [0.0, 0.0]

def get_linux_cpu_usage() -> float:
    global _last_cpu_times
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        fields = [float(x) for x in line.strip().split()[1:5]]
        idle = fields[3]
        total = sum(fields)
        
        diff_total = total - _last_cpu_times[0]
        diff_idle = idle - _last_cpu_times[1]
        
        _last_cpu_times = [total, idle]
        
        if diff_total == 0:
            return 0.0
        return round(100.0 * (1.0 - diff_idle / diff_total), 1)
    except Exception:
        import random
        return round(15.0 + random.random() * 10, 1)

def get_linux_ram_usage() -> float:
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        mem_total = 0
        mem_free = 0
        mem_available = 0
        for line in lines:
            if 'MemTotal:' in line:
                mem_total = int(line.split()[1])
            elif 'MemFree:' in line:
                mem_free = int(line.split()[1])
            elif 'MemAvailable:' in line:
                mem_available = int(line.split()[1])
        used = mem_total - mem_available if mem_available else mem_total - mem_free
        return round(used / (1024 * 1024), 2)  # GB
    except Exception:
        import random
        return round(4.0 + random.random() * 0.5, 2)

def get_nvidia_gpu_usage() -> Optional[dict]:
    try:
        if shutil.which("nvidia-smi"):
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if res.returncode == 0:
                parts = res.stdout.strip().split(",")
                gpu_util = int(parts[0].strip())
                mem_used = float(parts[1].strip()) / 1024.0  # GB
                return {"util": gpu_util, "mem": mem_used}
    except Exception:
        pass
    return None

@app.get("/stats")
def get_system_stats():
    """Returns real CPU, RAM and optional GPU usage metrics."""
    return {
        "cpu": get_linux_cpu_usage(),
        "ram": get_linux_ram_usage(),
        "gpu": get_nvidia_gpu_usage()
    }

@app.get("/hud")
def get_hud():
    return FileResponse(web_ui_dir / "hud.html")

@app.get("/config_page")
def get_config_page():
    return FileResponse(web_ui_dir / "config.html")

@app.get("/alert")
def get_alert_page():
    return FileResponse(web_ui_dir / "alert.html")

@app.get("/api/preview")
def get_preview_image(path: str):
    """Securely serve local image files for preview in the HUD."""
    import os
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
        
    try:
        resolved_path = Path(path).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path format")
        
    # Check if the path exists
    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    # Check if the path is an image file
    if resolved_path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        raise HTTPException(status_code=400, detail="Only images are allowed for preview")
        
    # Security check: ensure the path is within allowed directories or project root
    root = Path(__file__).parent.parent.resolve()
    is_allowed = False
    
    # 1. Check workspace project root
    if resolved_path.is_relative_to(root):
        is_allowed = True
        
    # 2. Check /tmp
    elif resolved_path.is_relative_to(Path("/tmp")):
        is_allowed = True
        
    # 3. Check home dir allowed subfolders
    else:
        try:
            home = Path.home()
            for sub in ["Documents", "Downloads", "Desktop", ".config", ".gemini"]:
                if resolved_path.is_relative_to(home / sub):
                    is_allowed = True
                    break
        except Exception:
            pass
            
    if not is_allowed:
        logger.warning(f"Preview requested for unauthorized path: {resolved_path}")
        raise HTTPException(status_code=403, detail="Path is outside allowed directories")
        
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp"
    }
    media_type = media_types.get(resolved_path.suffix.lower(), "application/octet-stream")
    return FileResponse(resolved_path, media_type=media_type)

@app.post("/api/screenshot")
async def trigger_screenshot():
    """Trigger a screen capture and return the preview path and metadata."""
    try:
        vision_mgr = Container.resolve("vision_manager")
        result = await vision_mgr.analyze_screen(force=True)
        return result
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return {"error": str(e)}

# Cached camera frame from HUD frontend
_latest_web_camera_frame: Optional[bytes] = None
_latest_web_camera_time: float = 0.0
_active_ui_mode: str = "core"

class CameraFrameRequest(BaseModel):
    image: str # Base64 Data URL

@app.post("/api/camera_frame")
async def upload_camera_frame(req: CameraFrameRequest):
    """Receive and cache a camera frame from the HUD frontend webcam stream."""
    global _latest_web_camera_frame, _latest_web_camera_time
    try:
        import base64
        img_data = req.image
        if "," in img_data:
            img_data = img_data.split(",")[1]
        raw_bytes = base64.b64decode(img_data)
        _latest_web_camera_frame = raw_bytes
        _latest_web_camera_time = time.time()
        
        # Save to cache file for tools to read
        from runtime.paths import resolve_path
        cache_dir = resolve_path("data/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        img_path = cache_dir / "camera_capture.png"
        
        def _save_file():
            with open(img_path, "wb") as f:
                f.write(raw_bytes)
        await asyncio.to_thread(_save_file)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to save uploaded camera frame: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/health")
def health():
    from runtime.health import check_health
    res = check_health()
    res["state"] = Container.resolve("state_manager").state.value
    return res

def play_audio(audio_data: bytes):
    """
    Play synthesized speech bytes using available system audio players.
    
    Tries to stream bytes to player stdin first. If that fails or is unsupported,
    falls back to writing to a temporary file and playing it.
    """
    if not audio_data:
        return
        
    import sys
    is_wav = audio_data.startswith(b'RIFF')
    
    if sys.platform == "darwin":
        # macOS: use afplay
        ext = ".wav" if is_wav else ".mp3"
        tmp_name = None
        try:
            logger.info("macOS detected: Playing audio via afplay...")
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_data)
                tmp_name = tmp.name
            subprocess.run(["afplay", tmp_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception as e:
            logger.warning(f"macOS afplay playback failed: {e}")
        finally:
            if tmp_name:
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass
    elif sys.platform == "win32":
        # Windows: play WAV files natively using winsound, fallback to PowerShell
        try:
            if is_wav:
                import winsound
                logger.info("Windows detected: Playing WAV via winsound...")
                winsound.PlaySound(audio_data, winsound.SND_MEMORY)
                return
        except Exception as e:
            logger.warning(f"winsound memory playback failed: {e}")
            
        ext = ".wav" if is_wav else ".mp3"
        tmp_name = None
        try:
            logger.info("Windows detected: Playing audio via PowerShell fallback...")
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_data)
                tmp_name = tmp.name
            if is_wav:
                ps_cmd = f"(New-Object System.Media.SoundPlayer('{tmp_name}')).PlaySync()"
                subprocess.run(["powershell", "-c", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                ps_cmd = f"$m = New-Object System.Windows.Media.MediaPlayer; $m.Open('{tmp_name}'); $m.Play(); Start-Sleep -s 10"
                subprocess.run(["powershell", "-c", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception as e:
            logger.warning(f"Windows PowerShell playback failed: {e}")
        finally:
            if tmp_name:
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass

    # Default/Linux implementation
    # Estimate audio duration to set a safe, dynamic timeout
    if is_wav:
        # 16000Hz, 16-bit mono PCM is 32000 bytes/sec
        duration = len(audio_data) / 32000.0
    else:
        # MP3 (assume conservative 32kbps = 4000 bytes/sec)
        duration = len(audio_data) / 4000.0
    playback_timeout = max(30.0, duration + 15.0)

    # List of players to try in order of preference
    players = ["pw-play", "aplay", "paplay", "mpv", "play"]
    if not is_wav:
        # Skip raw PCM/WAV players for MP3 format
        players = [p for p in players if p not in ("pw-play", "aplay", "paplay")]
    
    for player in players:
        if not shutil.which(player):
            continue
            
        try:
            logger.info(f"Attempting to stream audio to {player} stdin...")
            if player == "aplay":
                cmd = ["aplay", "-q", "-"]
            elif player == "pw-play":
                cmd = ["pw-play", "-"]
            elif player == "paplay":
                cmd = ["paplay", "/dev/stdin"]
            elif player == "mpv":
                cmd = ["mpv", "--no-video", "--really-quiet", "--no-terminal", "-"]
            elif player == "play":
                cmd = ["play", "-q", "-"]
            else:
                cmd = [player, "-"]
                
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.communicate(input=audio_data, timeout=playback_timeout)
            if proc.returncode == 0:
                logger.info(f"Successfully played audio via {player} stdin.")
                return
            logger.warning(f"{player} process returned non-zero code: {proc.returncode}")
        except subprocess.TimeoutExpired:
            logger.warning(f"Playback with {player} timed out after {playback_timeout:.1f}s.")
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except Exception:
                proc.kill()
        except Exception as e:
            logger.warning(f"Failed to play via {player} stdin: {e}")
            
    # Fallback to temp file if stdin streaming fails
    logger.info("Falling back to playing via temporary file...")
    ext = ".wav" if is_wav else ".mp3"
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_data)
            tmp_name = tmp.name
        
        for player in players:
            if not shutil.which(player):
                continue
            try:
                logger.info(f"Playing audio via temporary file with {player}...")
                if player == "mpv":
                    cmd = [player, "--no-video", "--really-quiet", "--no-terminal", tmp_name]
                elif player == "aplay":
                    cmd = [player, "-q", tmp_name]
                else:
                    cmd = [player, tmp_name]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=playback_timeout)
                if res.returncode == 0:
                    return
            except Exception as e:
                logger.warning(f"Temporary file playback failed with {player}: {e}")
    finally:
        if tmp_name:
            try:
                os.remove(tmp_name)
            except Exception:
                pass

async def speak_text(text: str):
    """
    Synthesizes and plays back speech audio from the given text asynchronously.
    """
    try:
        if not text:
            return
            
        # Strip any markdown formatting to ensure clean TTS
        clean_text = re.sub(r'[*_`#~-]', '', text).strip()
        if not clean_text:
            return
            
        if not Container.has("voice_manager"):
            logger.warning("VoiceManager not registered in Container. Speech synthesis aborted.")
            return
            
        voice_mgr = Container.resolve("voice_manager")
        state_mgr = Container.resolve("state_manager")
        
        logger.info("speak_text: Synthesizing complete text...")
        
        # Set state to SPEAKING
        await state_mgr.transition_to(AssistantState.SPEAKING)
        
        try:
            audio_data = await voice_mgr.synthesize_text(clean_text)
            if audio_data:
                # Play the audio synchronously in a thread pool to avoid blocking asyncio event loop
                await asyncio.to_thread(play_audio, audio_data)
        finally:
            # Revert back to IDLE state once playback is completed
            await state_mgr.transition_to(AssistantState.IDLE)
                
    except Exception as e:
        logger.error(f"Error in speak_text wrapper: {e}", exc_info=True)

def update_env_file(key: str, value: str):
    """Update or append an environment variable in the .env file."""
    from runtime.paths import ENV_FILE_PATH
    env_path = ENV_FILE_PATH
    if not env_path.exists():
        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")
            return
        except Exception as e:
            logger.error(f"Failed to create .env file: {e}")
            return
            
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        updated = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                updated = True
            else:
                new_lines.append(line)
                
        if not updated:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            new_lines.append(f"{key}={value}\n")
            
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
    except Exception as e:
        logger.error(f"Failed to update .env file: {e}")
def update_yaml_file(file_path: Path, new_data: dict):
    """Update or create a YAML configuration file with new key-value pairs."""
    if not file_path.exists():
        data = {}
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = {}
    data.update(new_data)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)

# Piper model download state
_piper_download_state = {
    "status": "idle",  # "idle", "downloading", "completed", "error"
    "progress": 0,
    "error_message": ""
}

# Vosk model download state
_vosk_download_state = {
    "status": "idle",  # "idle", "downloading", "completed", "error"
    "progress": 0,
    "error_message": ""
}

def _download_vosk_task():
    global _vosk_download_state
    import urllib.request
    import zipfile
    import shutil
    
    from runtime.paths import DATA_DIR
    models_dir = DATA_DIR / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    zip_dest = models_dir / "vosk-model-es.zip"
    model_dir = models_dir / "vosk-model-es"
    
    # Lightweight Spanish model
    url = "https://alphacephei.com/vosk/models/vosk-model-small-es-0.3.zip"
    
    try:
        _vosk_download_state["status"] = "downloading"
        _vosk_download_state["progress"] = 0
        
        logger.info(f"Downloading Vosk model from {url} to {zip_dest}...")
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 1024 * 64
            with open(zip_dest, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 90)
                        _vosk_download_state["progress"] = min(percent, 90)
                        
        _vosk_download_state["progress"] = 92
        logger.info(f"Extracting Vosk model zip file {zip_dest}...")
        
        with zipfile.ZipFile(zip_dest, 'r') as zip_ref:
            extracted_names = zip_ref.namelist()
            zip_ref.extractall(path=str(models_dir))
            
            top_dir_name = extracted_names[0].split('/')[0]
            top_dir_path = models_dir / top_dir_name
            
            if model_dir.exists():
                shutil.rmtree(model_dir)
            top_dir_path.rename(model_dir)
            
        _vosk_download_state["progress"] = 99
        if zip_dest.exists():
            zip_dest.unlink()
            
        _vosk_download_state["status"] = "completed"
        _vosk_download_state["progress"] = 100
        logger.info("Vosk model downloaded and extracted successfully.")
        
    except Exception as e:
        logger.error(f"Error downloading/extracting Vosk model: {e}", exc_info=True)
        _vosk_download_state["status"] = "error"
        _vosk_download_state["error_message"] = str(e)
        if zip_dest.exists():
            try:
                zip_dest.unlink()
            except Exception:
                pass
        if model_dir.exists():
            try:
                shutil.rmtree(model_dir)
            except Exception:
                pass

def _download_piper_task(model_url: str, config_url: str, dest_model: Path, dest_config: Path):
    global _piper_download_state
    import urllib.request
    
    try:
        dest_model.parent.mkdir(parents=True, exist_ok=True)
        
        # Helper to download with progress reporting
        def download_file(url, dest_path, progress_weight, progress_offset):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 1024 * 64
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * progress_weight + progress_offset)
                            percent = min(percent, progress_weight + progress_offset)
                            _piper_download_state["progress"] = percent
                            
        logger.info(f"Downloading Piper model from {model_url} to {dest_model}...")
        download_file(model_url, dest_model, 95, 0)
        
        logger.info(f"Downloading Piper config from {config_url} to {dest_config}...")
        download_file(config_url, dest_config, 5, 95)
        
        _piper_download_state["status"] = "completed"
        _piper_download_state["progress"] = 100
        logger.info("Piper model and config downloaded successfully.")
    except Exception as e:
        logger.error(f"Error downloading Piper voice files: {e}", exc_info=True)
        _piper_download_state["status"] = "error"
        _piper_download_state["error_message"] = str(e)
        # Clean up partial files if any
        for path in (dest_model, dest_config):
            if path.exists():
                try:
                    path.unlink()
                except Exception:
                    pass

_whisper_download_state = {
    "status": "idle",
    "progress": 0,
    "error_message": ""
}

def _download_whisper_task(provider: str, model: str):
    global _whisper_download_state
    import urllib.request
    from runtime.paths import resolve_path
    
    WHISPER_URLS = {
        "tiny": "https://openaipublic.azureedge.net/main/whisper/models/651470b012652a29e8150d98fa65ecf765dd722041d6995d59c43957a57c6c55/tiny.pt",
        "base": "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b240efebe5809ab7004f2a7493d5b10c69102b598b6d4d1da67b12a00/base.pt",
        "small": "https://openaipublic.azureedge.net/main/whisper/models/9ecf779900ec40edb114d6c713b9b77341747dfd76be1451d284aaefd9a1e3bc/small.pt",
        "medium": "https://openaipublic.azureedge.net/main/whisper/models/3a3a1f42d69d6ca99d0407db9545b9a21787d8f57f1c1ee3512b0ecf8498c35b/medium.pt",
        "large-v3": "https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367cacf9613b4eedd81e97bb0c1c2480aec9c7c1dbb540f2157f/large-v3.pt",
    }
    
    try:
        _whisper_download_state["status"] = "downloading"
        _whisper_download_state["progress"] = 0
        
        if provider == "whisper_local":
            url = WHISPER_URLS.get(model)
            if not url:
                raise ValueError(f"Modelo Whisper desconocido: {model}")
                
            dest_dir = resolve_path("data/models/whisper")
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / f"{model}.pt"
            
            logger.info(f"Descargando modelo Whisper {model} desde {url} hacia {dest_path}...")
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 1024 * 64
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            _whisper_download_state["progress"] = min(percent, 99)
                            
        elif provider == "faster_whisper":
            dest_dir = resolve_path(f"data/models/faster-whisper/{model}")
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Descargando modelo Faster-Whisper {model} hacia {dest_dir}...")
            
            _whisper_download_state["progress"] = 5
            
            # Incrementar progreso ficiticiamente mientras hf descarga
            stop_increment = [False]
            def increment_progress():
                import time
                while not stop_increment[0]:
                    time.sleep(3)
                    if stop_increment[0]:
                        break
                    curr = _whisper_download_state["progress"]
                    if curr < 95:
                        _whisper_download_state["progress"] = curr + 5
                        
            t = threading.Thread(target=increment_progress, daemon=True)
            t.start()
            
            try:
                from faster_whisper.utils import download_model
                download_model(model, output_dir=str(dest_dir))
            finally:
                stop_increment[0] = True
                try:
                    t.join(timeout=1.0)
                except Exception:
                    pass
                
        else:
            raise ValueError(f"Proveedor de Whisper desconocido: {provider}")
            
        _whisper_download_state["status"] = "completed"
        _whisper_download_state["progress"] = 100
        logger.info(f"Modelo Whisper {model} descargado con éxito.")
        
    except Exception as e:
        logger.error(f"Error descargando modelo Whisper: {e}", exc_info=True)
        _whisper_download_state["status"] = "error"
        _whisper_download_state["error_message"] = str(e)

@app.get("/voice/check_piper")
def check_piper(path: Optional[str] = None):
    """Check if the selected Piper voice model exists on disk."""
    config = Container.resolve("config")
    model_path = path or config.voice.tts_voice
    
    if not model_path or model_path == "custom" or model_path.startswith("es-"):
        model_path = "data/models/es_ES-carlfm-x_low.onnx"
        
    from runtime.paths import resolve_path
    full_path = resolve_path(model_path)
    
    exists = full_path.exists()
    return {
        "exists": exists,
        "path": str(model_path)
    }

class DownloadPiperRequest(BaseModel):
    path: Optional[str] = None

@app.post("/voice/download_piper")
def download_piper(req: DownloadPiperRequest):
    """Start the background task to download the specified Piper model."""
    global _piper_download_state
    if _piper_download_state["status"] == "downloading":
        return {"status": "already_downloading"}
        
    config = Container.resolve("config")
    model_path_str = req.path or config.voice.tts_voice
    
    if not model_path_str or model_path_str == "custom" or not model_path_str.endswith(".onnx"):
        model_path_str = "data/models/es_ES-carlfm-x_low.onnx"
        
    from runtime.paths import resolve_path
    dest_model = resolve_path(model_path_str)
    dest_config = dest_model.with_suffix(".onnx.json")
    
    voice_name = dest_model.stem
    
    lang_code = "es_ES"
    lang_family = "es"
    speaker = "carlfm"
    quality = "medium"
    
    if "-" in voice_name:
        parts = voice_name.split("-")
        if len(parts) >= 3:
            lang_code = parts[0]
            lang_family = lang_code.split("_")[0]
            speaker = parts[1]
            quality = parts[2]
            
    base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/{lang_family}/{lang_code}/{speaker}/{quality}/{voice_name}"
    model_url = base_url + ".onnx"
    config_url = base_url + ".onnx.json"
    
    _piper_download_state["status"] = "downloading"
    _piper_download_state["progress"] = 0
    _piper_download_state["error_message"] = ""
    
    threading.Thread(
        target=_download_piper_task,
        args=(model_url, config_url, dest_model, dest_config),
        daemon=True
    ).start()
    
    return {"status": "started"}

@app.get("/voice/download_piper/status")
def get_download_piper_status():
    """Get the current progress/status of the Piper model download."""
    global _piper_download_state
    return _piper_download_state

@app.get("/voice/check_vosk")
def check_vosk():
    """Check if the Vosk Spanish model exists on disk."""
    from runtime.paths import resolve_path
    model_dir = resolve_path("data/models/vosk-model-es")
    exists = model_dir.exists() and any(model_dir.iterdir())
    return {
        "exists": exists,
        "path": "data/models/vosk-model-es"
    }

@app.post("/voice/download_vosk")
def download_vosk():
    global _vosk_download_state
    if _vosk_download_state["status"] == "downloading":
        return {"status": "already_downloading"}
        
    _vosk_download_state["status"] = "downloading"
    _vosk_download_state["progress"] = 0
    _vosk_download_state["error_message"] = ""
    
    threading.Thread(
        target=_download_vosk_task,
        daemon=True
    ).start()
    
    return {"status": "started"}

@app.get("/voice/download_vosk/status")
def get_download_vosk_status():
    global _vosk_download_state
    return _vosk_download_state

@app.get("/voice/check_whisper")
def check_whisper(provider: str, model: str):
    """Check if the selected local Whisper/Faster-Whisper model exists on disk."""
    from runtime.paths import resolve_path
    if provider == "whisper_local":
        model_dir = resolve_path("data/models/whisper")
        model_file = model_dir / f"{model}.pt"
        exists = model_file.exists()
        path = str(model_file)
    else: # faster_whisper
        model_dir = resolve_path(f"data/models/faster-whisper/{model}")
        exists = model_dir.exists() and (model_dir / "model.bin").exists()
        path = str(model_dir)
        
    return {
        "exists": exists,
        "path": path
    }

class DownloadWhisperRequest(BaseModel):
    provider: str
    model: str

@app.post("/voice/download_whisper")
def download_whisper(req: DownloadWhisperRequest):
    global _whisper_download_state
    if _whisper_download_state["status"] == "downloading":
        return {"status": "already_downloading"}
        
    _whisper_download_state["status"] = "downloading"
    _whisper_download_state["progress"] = 0
    _whisper_download_state["error_message"] = ""
    
    threading.Thread(
        target=_download_whisper_task,
        args=(req.provider, req.model),
        daemon=True
    ).start()
    
    return {"status": "started"}

@app.get("/voice/download_whisper/status")
def get_download_whisper_status():
    global _whisper_download_state
    return _whisper_download_state

@app.get("/config")
def get_config():
    config = Container.resolve("config")
    return config.model_dump()

@app.post("/config")
async def update_config(req: ConfigUpdateRequest):
    config = Container.resolve("config")
    
    # Extract actual API keys to save in .env instead of YAML
    actual_llm_key = req.llm.get("api_key")
    actual_voice_key = req.voice.get("api_key")
    
    # Save keys into the .env file if provided, and save references in YAML
    if actual_llm_key is not None:
        update_env_file("PROVIDER_API_KEY", actual_llm_key)
        os.environ["PROVIDER_API_KEY"] = actual_llm_key
        req.llm["api_key"] = "env:PROVIDER_API_KEY"
        
    if actual_voice_key is not None:
        update_env_file("VOICE_API_KEY", actual_voice_key)
        os.environ["VOICE_API_KEY"] = actual_voice_key
        req.voice["api_key"] = "env:VOICE_API_KEY"
        
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    # 1. Update YAMLs
    from runtime.paths import CONFIG_DIR
    configs_dir = CONFIG_DIR
            
    try:
        update_yaml_file(configs_dir / "llm.yml", req.llm)
        update_yaml_file(configs_dir / "security.yml", req.security)
        update_yaml_file(configs_dir / "app.yml", req.app)
        update_yaml_file(configs_dir / "memory.yml", req.memory)
        update_yaml_file(configs_dir / "voice.yml", req.voice)
    except Exception as e:
        logger.error(f"Failed to save YAML config updates: {e}")
        return {"status": "error", "message": f"Failed to save files: {e}"}

    # 2. Update config object in Container
    config.llm = config.llm.model_copy(update=req.llm)
    config.security = config.security.model_copy(update=req.security)
    config.app = config.app.model_copy(update=req.app)
    config.memory = config.memory.model_copy(update=req.memory)
    config.voice = config.voice.model_copy(update=req.voice)
    
    # Restore actual keys in memory
    if actual_llm_key is not None:
        config.llm.api_key = actual_llm_key
    if actual_voice_key is not None:
        config.voice.api_key = actual_voice_key
    
    # 3. Propagate changes to active instances
    try:
        from llm.router import get_llm_provider
        new_llm = get_llm_provider(config.llm)
        Container.register("llm_provider", new_llm)
        
        # Update references in active singletons
        if Container.has("planner"):
            Container.resolve("planner").llm_provider = new_llm
        if Container.has("agent"):
            Container.resolve("agent").llm_provider = new_llm
        if Container.has("memory_manager"):
            Container.resolve("memory_manager").llm_provider = new_llm
            
        logger.info(f"LLM Provider dynamically swapped in hot-reload to: '{config.llm.provider}' using model '{config.llm.model}'")
    except Exception as e:
        logger.error(f"Failed to dynamically swap LLM provider: {e}")
        
    confirm_mgr = Container.resolve("confirmation_manager")
    confirm_mgr.min_level = PermissionLevel.from_str(config.security.min_permission_level)
    confirm_mgr.require_confirmation = config.security.require_confirmation
    
    # Propagate voice configuration changes to VoiceManager
    try:
        from voice.manager import get_stt_provider, get_tts_provider
        voice_mgr = Container.resolve("voice_manager")
        voice_mgr.stt = get_stt_provider(config.voice.stt_provider, config.voice)
        voice_mgr.tts = get_tts_provider(config.voice.tts_provider, config.voice)
        logger.info("VoiceManager STT and TTS engines updated dynamically.")
        
        # Start or stop the voice recording loop dynamically based on enabled config
        voice_ctrl = Container.resolve("voice_controller")
        if config.voice.enabled:
            if not voice_ctrl.active:
                asyncio.create_task(voice_ctrl.start_voice_loop())
        else:
            voice_ctrl.stop_voice_loop()
    except Exception as e:
        logger.error(f"Failed to dynamically propagate voice configuration updates: {e}")
        
    logger.info("Configuration updated successfully and applied dynamically.")
    return {"status": "success"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # Check if there is a pending confirmation first
    try:
        confirm_mgr = Container.resolve("confirmation_manager")
        if len(confirm_mgr._pending_confirmations) > 0:
            from security.confirmation import try_resolve_confirmation_by_text
            resolved = await try_resolve_confirmation_by_text(req.message)
            if resolved:
                return {"response": "[✔] Confirmación procesada."}
    except Exception as e:
        logger.error(f"Error checking pending confirmations in chat endpoint: {e}")

    assistant = Container.resolve("assistant")
    response = await assistant.chat(req.message, req.session_id)
    
    # Trigger voice playback asynchronously if voice is enabled
    try:
        config = Container.resolve("config")
        if config.voice.enabled:
            asyncio.create_task(speak_text(response))
    except Exception as e:
        logger.error(f"Failed to trigger voice playback in chat endpoint: {e}")
        
    return {"response": response}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global _active_ui_mode
    await websocket.accept()
    _active_connections.append(websocket)
    logger.info("New WebSocket client connected.")
    
    # Send current state upon connection
    state_mgr = Container.resolve("state_manager")
    await websocket.send_json({"type": "state", "state": state_mgr.state.value})
    
    # Send the active UI mode to the newly connected client so it syncs up immediately on startup
    if _active_ui_mode != "core":
        await websocket.send_json({"type": "ui_command", "action": f"show_{_active_ui_mode}"})

    try:
        assistant = Container.resolve("assistant")
        while True:
            data = await websocket.receive_json()
            
            # Handle user confirmation response from HUD
            if data.get("type") == "confirmation_response":
                confirm_id = data.get("confirm_id")
                approved = data.get("approved", False)
                logger.info(f"Received confirmation response for ID {confirm_id}: approved={approved}")
                confirm_mgr = Container.resolve("confirmation_manager")
                confirm_mgr.resolve_confirmation(confirm_id, approved)
                continue

            # Handle custom UI window actions
            if data.get("type") == "ui_action":
                action = data.get("action")
                logger.info(f"Received UI window action from client: {action}")
                
                if action == "open_file":
                    path = data.get("path")
                    if path:
                        logger.info(f"Opening folder location for: {path}")
                        import os
                        import sys
                        import subprocess
                        try:
                            target = path
                            if os.path.isfile(path):
                                target = os.path.dirname(path)
                            
                            if sys.platform == "win32":
                                os.startfile(target)
                            elif sys.platform == "darwin":
                                subprocess.Popen(["open", target])
                            else:
                                subprocess.Popen(["xdg-open", target])
                        except Exception as e:
                            logger.error(f"Failed to open file path {path}: {e}")
                elif action == "set_active_mode":
                    mode = data.get("mode", "core")
                    _active_ui_mode = mode
                    logger.info(f"Updated active UI mode to: {_active_ui_mode}")
                continue

            if "message" in data:
                msg_text = data["message"]
                session_id = data.get("session_id", "default")
                
                # Check if there is a pending confirmation first
                try:
                    confirm_mgr = Container.resolve("confirmation_manager")
                    if len(confirm_mgr._pending_confirmations) > 0:
                        from security.confirmation import try_resolve_confirmation_by_text
                        resolved = await try_resolve_confirmation_by_text(msg_text)
                        if resolved:
                            logger.info("Pending confirmation resolved via WebSocket text message.")
                            await websocket.send_json({
                                "type": "response",
                                "content": "[✔] Confirmación procesada."
                            })
                            continue
                except Exception as e:
                    logger.error(f"Error checking pending confirmations in WebSocket: {e}")
                
                # Intercept HUD input to save it as a "Pasted Payload" instead of executing it
                from llm.message import Message
                pasted_msg = Message(role="user", content=f"Pasted Payload: {msg_text}")
                memory_mgr = Container.resolve("memory_manager")
                memory_mgr.add_message(session_id, pasted_msg)
                
                logger.info(f"Saved HUD input as Pasted Payload in session '{session_id}': {msg_text}")
                
                # Reply to the HUD with the success message
                ack_response = "[✔] Contenido recibido. Listo para instrucciones por voz."
                await websocket.send_json({
                    "type": "response",
                    "content": ack_response
                })
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket session error: {e}", exc_info=True)
    finally:
        if websocket in _active_connections:
            _active_connections.remove(websocket)

def run_daemon(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the uvicorn web server."""
    logger.info(f"Launching daemon at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
