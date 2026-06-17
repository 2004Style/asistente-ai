"""
Manages user confirmation prompts for high-risk actions.
"""
import sys
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional
from security.permissions import PermissionLevel
from core.events import EventBus

logger = logging.getLogger("ConfirmationManager")

class ConfirmationRequiredError(Exception):
    def __init__(self, tool_name: str, arguments: Dict[str, Any], permission_level: PermissionLevel):
        self.tool_name = tool_name
        self.arguments = arguments
        self.permission_level = permission_level
        super().__init__(f"Confirmation required for tool '{tool_name}' ({permission_level.name})")

class ConfirmationManager:
    def __init__(self, min_permission_level: str = "medium", require_confirmation: bool = True, event_bus: Optional[EventBus] = None):
        self.min_level = PermissionLevel.from_str(min_permission_level)
        self.require_confirmation = require_confirmation
        self.event_bus = event_bus
        self._pending_confirmations: Dict[str, asyncio.Future] = {}

    def needs_confirmation(self, tool_level: str, tool_name: Optional[str] = None) -> bool:
        """Verify if a tool requires explicit user confirmation."""
        if not self.require_confirmation:
            return False
        if tool_name:
            try:
                from app.container import Container
                registry = Container.resolve("tool_registry")
                tool = registry.get_tool(tool_name)
                if tool and getattr(tool.manifest, "risk", "") == "read_only":
                    return False
            except Exception:
                pass
        level = PermissionLevel.from_str(tool_level)
        return level >= self.min_level

    async def request_confirmation(self, tool_name: str, arguments: Dict[str, Any], tool_level: str) -> bool:
        """Request confirmation. Suspends execution waiting for a response in non-TTY environments."""
        if not self.needs_confirmation(tool_level, tool_name):
            return True

        logger.info(f"Requesting confirmation for tool={tool_name} (level={tool_level})")

        has_web_clients = False
        try:
            from runtime.daemon import _active_connections
            has_web_clients = len(_active_connections) > 0
        except Exception:
            pass

        # Send a system desktop notification on Linux to alert the user
        if sys.platform == "linux":
            try:
                import shutil
                if shutil.which("notify-send"):
                    subprocess.Popen([
                        "notify-send", 
                        "-u", "critical", 
                        "-a", "rbot",
                        "⚠️ Confirmación Requerida", 
                        f"La herramienta '{tool_name}' requiere tu aprobación en el HUD."
                    ])
            except Exception as e:
                logger.debug(f"Failed to send system notification: {e}")

        # If stdin is a TTY and no web clients are connected, ask in the terminal
        if sys.stdin.isatty() and not has_web_clients:
            print(f"\n⚠️  [SEGURIDAD] El asistente quiere ejecutar la herramienta: '{tool_name}'")
            print(f"   Argumentos: {arguments}")
            print(f"   Nivel de riesgo: {tool_level}")
            
            def _prompt():
                try:
                    ans = input("   ¿Permitir ejecución? [s/N]: ").strip().lower()
                    return ans in ("s", "si", "y", "yes")
                except Exception:
                    return False
            
            approved = await asyncio.to_thread(_prompt)
            return approved

        # Asynchronous suspension for GUI/Web interface
        import time
        confirm_id = f"conf_{int(time.time() * 1000)}"
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._pending_confirmations[confirm_id] = fut

        # Speak the request if voice is enabled
        try:
            config = Container.resolve("config")
            if config.voice.enabled:
                from runtime.daemon import speak_text
                tool_friendly_names = {
                    "inspect_camera": "usar la cámara web",
                    "inspect_screen": "tomar una captura de pantalla",
                    "run_command": "ejecutar un comando en la terminal",
                    "write_file": "escribir o modificar un archivo",
                    "delete_file": "eliminar un archivo",
                    "close_app": "cerrar una aplicación",
                    "open_app": "abrir una aplicación"
                }
                friendly_tool = tool_friendly_names.get(tool_name, f"ejecutar la herramienta {tool_name}")
                speak_prompt = f"El asistente requiere tu confirmación para {friendly_tool}. ¿Deseas autorizar esta acción?"
                asyncio.create_task(speak_text(speak_prompt))
        except Exception as e:
            logger.debug(f"Failed to speak confirmation request: {e}")

        if self.event_bus:
            # Publish event to notify WebSocket clients
            await self.event_bus.publish("tool_pending_confirmation", {
                "confirm_id": confirm_id,
                "tool": tool_name,
                "arguments": arguments,
                "level": tool_level
            })

        logger.info(f"Execution suspended. Waiting for confirmation ID: {confirm_id}")
        try:
            approved = await fut
            logger.info(f"Confirmation ID {confirm_id} resolved with approved={approved}")
            if self.event_bus:
                await self.event_bus.publish("tool_confirmation_resolved", {
                    "confirm_id": confirm_id,
                    "approved": approved
                })
            return approved
        finally:
            self._pending_confirmations.pop(confirm_id, None)

    def resolve_confirmation(self, confirm_id: str, approved: bool) -> bool:
        """Resolve a pending confirmation future."""
        if confirm_id in self._pending_confirmations:
            fut = self._pending_confirmations[confirm_id]
            if not fut.done():
                fut.set_result(approved)
                return True
        return False

async def try_resolve_confirmation_by_text(text: str) -> bool:
    """
    Attempts to match a user's text message to affirmation/negation keywords
    to resolve any pending confirmation. Returns True if a confirmation was resolved.
    """
    from app.container import Container
    try:
        confirm_mgr = Container.resolve("confirmation_manager")
    except Exception:
        return False

    if not confirm_mgr or not confirm_mgr._pending_confirmations:
        return False

    # Get the oldest pending confirmation ID
    confirm_ids = list(confirm_mgr._pending_confirmations.keys())
    if not confirm_ids:
        return False
    confirm_id = confirm_ids[0]

    clean_text = text.lower().strip()
    # Remove basic punctuation
    import re
    clean_text = re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()?¿¡]', '', clean_text).strip()

    affirmations = {
        "sí", "si", "yes", "y", "ok", "okay", "claro", "procede", "proceder", 
        "aprobar", "aprobado", "aprueba", "dale", "afirmativo", "aceptar", "acepto", 
        "está bien", "esta bien", "ejecutar", "ejecuta", "autorizo", "autorizar"
    }

    negations = {
        "no", "cancelar", "cancela", "cancel", "n", "rechazar", "rechazado", "rechaza", 
        "no aprobar", "no apruebo", "no procede", "no proceder", "alto", "detener", 
        "detén", "deten", "parar", "para"
    }

    # Check for exact word matches or close matches
    words = clean_text.split()
    is_affirmative = any(word in affirmations for word in words) or clean_text in affirmations
    is_negative = any(word in negations for word in words) or clean_text in negations

    if is_affirmative:
        confirm_mgr.resolve_confirmation(confirm_id, True)
        return True
    elif is_negative:
        confirm_mgr.resolve_confirmation(confirm_id, False)
        return True

    return False

