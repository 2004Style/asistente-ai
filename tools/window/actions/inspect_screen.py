"""
Tool to analyze the active screen contents.
"""
from typing import Any
from pydantic import BaseModel
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

class InspectScreenInput(BaseModel):
    pass

class InspectScreenTool(BaseTool):
    manifest = ToolManifest(
        name="inspect_screen",
        description="Captures a screenshot of the desktop environment and returns recognized visual items and a description.",
        arguments_schema=InspectScreenInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        try:
            vision_mgr = Container.resolve("vision_manager")
            result = await vision_mgr.analyze_screen()
            return result
        except Exception as e:
            return {"error": f"Failed to analyze screen: {str(e)}"}
