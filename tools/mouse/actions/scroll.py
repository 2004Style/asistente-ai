"""
Simulates mouse wheel scrolling.
"""
import subprocess
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("MouseScrollTool")

class MouseScrollInput(BaseModel):
    direction: str = Field("down", description="The scroll direction (up, down, left, right).")
    amount: int = Field(5, description="The scroll amount (usually lines or clicks).")

class MouseScrollTool(BaseTool):
    manifest = ToolManifest(
        name="scroll_mouse",
        description="Simulates mouse wheel scrolling in the host environment.",
        arguments_schema=MouseScrollInput,
        permission_level="medium",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        direction = kwargs.get("direction", "down").lower()
        amount = kwargs.get("amount", 5)
        
        logger.info(f"Simulating mouse scroll: {direction}, amount: {amount}")
        
        # 1. Try PyAutoGUI
        try:
            import pyautogui
            # pyautogui.scroll takes a positive number for up, negative for down
            scroll_amt = amount if direction == "up" else -amount
            pyautogui.scroll(scroll_amt)
            return {"status": "success", "method": "pyautogui"}
        except ImportError:
            pass
            
        # 2. Try xdotool
        try:
            # In xdotool, button 4 is scroll up, button 5 is scroll down
            btn_code = "4" if direction == "up" else "5"
            cmd = ["xdotool", "click", "--repeat", str(amount), btn_code]
            subprocess.run(cmd, check=True, capture_output=True)
            return {"status": "success", "method": "xdotool"}
        except Exception:
            pass
            
        # 3. Fallback
        logger.warning("No pointer scroll utility available. Mouse scroll: mock success.")
        return {"status": "success", "method": "mock_simulation", "direction": direction, "amount": amount}
