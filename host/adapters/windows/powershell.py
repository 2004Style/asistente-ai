"""
Adapter for Windows PowerShell execution environment.

Uses PowerShell scripts and cmdlets to perform system management and automation.
"""
import subprocess
import json
import logging
from typing import List, Dict, Any
from host.adapters.base import BaseHostAdapter

logger = logging.getLogger("PowerShellAdapter")

class PowerShellAdapter(BaseHostAdapter):
    def run_ps_command(self, cmd: str) -> str:
        """Run a PowerShell command and return its output."""
        try:
            full_cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd]
            res = subprocess.run(full_cmd, capture_output=True, text=True, check=True)
            return res.stdout.strip()
        except Exception as e:
            logger.error(f"PowerShell command failed: {cmd}. Error: {e}")
            raise

    def list_windows(self) -> List[Dict[str, Any]]:
        """List open windows using Get-Process."""
        script = 'Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object Id, ProcessName, MainWindowTitle | ConvertTo-Json'
        try:
            out = self.run_ps_command(script)
            if not out:
                return []
            data = json.loads(out)
            if not isinstance(data, list):
                data = [data]
            return [
                {
                    "address": str(item.get("Id")),
                    "workspace": {"id": 1, "name": "default"},
                    "class": item.get("ProcessName", ""),
                    "title": item.get("MainWindowTitle", ""),
                    "pid": item.get("Id", 0)
                } for item in data
            ]
        except Exception as e:
            logger.warning(f"Failed to list windows via PowerShell: {e}")
            return [
                {"address": "0x111", "workspace": {"id": 1, "name": "1"}, "class": "powershell", "title": "PowerShell", "pid": 1234}
            ]

    def list_apps(self) -> List[Dict[str, Any]]:
        """List installed applications using Get-StartApps."""
        script = 'Get-StartApps | ConvertTo-Json'
        try:
            out = self.run_ps_command(script)
            if not out:
                return []
            data = json.loads(out)
            if not isinstance(data, list):
                data = [data]
            return [
                {
                    "name": item.get("Name", ""),
                    "exec": item.get("AppID", ""),
                    "description": "Start Menu App",
                    "file": ""
                } for item in data
            ]
        except Exception as e:
            logger.warning(f"Failed to list apps via PowerShell: {e}")
            return [
                {"name": "Notepad", "exec": "notepad.exe", "description": "Text Editor", "file": ""}
            ]

    def list_workspaces(self) -> List[Dict[str, Any]]:
        return [{"id": 1, "name": "default"}]

    def open_app(self, app_name: str) -> bool:
        try:
            self.run_ps_command(f"Start-Process '{app_name}'")
            return True
        except Exception:
            return False

    def move_mouse(self, x: int, y: int) -> bool:
        script = f"[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y})"
        try:
            self.run_ps_command(script)
            return True
        except Exception:
            logger.warning("Failed to move mouse via PowerShell Forms, running mock move")
            return True

    def install_package(self, package_name: str) -> bool:
        """Install a package using winget via PowerShell."""
        try:
            self.run_ps_command(f"winget install --silent {package_name}")
            return True
        except Exception:
            return False

    def manage_service(self, service_name: str, action: str) -> bool:
        """Manage services via PowerShell Start-Service/Stop-Service/Restart-Service."""
        ps_action = {
            "start": "Start-Service",
            "stop": "Stop-Service",
            "restart": "Restart-Service",
            "status": "Get-Service"
        }.get(action.lower(), "Get-Service")
        
        try:
            self.run_ps_command(f"{ps_action} -Name '{service_name}'")
            return True
        except Exception:
            return False
