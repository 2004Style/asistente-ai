"""
Kills a running process.
"""
import subprocess
import os
import signal
import sys
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("KillProcessTool")

class KillProcessInput(BaseModel):
    pid: Optional[int] = Field(None, description="The process ID (PID) to kill.")
    process_name: Optional[str] = Field(None, description="The process name to kill if PID is not known.")

class KillProcessTool(BaseTool):
    manifest = ToolManifest(
        name="kill_process",
        description="Terminates a process by PID or name.",
        arguments_schema=KillProcessInput,
        permission_level="high",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        pid = kwargs.get("pid")
        process_name = kwargs.get("process_name")
        if not pid and not process_name:
            return {"error": "Must provide either pid or process_name"}
            
        try:
            if pid:
                os.kill(pid, signal.SIGKILL)
                return {"status": "success", "message": f"Killed process with PID {pid}"}
            else:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/IM", process_name], check=True)
                else:
                    subprocess.run(["pkill", "-f", process_name], check=True)
                return {"status": "success", "message": f"Killed processes matching name '{process_name}'"}
        except Exception as e:
            logger.error(f"Failed to kill process: {e}")
            return {"error": str(e)}
