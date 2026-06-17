"""
Opens a specific application.
"""
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

logger = logging.getLogger("OpenAppTool")

class OpenAppInput(BaseModel):
    app_name: str = Field(..., description="The command or executable name of the app to launch (e.g., 'kitty', 'firefox').")

class OpenAppTool(BaseTool):
    manifest = ToolManifest(
        name="open_app",
        description="Launches an application in the system.",
        arguments_schema=OpenAppInput,
        permission_level="medium",
        risk="execution"
    )

    async def execute(self, **kwargs) -> Any:
        app_name = kwargs.get("app_name")
        if not app_name:
            return {"error": "Missing app_name"}
            
        logger.info(f"Launching app: {app_name}")
        
        try:
            adapter = Container.resolve("platform_adapter")
            success = adapter.open_app(app_name)
            if success:
                return {"status": "success", "message": f"Successfully launched {app_name}."}
            else:
                return {"error": f"Failed to launch app {app_name} via platform adapter."}
        except Exception as e:
            logger.error(f"Error launching app {app_name}: {e}")
            return {"error": str(e)}
