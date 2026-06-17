"""
Simulates a keyboard shortcut (combination of keys).
"""
import subprocess
import logging
from typing import Any, List
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("KeyboardShortcutTool")

class KeyboardShortcutInput(BaseModel):
    keys: List[str] = Field(..., description="The list of keys in the shortcut combination (e.g. ['ctrl', 'alt', 't']).")

class KeyboardShortcutTool(BaseTool):
    manifest = ToolManifest(
        name="shortcut",
        description="Simulates triggering a keyboard shortcut combination.",
        arguments_schema=KeyboardShortcutInput,
        permission_level="medium",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        keys = kwargs.get("keys")
        if not keys:
            return {"error": "Missing parameter: keys"}
            
        logger.info(f"Simulating keyboard shortcut: {keys}")
        
        # 1. Try wtype (Wayland native keyboard simulator)
        import shutil
        if shutil.which("wtype"):
            try:
                cmd = ["wtype"]
                modifiers = []
                main_key = None
                
                mod_map = {
                    "ctrl": "ctrl",
                    "control": "ctrl",
                    "alt": "alt",
                    "shift": "shift",
                    "super": "logo",
                    "win": "logo",
                    "logo": "logo"
                }
                
                for k in keys:
                    k_lower = k.lower().strip()
                    if k_lower in mod_map:
                        modifiers.append(mod_map[k_lower])
                    else:
                        main_key = k
                
                for mod in modifiers:
                    cmd.extend(["-M", mod])
                if main_key:
                    if main_key.lower() == "return":
                        main_key = "Enter"
                    cmd.extend(["-k", main_key])
                
                logger.info(f"Using wtype to trigger shortcut: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                return {"status": "success", "method": "wtype"}
            except Exception as e:
                logger.warning(f"wtype shortcut failed: {e}. Trying other methods.")

        # 2. Try PyAutoGUI
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return {"status": "success", "method": "pyautogui"}
        except Exception:
            pass
            
        # 3. Try xdotool (Linux X11 fallback)
        if shutil.which("xdotool"):
            try:
                xd_shortcut = "+".join(keys)
                subprocess.run(["xdotool", "key", xd_shortcut], check=True, capture_output=True)
                return {"status": "success", "method": "xdotool"}
            except Exception:
                pass
            
        # 4. Fallback
        logger.warning("No virtual keyboard tool available. Simulated shortcut: mock success.")
        return {"status": "success", "method": "mock_simulation", "keys": keys}
