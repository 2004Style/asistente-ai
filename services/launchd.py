"""
Service management implementation for macOS launchd.
"""
import os
import sys
import logging
from pathlib import Path
from services.base import BaseServiceInstaller

logger = logging.getLogger("LaunchdInstaller")

class LaunchdInstaller(BaseServiceInstaller):
    def __init__(self):
        self.root = Path(__file__).parent.parent.resolve()
        self.plist_path = Path(os.path.expanduser("~/Library/LaunchAgents/com.rbot.assistant.plist"))
        self.python_bin = sys.executable

    def install(self) -> bool:
        """Generate launchd plist file."""
        is_frozen = getattr(sys, "frozen", False)
        
        from runtime.paths import resolve_path
        stdout_log = resolve_path("data/logs/daemon.stdout.log")
        stderr_log = resolve_path("data/logs/daemon.stderr.log")
        
        # Ensure directories exist
        stdout_log.parent.mkdir(parents=True, exist_ok=True)
        
        args_str = ""
        if is_frozen:
            args_str = f"<string>{self.python_bin}</string>\n        <string>run</string>"
        else:
            args_str = f"<string>{self.python_bin}</string>\n        <string>{self.root}/app/main.py</string>"
            
        work_dir = Path.home() if is_frozen else self.root
        
        try:
            self.plist_path.parent.mkdir(parents=True, exist_ok=True)
            content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rbot.assistant</string>
    <key>ProgramArguments</key>
    <array>
        {args_str}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{work_dir}</string>
    <key>StandardOutPath</key>
    <string>{stdout_log}</string>
    <key>StandardErrorPath</key>
    <string>{stderr_log}</string>
</dict>
</plist>
"""
            with open(self.plist_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Launchd plist file created at {self.plist_path}")
            logger.info("To load, run: launchctl load " + str(self.plist_path))
            return True
        except Exception as e:
            logger.error(f"Failed to generate launchd plist: {e}")
            return False

    def uninstall(self) -> bool:
        try:
            import subprocess
            if self.plist_path.exists():
                subprocess.run(["launchctl", "unload", "-w", str(self.plist_path)], capture_output=True)
                os.remove(self.plist_path)
            logger.info("Launchd service uninstalled successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to uninstall launchd plist: {e}")
            return False

    def start(self) -> bool:
        try:
            import subprocess
            logger.info(f"Starting macOS launchd daemon: launchctl load -w {self.plist_path}")
            subprocess.run(["launchctl", "load", "-w", str(self.plist_path)], check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Failed to start launchd daemon: {e}")
            return False

    def stop(self) -> bool:
        try:
            import subprocess
            logger.info(f"Stopping macOS launchd daemon: launchctl unload -w {self.plist_path}")
            subprocess.run(["launchctl", "unload", "-w", str(self.plist_path)], check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Failed to stop launchd daemon: {e}")
            return False

    def status(self) -> str:
        try:
            import subprocess
            res = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
            if "com.rbot.assistant" in res.stdout:
                for line in res.stdout.strip().split("\n"):
                    if "com.rbot.assistant" in line:
                        return f"active ({line})"
                return "active"
            return "inactive"
        except Exception as e:
            return f"failed to check launchd: {e}"
