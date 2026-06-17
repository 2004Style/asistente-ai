"""
Adapter for Hyprland window manager.

Uses hyprctl to manipulate windows and gestures.
"""
import os
import json
import subprocess
import logging
from typing import List, Dict, Any

from host.adapters.base import BaseHostAdapter
from host.adapters.linux.distros.arch import ArchAdapter

logger = logging.getLogger("HyprlandAdapter")

class HyprlandAdapter(BaseHostAdapter):
    def __init__(self):
        self.distro_adapter = ArchAdapter()

    def list_windows(self) -> List[Dict[str, Any]]:
        """List active windows using hyprctl."""
        try:
            result = subprocess.run(
                ["hyprctl", "clients", "-j"],
                capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            logger.warning(f"hyprctl client command failed, returning mock windows: {e}")
            # Mock fallback for non-Hyprland environments
            return [
                {"address": "0x5555562d29f0", "workspace": {"id": 1, "name": "1"}, "class": "kitty", "title": "bash - terminal", "pid": 1234},
                {"address": "0x5555563a3c20", "workspace": {"id": 2, "name": "2"}, "class": "firefox", "title": "Google - Firefox", "pid": 5678}
            ]

    def list_apps(self) -> List[Dict[str, Any]]:
        """List installed applications by scanning standard XDG paths for .desktop files."""
        apps = []
        paths = ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]
        seen_names = set()

        for path in paths:
            if not os.path.exists(path):
                continue
            try:
                for file in os.listdir(path):
                    if not file.endswith(".desktop"):
                        continue
                    full_path = os.path.join(path, file)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            name, exec_cmd, desc = "", "", ""
                            for line in f:
                                if line.startswith("Name=") and not name:
                                    name = line.split("=")[1].strip()
                                elif line.startswith("Exec=") and not exec_cmd:
                                    exec_cmd = line.split("=")[1].strip()
                                elif line.startswith("Comment=") and not desc:
                                    desc = line.split("=")[1].strip()
                            if name and exec_cmd and name not in seen_names:
                                apps.append({
                                    "name": name,
                                    "exec": exec_cmd,
                                    "description": desc,
                                    "file": file
                                })
                                seen_names.add(name)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error scanning {path} for apps: {e}")

        # If no apps found, return a default mock list
        if not apps:
            apps = [
                {"name": "Terminal", "exec": "kitty", "description": "Run shell commands", "file": "terminal.desktop"},
                {"name": "Firefox", "exec": "firefox", "description": "Web Browser", "file": "firefox.desktop"},
                {"name": "VS Code", "exec": "code", "description": "Code Editor", "file": "code.desktop"}
            ]
        return apps

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List workspaces using hyprctl."""
        try:
            result = subprocess.run(
                ["hyprctl", "workspaces", "-j"],
                capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            logger.warning(f"hyprctl workspaces command failed, returning mock workspaces: {e}")
            return [
                {"id": 1, "name": "1", "windows": 1, "hasfullscreen": False},
                {"id": 2, "name": "2", "windows": 1, "hasfullscreen": False},
                {"id": 3, "name": "3", "windows": 0, "hasfullscreen": False}
            ]

    def switch_workspace(self, workspace_id: str) -> bool:
        """Switch to workspace using hyprctl dispatch."""
        try:
            logger.info(f"Switching to workspace: {workspace_id} via hyprctl")
            res = subprocess.run(["hyprctl", "dispatch", "workspace", str(workspace_id)], capture_output=True, text=True)
            return res.returncode == 0
        except Exception as e:
            logger.error(f"Failed to switch workspace via hyprctl: {e}")
            return False

    def open_app(self, app_name: str) -> bool:
        """Launch an application via hyprctl exec or fallback subprocess Popen."""
        try:
            logger.info(f"Opening app: {app_name}")
            # Try Hyprland run command first
            subprocess.run(["hyprctl", "dispatch", "exec", app_name], check=True, capture_output=True)
            return True
        except Exception:
            try:
                # Fallback to standard subprocess Popen
                subprocess.Popen(app_name.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setpgrp)
                return True
            except Exception as e:
                logger.error(f"Failed to open app {app_name}: {e}")
                return False

    def move_mouse(self, x: int, y: int) -> bool:
        """Move cursor to coordinate (x, y)."""
        try:
            # Hyprland movecursor
            subprocess.run(["hyprctl", "dispatch", "movecursor", f"{x} {y}"], check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Failed to move mouse via hyprctl: {e}")
            return False

    def install_package(self, package_name: str) -> bool:
        return self.distro_adapter.install_package(package_name)

    def manage_service(self, service_name: str, action: str) -> bool:
        return self.distro_adapter.manage_service(service_name, action)
