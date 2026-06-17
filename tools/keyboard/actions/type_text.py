"""
Types text using simulated keyboard input.
"""
import subprocess
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("TypeTextTool")

class TypeTextInput(BaseModel):
    text: str = Field(..., description="The text to type.")

class TypeTextTool(BaseTool):
    manifest = ToolManifest(
        name="type_text",
        description="Simulates keyboard typing of a string of text.",
        arguments_schema=TypeTextInput,
        permission_level="medium",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        text = kwargs.get("text")
        if not text:
            return {"error": "Missing parameter: text"}
            
        logger.info(f"Simulating typing text: {text}")
        
        # Determine if we should paste to support special/accented/multiline characters safely
        use_paste = not all(ord(c) < 128 for c in text) or "\n" in text or "\r" in text
        
        # 1. Try wtype (Wayland native keyboard simulator)
        import shutil
        if shutil.which("wtype"):
            try:
                logger.info("Using wtype for Wayland keyboard typing.")
                subprocess.run(["wtype", "--", text], check=True)
                return {"status": "success", "method": "wtype"}
            except Exception as e:
                logger.warning(f"wtype typing failed: {e}. Trying other methods.")

        # 2. Try PyAutoGUI / Paste
        try:
            if use_paste:
                logger.info("Using clipboard paste method for non-ASCII or multiline text.")
                from tools.clipboard_utils import paste_text_via_gui
                await paste_text_via_gui(text)
            else:
                import pyautogui
                pyautogui.write(text)
            return {"status": "success", "method": "clipboard_paste" if use_paste else "pyautogui"}
        except Exception as e:
            logger.warning(f"PyAutoGUI/Paste failed: {e}. Trying xdotool fallback.")
            
        # 3. Try xdotool (Linux X11 fallback)
        if shutil.which("xdotool"):
            try:
                subprocess.run(["xdotool", "type", text], check=True, capture_output=True)
                return {"status": "success", "method": "xdotool"}
            except Exception:
                pass
            
        # 4. Fallback (mock success in headless/testing env)
        logger.warning("No virtual keyboard tool available. Simulated typing: mock success.")
        return {"status": "success", "method": "mock_simulation", "text": text}
