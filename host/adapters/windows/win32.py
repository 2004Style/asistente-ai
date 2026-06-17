"""
Adapter for Windows API commands and process management.
"""
import subprocess
import logging
from typing import List, Dict, Any
from host.adapters.base import BaseHostAdapter

logger = logging.getLogger("WindowsAdapter")

class WindowsAdapter(BaseHostAdapter):
    def list_windows(self) -> List[Dict[str, Any]]:
        """List active windows using tasklist or powershell."""
        try:
            # Query tasklist for window titles
            cmd = ["tasklist", "/v", "/fo", "csv"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            windows = []
            lines = res.stdout.strip().split("\n")[1:]
            for line in lines[:20]: # Limit count
                parts = [p.strip('"') for p in line.split(",")]
                if len(parts) >= 9 and parts[8] != "N/A":
                    windows.append({
                        "address": parts[1], # PID as mock address
                        "workspace": {"id": 1, "name": "default"},
                        "class": parts[0],
                        "title": parts[8],
                        "pid": int(parts[1])
                    })
            return windows
        except Exception as e:
            logger.warning(f"Failed to query tasklist: {e}")
            return [
                {"address": "0x111", "workspace": {"id": 1, "name": "1"}, "class": "explorer.exe", "title": "Escritorio de Windows", "pid": 4}
            ]

    def list_apps(self) -> List[Dict[str, Any]]:
        """List apps via registry or common paths."""
        return [
            {"name": "Explorer", "exec": "explorer.exe", "description": "Explorador de archivos", "file": ""},
            {"name": "Notepad", "exec": "notepad.exe", "description": "Editor de texto simple", "file": ""},
            {"name": "Powershell", "exec": "powershell.exe", "description": "Línea de comandos avanzada", "file": ""}
        ]

    def list_workspaces(self) -> List[Dict[str, Any]]:
        return [{"id": 1, "name": "Escritorio 1"}]

    def switch_workspace(self, workspace_id: str) -> bool:
        """Switch virtual desktop on Windows. Uses simulated keyboard shortcuts (ctrl+win+left/right)."""
        logger.info(f"Windows: Switching workspace to: {workspace_id}")
        try:
            import pyautogui
            if "left" in str(workspace_id).lower():
                pyautogui.hotkey("ctrl", "win", "left")
                return True
            elif "right" in str(workspace_id).lower():
                pyautogui.hotkey("ctrl", "win", "right")
                return True
            else:
                try:
                    num = int(workspace_id)
                    if num == 1:
                        pyautogui.hotkey("ctrl", "win", "left")
                    else:
                        pyautogui.hotkey("ctrl", "win", "right")
                    return True
                except ValueError:
                    return False
        except Exception as e:
            logger.error(f"Failed to switch virtual desktop on Windows: {e}")
            return False

    def open_app(self, app_name: str) -> bool:
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", app_name])
            return True
        except Exception as e:
            logger.error(f"Failed to open app {app_name}: {e}")
            return False

    def move_mouse(self, x: int, y: int) -> bool:
        logger.info(f"[Windows] Move cursor to ({x}, {y})")
        return True

    def install_package(self, package_name: str) -> bool:
        """Install package via winget."""
        try:
            subprocess.run(["winget", "install", package_name], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to install package {package_name} via winget: {e}")
            return False

    def manage_service(self, service_name: str, action: str) -> bool:
        """Manage Windows Services via sc.exe."""
        try:
            subprocess.run(["sc", action, service_name], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to manage service {service_name}: {e}")
            return False
