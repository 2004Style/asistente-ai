"""
Implements a sandbox environment to safely execute tools and external commands.
"""
import os
import subprocess
import logging
from typing import List, Dict, Any, Optional
from security.policy import SecurityPolicy

logger = logging.getLogger("Sandbox")

class CommandSandbox:
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy()

    def run_command(self, cmd: List[str], timeout: float = 15.0) -> Dict[str, Any]:
        """Run a command inside a restricted environment with a timeout."""
        # 1. Policy check
        cmd_str = " ".join(cmd)
        if not self.policy.validate_action("execute_command", {"app_name": cmd_str}):
            return {"status": "blocked", "error": "Command blocked by security policy."}

        # 2. Build restricted environment
        # Keep basic PATH but remove sensitive keys
        clean_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
            "TERM": "xterm-256color"
        }
        
        # Keep XDG or Wayland vars if needed for graphical operations
        for key in ["WAYLAND_DISPLAY", "DISPLAY", "HYPRLAND_INSTANCE_SIGNATURE", "XDG_RUNTIME_DIR"]:
            if key in os.environ:
                clean_env[key] = os.environ[key]

        logger.info(f"Running sandboxed command: {cmd_str}")
        try:
            res = subprocess.run(
                cmd,
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "status": "completed",
                "returncode": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr
            }
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {cmd_str}")
            return {"status": "timeout", "error": f"Command timed out after {timeout} seconds."}
        except Exception as e:
            logger.error(f"Failed to run command in sandbox: {e}")
            return {"status": "failed", "error": str(e)}
