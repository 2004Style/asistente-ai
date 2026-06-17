"""
Lists all active workspaces.
"""
from typing import Any
from pydantic import BaseModel
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

class ListWorkspacesInput(BaseModel):
    pass

class ListWorkspacesTool(BaseTool):
    manifest = ToolManifest(
        name="list_workspaces",
        description="Lists active workspaces and virtual desktops in the system.",
        arguments_schema=ListWorkspacesInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        try:
            adapter = Container.resolve("platform_adapter")
            return adapter.list_workspaces()
        except Exception as e:
            return {"error": f"Failed to list workspaces: {str(e)}"}
