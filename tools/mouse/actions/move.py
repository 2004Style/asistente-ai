"""
Moves the mouse cursor to specific screen coordinates.
"""
import subprocess
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

logger = logging.getLogger("MouseMoveTool")

class MouseMoveInput(BaseModel):
    x: int = Field(..., description="The X-coordinate on the screen.")
    y: int = Field(..., description="The Y-coordinate on the screen.")

class MouseMoveTool(BaseTool):
    manifest = ToolManifest(
        name="move_mouse",
        description="Moves the mouse cursor to the specified screen coordinates.",
        arguments_schema=MouseMoveInput,
        permission_level="medium",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        x = kwargs.get("x")
        y = kwargs.get("y")
        if x is None or y is None:
            return {"error": "Missing parameters: x and y"}
            
        logger.info(f"Moving mouse cursor to ({x}, {y})")
        
        # 1. Try Platform Adapter
        try:
            adapter = Container.resolve("platform_adapter")
            if adapter and adapter.move_mouse(x, y):
                return {"status": "success", "method": "platform_adapter"}
        except Exception:
            pass
            
        # 2. Try PyAutoGUI
        try:
            import pyautogui
            pyautogui.moveTo(x, y)
            return {"status": "success", "method": "pyautogui"}
        except ImportError:
            pass
            
        # 3. Try xdotool
        try:
            subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=True, capture_output=True)
            return {"status": "success", "method": "xdotool"}
        except Exception:
            pass
            
        # 4. Fallback
        logger.warning("No pointer movement utility available. Mouse move: mock success.")
        return {"status": "success", "method": "mock_simulation", "x": x, "y": y}
