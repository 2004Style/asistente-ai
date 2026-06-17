"""
Adapter for the Shortcuts app on macOS.

Enables triggering shortcuts and automations.
"""
import subprocess
import logging
from typing import List, Optional

logger = logging.getLogger("MacShortcutsAdapter")

class MacShortcutsAdapter:
    def list_shortcuts(self) -> List[str]:
        """List all available shortcuts on macOS."""
        try:
            res = subprocess.run(
                ["shortcuts", "list"],
                capture_output=True, text=True, check=True
            )
            return [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]
        except Exception as e:
            logger.error(f"Failed to list macOS shortcuts: {e}")
            return []

    def run_shortcut(self, shortcut_name: str, input_text: Optional[str] = None) -> bool:
        """Run a specific macOS shortcut by name, optionally passing input text."""
        try:
            cmd = ["shortcuts", "run", shortcut_name]
            if input_text:
                cmd.extend(["-i", input_text])
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return res.returncode == 0
        except Exception as e:
            logger.error(f"Failed to run macOS shortcut '{shortcut_name}': {e}")
            return False
