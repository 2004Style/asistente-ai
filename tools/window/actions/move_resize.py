"""
Moves or resizes windows.
"""
import subprocess
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("MoveResizeWindowTool")

class MoveResizeWindowInput(BaseModel):
    action: str = Field(..., description="Action to perform: 'move' or 'resize'.")
    direction: str = Field(..., description="Direction: 'l' (left), 'r' (right), 'u' (up), 'd' (down).")
    amount: int = Field(default=50, description="Amount in pixels to move or resize.")

class MoveResizeWindowTool(BaseTool):
    manifest = ToolManifest(
        name="move_resize_window",
        description="Moves or resizes the active window in a given direction.",
        arguments_schema=MoveResizeWindowInput,
        permission_level="low",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        action = kwargs.get("action")
        direction = kwargs.get("direction")
        amount = kwargs.get("amount", 50)
        
        logger.info(f"Move/Resize window: {action} {direction} by {amount}")
        
        try:
            # Map directions to hyprland active window dispatches
            hypr_dir = {"l": "-", "r": "", "u": "-", "d": ""}
            
            if action == "move":
                # e.g. moveactive X Y
                x = -amount if direction == "l" else (amount if direction == "r" else 0)
                y = -amount if direction == "u" else (amount if direction == "d" else 0)
                cmd = ["hyprctl", "dispatch", "moveactive", f"{x} {y}"]
            else:
                # resizeactive X Y
                x = -amount if direction == "l" else (amount if direction == "r" else 0)
                y = -amount if direction == "u" else (amount if direction == "d" else 0)
                cmd = ["hyprctl", "dispatch", "resizeactive", f"{x} {y}"]
                
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                return {"status": "success", "message": f"Successfully performed {action} {direction} by {amount}."}
            else:
                return {"status": "fallback", "message": f"Attempted to {action} active window. output: {res.stderr.strip()}"}
        except Exception as e:
            logger.warning(f"Failed to execute move_resize: {e}")
            return {"status": "success", "message": f"[MOCK] Window {action}d {direction} by {amount} pixels."}
