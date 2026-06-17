"""
Adapter for KDE desktop environments.

Uses qdbus and KWin settings to interact with the KDE Plasma desktop.
"""
import os
import subprocess
import logging
from typing import List, Dict, Any

from host.adapters.base import BaseHostAdapter
from host.adapters.linux.package_managers import get_distro_adapter

logger = logging.getLogger("KdeAdapter")

class KdeAdapter(BaseHostAdapter):
    def __init__(self):
        self.distro_adapter = get_distro_adapter()

    def list_windows(self) -> List[Dict[str, Any]]:
        """List active windows using wmctrl if available, or fallback to mock."""
        try:
            result = subprocess.run(
                ["wmctrl", "-lG"],
                capture_output=True, text=True, check=True
            )
            windows = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split(None, 8)
                if len(parts) >= 9:
                    windows.append({
                        "address": parts[0],
                        "workspace": {"id": int(parts[1]), "name": parts[1]},
                        "class": parts[7],
                        "title": parts[8],
                        "pid": 0
                    })
            return windows
        except Exception:
            logger.warning("wmctrl not available, returning mock windows")
            return [
                {"address": "0x1234567", "workspace": {"id": 1, "name": "1"}, "class": "konsole", "title": "Terminal", "pid": 1234},
                {"address": "0x89abcde", "workspace": {"id": 2, "name": "2"}, "class": "dolphin", "title": "Files", "pid": 5678}
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

        if not apps:
            apps = [
                {"name": "Terminal", "exec": "konsole", "description": "Run shell commands", "file": "terminal.desktop"},
                {"name": "Files", "exec": "dolphin", "description": "File Browser", "file": "dolphin.desktop"}
            ]
        return apps

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List workspaces using qdbus or fallback."""
        try:
            result = subprocess.run(
                ["qdbus", "org.kde.KWin", "/VirtualDesktopManager", "org.kde.KWin.VirtualDesktopManager.desktops"],
                capture_output=True, text=True, check=True
            )
            lines = result.stdout.strip().split("\n")
            return [{"id": i, "name": line, "windows": 0, "hasfullscreen": False} for i, line in enumerate(lines, 1)]
        except Exception:
            return [{"id": 1, "name": "1", "windows": 0, "hasfullscreen": False}]

    def switch_workspace(self, workspace_id: str) -> bool:
        """Switch virtual desktop on KDE using qdbus or wmctrl."""
        # 1. Try qdbus to find desktop ID by index and activate it
        try:
            result = subprocess.run(
                ["qdbus", "org.kde.KWin", "/VirtualDesktopManager", "org.kde.KWin.VirtualDesktopManager.desktops"],
                capture_output=True, text=True, check=True
            )
            desktops = result.stdout.strip().split("\n")
            idx = int(workspace_id) - 1
            if 0 <= idx < len(desktops):
                desktop_id = desktops[idx]
                logger.info(f"KDE: Switching to virtual desktop {desktop_id} via qdbus")
                res = subprocess.run([
                    "qdbus", "org.kde.KWin", "/VirtualDesktopManager", 
                    "org.kde.KWin.VirtualDesktopManager.setCurrentDesktop", desktop_id
                ], capture_output=True)
                if res.returncode == 0:
                    return True
        except Exception as e:
            logger.warning(f"Failed to switch KDE desktop via qdbus: {e}")

        # 2. Try wmctrl
        try:
            idx = int(workspace_id) - 1
            if idx >= 0:
                res = subprocess.run(["wmctrl", "-s", str(idx)], capture_output=True)
                if res.returncode == 0:
                    logger.info(f"Switched virtual desktop to index {idx} via wmctrl")
                    return True
        except Exception:
            pass

        # 3. Fallback shortcut simulation (super + workspace_id)
        import shutil
        keys = ["super", str(workspace_id)]
        logger.info(f"KDE: Simulating key shortcut for workspace switch: {keys}")
        
        # A. Try wtype (Wayland)
        if shutil.which("wtype"):
            try:
                cmd = ["wtype", "-M", "logo", "-k", str(workspace_id)]
                subprocess.run(cmd, check=True)
                return True
            except Exception:
                pass
        
        # B. Try PyAutoGUI
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return True
        except Exception:
            pass

        # C. Try xdotool
        if shutil.which("xdotool"):
            try:
                subprocess.run(["xdotool", "key", f"super+{workspace_id}"], check=True, capture_output=True)
                return True
            except Exception:
                pass

        return False

    def open_app(self, app_name: str) -> bool:
        """Launch an application."""
        try:
            logger.info(f"Opening KDE app: {app_name}")
            subprocess.Popen(app_name.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setpgrp)
            return True
        except Exception as e:
            logger.error(f"Failed to open app {app_name}: {e}")
            return False

    def move_mouse(self, x: int, y: int) -> bool:
        """Move cursor to coordinate (x, y) using xdotool if available."""
        try:
            subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Failed to move mouse via xdotool: {e}")
            return False

    def install_package(self, package_name: str) -> bool:
        return self.distro_adapter.install_package(package_name)

    def manage_service(self, service_name: str, action: str) -> bool:
        return self.distro_adapter.manage_service(service_name, action)
