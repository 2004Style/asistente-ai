"""
Service management implementation for Linux systemd.
"""
import os
import sys
import getpass
import subprocess
import logging
from pathlib import Path
from services.base import BaseServiceInstaller

logger = logging.getLogger("SystemdInstaller")

class SystemdInstaller(BaseServiceInstaller):
    def __init__(self):
        self.user = getpass.getuser()
        self.root = Path(__file__).parent.parent.resolve()
        self.service_dir = Path(os.path.expanduser("~/.config/systemd/user"))
        self.service_path = self.service_dir / "rbot.service"
        self.python_bin = sys.executable

    def install(self) -> bool:
        """Create and load user systemd service."""
        is_frozen = getattr(sys, "frozen", False)
        exec_start = f"{self.python_bin} run" if is_frozen else f"{self.python_bin} {self.root}/app/main.py"
        work_dir = Path.home() if is_frozen else self.root
        
        try:
            self.service_dir.mkdir(parents=True, exist_ok=True)
            
            content = f"""[Unit]
Description=rbot AI Assistant Daemon
After=network.target

[Service]
Type=simple
User={self.user}
WorkingDirectory={work_dir}
ExecStart={exec_start}
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""
            with open(self.service_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Systemd service file created at {self.service_path}")
            
            # Reload daemon
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            # Enable service
            subprocess.run(["systemctl", "--user", "enable", "rbot.service"], check=True)
            logger.info("Systemd service enabled successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to install systemd service: {e}")
            return False

    def uninstall(self) -> bool:
        """Disable and remove systemd service."""
        try:
            subprocess.run(["systemctl", "--user", "disable", "rbot.service"], check=True)
            if self.service_path.exists():
                os.remove(self.service_path)
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            logger.info("Systemd service uninstalled successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to uninstall systemd service: {e}")
            return False

    def start(self) -> bool:
        try:
            subprocess.run(["systemctl", "--user", "start", "rbot.service"], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to start systemd service: {e}")
            return False

    def stop(self) -> bool:
        try:
            subprocess.run(["systemctl", "--user", "stop", "rbot.service"], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to stop systemd service: {e}")
            return False

    def status(self) -> str:
        try:
            res = subprocess.run(
                ["systemctl", "--user", "is-active", "rbot.service"],
                capture_output=True, text=True
            )
            return res.stdout.strip()
        except Exception as e:
            return f"failed to check systemd: {e}"
