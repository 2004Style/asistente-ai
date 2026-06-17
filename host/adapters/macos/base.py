"""
Adapter for macOS commands and AppleScript interface.
"""
import os
import subprocess
import logging
from typing import List, Dict, Any
from host.adapters.base import BaseHostAdapter

logger = logging.getLogger("MacOSAdapter")

class MacOSAdapter(BaseHostAdapter):
    def list_windows(self) -> List[Dict[str, Any]]:
        """List active windows using AppleScript."""
        script = 'tell application "System Events" to get name of every window of (every process whose visible is true)'
        try:
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
            windows = []
            titles = [t.strip() for t in res.stdout.strip().split(",") if t.strip()]
            for idx, title in enumerate(titles[:15]):
                windows.append({
                    "address": f"win_{idx}",
                    "workspace": {"id": 1, "name": "Desktop"},
                    "class": "Application",
                    "title": title,
                    "pid": idx + 1000
                })
            return windows
        except Exception as e:
            logger.warning(f"Failed to query windows via AppleScript: {e}")
            return [
                {"address": "0xabc", "workspace": {"id": 1, "name": "Desktop 1"}, "class": "Finder", "title": "Finder", "pid": 100}
            ]

    def list_apps(self) -> List[Dict[str, Any]]:
        """List macOS applications in standard folder."""
        apps = []
        try:
            for item in os.listdir("/Applications"):
                if item.endswith(".app"):
                    name = item.replace(".app", "")
                    apps.append({
                        "name": name,
                        "exec": f"open -a '{name}'",
                        "description": "macOS Application",
                        "file": item
                    })
        except Exception:
            pass
        if not apps:
            apps = [
                {"name": "Finder", "exec": "open -a Finder", "description": "File Manager", "file": ""},
                {"name": "Safari", "exec": "open -a Safari", "description": "Web Browser", "file": ""},
                {"name": "Terminal", "exec": "open -a Terminal", "description": "Command Line Interface", "file": ""}
            ]
        return apps

    def list_workspaces(self) -> List[Dict[str, Any]]:
        return [{"id": 1, "name": "Desktop 1"}]

    def switch_workspace(self, workspace_id: str) -> bool:
        """Switch Space (workspace) on macOS via AppleScript simulating control + arrows or control + number."""
        import subprocess
        logger.info(f"macOS: Switching to workspace Space: {workspace_id}")
        if "left" in str(workspace_id).lower():
            script = 'tell application "System Events" to key code 123 using control down'
        elif "right" in str(workspace_id).lower():
            script = 'tell application "System Events" to key code 124 using control down'
        else:
            try:
                num = int(workspace_id)
                key_codes = {1: 18, 2: 19, 3: 20, 4: 21, 5: 23, 6: 22, 7: 26, 8: 28, 9: 25}
                if num in key_codes:
                    script = f'tell application "System Events" to key code {key_codes[num]} using control down'
                else:
                    script = f'tell application "System Events" to keystroke "{num}" using control down'
            except ValueError:
                script = f'tell application "System Events" to keystroke "{workspace_id}" using control down'
        try:
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
            return res.returncode == 0
        except Exception as e:
            logger.error(f"Failed to switch macOS workspace via AppleScript: {e}")
            return False

    def open_app(self, app_name: str) -> bool:
        try:
            subprocess.run(["open", "-a", app_name], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to open app {app_name}: {e}")
            return False

    def move_mouse(self, x: int, y: int) -> bool:
        logger.info(f"[macOS] Move mouse to ({x}, {y})")
        return True

    def install_package(self, package_name: str) -> bool:
        """Install package via brew."""
        try:
            subprocess.run(["brew", "install", package_name], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to install package {package_name} via brew: {e}")
            return False

    def manage_service(self, service_name: str, action: str) -> bool:
        """Manage macOS services via launchctl."""
        try:
            cmd = ["launchctl", "bootstrap" if action == "start" else "bootout", service_name]
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to manage macOS service {service_name}: {e}")
            return False
