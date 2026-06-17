"""
Service management implementation for Windows Service Wrapper.
"""
import sys
import logging
from pathlib import Path
from services.base import BaseServiceInstaller

logger = logging.getLogger("WindowsServiceInstaller")

class WindowsServiceInstaller(BaseServiceInstaller):
    def __init__(self):
        self.root = Path(__file__).parent.parent.resolve()
        self.xml_path = self.root / "service.xml"
        self.python_bin = sys.executable

    def install(self) -> bool:
        """Generate WinSW service.xml configuration."""
        is_frozen = getattr(sys, "frozen", False)
        args_str = "run" if is_frozen else f"{self.root}/app/main.py"
        work_dir = Path.home() if is_frozen else self.root
        
        try:
            content = f"""<service>
  <id>rbot</id>
  <name>rbot AI Assistant</name>
  <description>AI Desktop Assistant Daemon</description>
  <executable>{self.python_bin}</executable>
  <arguments>{args_str}</arguments>
  <logmode>rotate</logmode>
  <workdirectory>{work_dir}</workdirectory>
</service>
"""
            with open(self.xml_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"WinSW configuration file created at {self.xml_path}")
            logger.info("Use winsw.exe install to register it as a Windows Service.")
            return True
        except Exception as e:
            logger.error(f"Failed to generate windows service XML: {e}")
            return False

    def uninstall(self) -> bool:
        try:
            if self.xml_path.exists():
                self.xml_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to uninstall Windows Service wrapper: {e}")
            return False

    def start(self) -> bool:
        try:
            import subprocess
            logger.info("Starting Windows service 'rbot' via sc.exe...")
            subprocess.run(["sc", "start", "rbot"], check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Failed to start Windows service 'rbot': {e}")
            return False

    def stop(self) -> bool:
        try:
            import subprocess
            logger.info("Stopping Windows service 'rbot' via sc.exe...")
            subprocess.run(["sc", "stop", "rbot"], check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Failed to stop Windows service 'rbot': {e}")
            return False

    def status(self) -> str:
        try:
            import subprocess
            res = subprocess.run(["sc", "query", "rbot"], capture_output=True, text=True)
            if "RUNNING" in res.stdout:
                return "active"
            elif "STOPPED" in res.stdout:
                return "inactive"
            return res.stdout.strip()
        except Exception as e:
            return f"failed to query Windows service: {e}"
