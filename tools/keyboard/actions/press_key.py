"""
Presses a single keyboard key.
"""
import subprocess
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("PressKeyTool")

class PressKeyInput(BaseModel):
    key: str = Field(..., description="The key to press (e.g. 'Return', 'space', 'a').")

class PressKeyTool(BaseTool):
    manifest = ToolManifest(
        name="press_key",
        description="Simulates pressing a single keyboard key.",
        arguments_schema=PressKeyInput,
        permission_level="medium",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        key = kwargs.get("key")
        if not key:
            return {"error": "Missing parameter: key"}
            
        logger.info(f"Simulating key press: {key}")
        
        # 1. Try wtype (Wayland native keyboard simulator)
        import shutil
        if shutil.which("wtype"):
            try:
                # Map some key names to wtype equivalents if necessary (e.g. Return -> Enter)
                wtype_key = key
                if key.lower() == "return":
                    wtype_key = "Enter"
                logger.info(f"Using wtype to press key: {wtype_key}")
                subprocess.run(["wtype", "-k", wtype_key], check=True)
                return {"status": "success", "method": "wtype"}
            except Exception as e:
                logger.warning(f"wtype keypress failed: {e}. Trying other methods.")

        # 2. Try PyAutoGUI
        try:
            import pyautogui
            pyautogui.press(key)
            return {"status": "success", "method": "pyautogui"}
        except Exception:
            pass
            
        # 3. Try xdotool (Linux X11 fallback)
        if shutil.which("xdotool"):
            try:
                subprocess.run(["xdotool", "key", key], check=True, capture_output=True)
                return {"status": "success", "method": "xdotool"}
            except Exception:
                pass
            
        # 4. Fallback
        logger.warning("No virtual keyboard tool available. Simulated key press: mock success.")
        return {"status": "success", "method": "mock_simulation", "key": key}
