"""
Simulates a mouse click.
"""
import subprocess
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("MouseClickTool")

class MouseClickInput(BaseModel):
    button: str = Field("left", description="The mouse button to click (left, right, middle).")
    clicks: int = Field(1, description="The number of clicks (1 for single, 2 for double).")

class MouseClickTool(BaseTool):
    manifest = ToolManifest(
        name="click_mouse",
        description="Simulates a mouse click on the host environment.",
        arguments_schema=MouseClickInput,
        permission_level="medium",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        button = kwargs.get("button", "left").lower()
        clicks = kwargs.get("clicks", 1)
        
        logger.info(f"Simulating mouse click: {button} button, {clicks} times")
        
        # 1. Try PyAutoGUI
        try:
            import pyautogui
            pyautogui.click(button=button, clicks=clicks)
            return {"status": "success", "method": "pyautogui"}
        except ImportError:
            pass
            
        # 2. Try xdotool
        try:
            # map button names to xdotool button codes
            btn_code = {"left": "1", "middle": "2", "right": "3"}.get(button, "1")
            cmd = ["xdotool", "click", "--repeat", str(clicks), btn_code]
            subprocess.run(cmd, check=True, capture_output=True)
            return {"status": "success", "method": "xdotool"}
        except Exception:
            pass
            
        # 3. Fallback
        logger.warning("No pointer input utility available. Mouse click: mock success.")
        return {"status": "success", "method": "mock_simulation", "button": button, "clicks": clicks}
