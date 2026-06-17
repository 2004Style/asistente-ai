"""
Tool to analyze the active camera feed contents.
"""
from typing import Any
from pydantic import BaseModel
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

class InspectCameraInput(BaseModel):
    pass

class InspectCameraTool(BaseTool):
    manifest = ToolManifest(
        name="inspect_camera",
        description="Captures a frame from the webcam and returns recognized objects and a visual description.",
        arguments_schema=InspectCameraInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        try:
            vision_mgr = Container.resolve("vision_manager")
            # Force capture/processing of a camera frame
            result = await vision_mgr.analyze_camera(force=True)
            return result
        except Exception as e:
            return {"error": f"Failed to analyze camera: {str(e)}"}
