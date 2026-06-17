"""
Adapter for GNOME desktop environments.

Uses D‑Bus and GSettings to interact with GNOME settings and applications.
"""
import os
import subprocess
import logging
from typing import List, Dict, Any

from host.adapters.base import BaseHostAdapter
from host.adapters.linux.package_managers import get_distro_adapter

logger = logging.getLogger("GnomeAdapter")

class GnomeAdapter(BaseHostAdapter):
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
                {"address": "0x1234567", "workspace": {"id": 1, "name": "1"}, "class": "gnome-terminal", "title": "Terminal", "pid": 1234},
                {"address": "0x89abcde", "workspace": {"id": 2, "name": "2"}, "class": "nautilus", "title": "Files", "pid": 5678}
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
                {"name": "Terminal", "exec": "gnome-terminal", "description": "Run shell commands", "file": "terminal.desktop"},
                {"name": "Files", "exec": "nautilus", "description": "File Browser", "file": "nautilus.desktop"}
            ]
        return apps

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List workspaces using gsettings or fallback."""
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.wm.preferences", "num-workspaces"],
                capture_output=True, text=True, check=True
            )
            num = int(result.stdout.strip().replace("uint32 ", ""))
            return [{"id": i, "name": str(i), "windows": 0, "hasfullscreen": False} for i in range(1, num + 1)]
        except Exception:
            return [{"id": 1, "name": "1", "windows": 0, "hasfullscreen": False}]

    def switch_workspace(self, workspace_id: str) -> bool:
        """Switch workspaces in GNOME using wmctrl, or by simulating key combinations."""
        # 1. Try wmctrl
        try:
            idx = int(workspace_id) - 1
            if idx >= 0:
                res = subprocess.run(["wmctrl", "-s", str(idx)], capture_output=True)
                if res.returncode == 0:
                    logger.info(f"Switched workspace to index {idx} via wmctrl")
                    return True
        except Exception:
            pass

        # 2. Try querying GSettings for switch-to-workspace keybinding
        import re
        import shutil
        keys = []
        try:
            res = subprocess.run([
                "gsettings", "get", 
                "org.gnome.desktop.wm.keybindings", 
                f"switch-to-workspace-{workspace_id}"
            ], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                binding = res.stdout.strip()
                match = re.search(r"'(.*?)'", binding)
                if match:
                    raw_keys = match.group(1)
                    mod_matches = re.findall(r"<(.*?)>", raw_keys)
                    for mod in mod_matches:
                        keys.append(mod.lower())
                    last_gt = raw_keys.rfind(">")
                    if last_gt != -1:
                        main_k = raw_keys[last_gt+1:]
                        if main_k:
                            keys.append(main_k.lower())
                    else:
                        keys.append(raw_keys.lower())
        except Exception as e:
            logger.warning(f"Failed to read GSettings switch-to-workspace: {e}")

        if not keys:
            keys = ["super", str(workspace_id)]

        logger.info(f"GNOME: Simulating key shortcut for workspace switch: {keys}")

        # 3. Simulate the keystrokes
        # A. Try wtype (Wayland)
        if shutil.which("wtype"):
            try:
                cmd = ["wtype"]
                modifiers = []
                main_key = None
                mod_map = {
                    "ctrl": "ctrl", "control": "ctrl",
                    "alt": "alt", "shift": "shift",
                    "super": "logo", "win": "logo", "logo": "logo"
                }
                for k in keys:
                    k_lower = k.lower().strip()
                    if k_lower in mod_map:
                        modifiers.append(mod_map[k_lower])
                    else:
                        main_key = k
                for mod in modifiers:
                    cmd.extend(["-M", mod])
                if main_key:
                    if main_key.lower() == "return":
                        main_key = "Enter"
                    cmd.extend(["-k", main_key])
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
                xd_shortcut = "+".join(keys)
                subprocess.run(["xdotool", "key", xd_shortcut], check=True, capture_output=True)
                return True
            except Exception:
                pass

        return False

    def open_app(self, app_name: str) -> bool:
        """Launch an application."""
        try:
            logger.info(f"Opening GNOME app: {app_name}")
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
