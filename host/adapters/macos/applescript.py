"""
Adapter for AppleScript interactions on macOS.

Allows sending AppleScript commands to automate macOS applications.
"""
import subprocess
import logging
from typing import Optional

logger = logging.getLogger("AppleScriptAdapter")

class AppleScriptAdapter:
    def run_script(self, script_content: str) -> Optional[str]:
        """Run an AppleScript string using osascript and return the output."""
        try:
            res = subprocess.run(
                ["osascript", "-e", script_content],
                capture_output=True, text=True, check=True
            )
            return res.stdout.strip()
        except Exception as e:
            logger.error(f"Failed to execute AppleScript: {e}")
            return None
