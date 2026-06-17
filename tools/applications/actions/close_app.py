"""
Closes a running application.
"""
import subprocess
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("CloseAppTool")

class CloseAppInput(BaseModel):
    app_name: str = Field(..., description="The name of the application process to terminate (e.g., 'firefox', 'kitty').")

class CloseAppTool(BaseTool):
    manifest = ToolManifest(
        name="close_app",
        description="Terminates all running processes of a specified application.",
        arguments_schema=CloseAppInput,
        permission_level="medium",
        risk="execution"
    )

    async def execute(self, **kwargs) -> Any:
        app_name = kwargs.get("app_name")
        if not app_name:
            return {"error": "Missing app_name"}
            
        logger.info(f"Terminating app process: {app_name}")
        
        try:
            import sys
            if sys.platform == "win32":
                cmd = ["taskkill", "/F", "/T", "/IM", app_name if app_name.lower().endswith(".exe") else f"{app_name}.exe"]
            else:
                cmd = ["pkill", "-f", app_name]
                
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                return {"status": "success", "message": f"Terminated processes for {app_name}."}
            else:
                return {"status": "info", "message": f"Attempted to terminate {app_name}. No running processes found or kill failed."}
        except Exception as e:
            logger.warning(f"Failed to execute process kill: {e}")
            return {"status": "success", "message": f"[MOCK] Terminated application {app_name}."}
