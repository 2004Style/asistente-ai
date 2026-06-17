"""
Executes a command in the terminal in the background.
"""
import subprocess
import os
import shlex
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("RunInBackgroundTool")

class RunInBackgroundInput(BaseModel):
    command: str = Field(..., description="The command to run in the background.")

class RunInBackgroundTool(BaseTool):
    manifest = ToolManifest(
        name="run_in_background",
        description="Executes a command in the background without waiting for completion.",
        arguments_schema=RunInBackgroundInput,
        permission_level="high",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        command = kwargs.get("command")
        if not command:
            return {"error": "Missing parameter: command"}
            
        try:
            import sys
            cmd_args = shlex.split(command, posix=(sys.platform != "win32"))
            proc = subprocess.Popen(
                cmd_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp if hasattr(os, "setpgrp") else None
            )
            return {
                "status": "started",
                "pid": proc.pid,
                "command": command
            }
        except Exception as e:
            logger.error(f"Failed to run in background: {e}")
            return {"status": "failed", "error": str(e)}
