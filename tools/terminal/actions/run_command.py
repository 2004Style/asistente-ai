"""
Executes a command in the terminal in the foreground.
"""
import shlex
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

class RunCommandInput(BaseModel):
    command: str = Field(..., description="The command to execute (e.g. 'ls -la' or 'echo hello').")
    timeout: float = Field(15.0, description="The maximum execution time in seconds.")

class RunCommandTool(BaseTool):
    manifest = ToolManifest(
        name="run_command",
        description="Executes a command in a sandboxed environment.",
        arguments_schema=RunCommandInput,
        permission_level="high",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        command = kwargs.get("command")
        timeout = kwargs.get("timeout", 15.0)
        if not command:
            return {"error": "Missing parameter: command"}

        try:
            sandbox = Container.resolve("sandbox")
        except Exception:
            from security.sandbox import CommandSandbox
            sandbox = CommandSandbox()
            
        import sys
        cmd_args = shlex.split(command, posix=(sys.platform != "win32"))
        result = sandbox.run_command(cmd_args, timeout=timeout)
        return result
