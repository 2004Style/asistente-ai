"""
Switches to the specified workspace.
"""
import subprocess
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("SwitchWorkspaceTool")

class SwitchWorkspaceInput(BaseModel):
    workspace_id: str = Field(..., description="The ID or name of the workspace to switch to (e.g., '1', '2', 'work').")

class SwitchWorkspaceTool(BaseTool):
    manifest = ToolManifest(
        name="switch_workspace",
        description="Switches the active desktop session to a different workspace.",
        arguments_schema=SwitchWorkspaceInput,
        permission_level="low",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        workspace_id = kwargs.get("workspace_id")
        if not workspace_id:
            return {"error": "Missing workspace_id"}
            
        logger.info(f"Switching to workspace: {workspace_id}")
        
        try:
            from app.container import Container
            adapter = Container.resolve("platform_adapter")
            success = adapter.switch_workspace(str(workspace_id))
            if success:
                return {"status": "success", "message": f"Switched to workspace {workspace_id}."}
            else:
                return {"status": "failed", "message": f"Failed to switch to workspace {workspace_id}."}
        except Exception as e:
            logger.error(f"Error executing workspace switch: {e}")
            return {"status": "error", "message": f"Failed to switch workspace: {str(e)}"}
