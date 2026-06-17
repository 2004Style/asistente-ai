"""
Lists all installed applications.
"""
from typing import Any
from pydantic import BaseModel
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

class ListAppsInput(BaseModel):
    pass

class ListAppsTool(BaseTool):
    manifest = ToolManifest(
        name="list_apps",
        description="Lists all installed applications on the system.",
        arguments_schema=ListAppsInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        try:
            adapter = Container.resolve("platform_adapter")
            return adapter.list_apps()
        except Exception as e:
            return {"error": f"Failed to list applications: {str(e)}"}
