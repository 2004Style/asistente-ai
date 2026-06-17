"""
Lists all open windows.
"""
from typing import Any
from pydantic import BaseModel
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

class ListWindowsInput(BaseModel):
    pass

class ListWindowsTool(BaseTool):
    manifest = ToolManifest(
        name="list_windows",
        description="Lists all currently open windows in the graphical environment.",
        arguments_schema=ListWindowsInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        try:
            adapter = Container.resolve("platform_adapter")
            return adapter.list_windows()
        except Exception as e:
            return {"error": f"Failed to list windows: {str(e)}"}
