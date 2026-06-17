"""
Detects the host OS distribution and graphic desktop environment at runtime.
"""
import os
import sys
import platform
from typing import Dict, Any

def detect_system() -> Dict[str, Any]:
    """Detect the host system distribution and graphic desktop environment."""
    os_name = sys.platform
    result = {
        "os": os_name,
        "distro": "unknown",
        "desktop": "unknown"
    }

    if os_name == "win32":
        result["os"] = "windows"
        result["distro"] = "windows"
        result["desktop"] = "explorer"
    elif os_name == "darwin":
        result["os"] = "macos"
        result["distro"] = "macos"
        result["desktop"] = "aqua"
    elif os_name.startswith("linux"):
        result["os"] = "linux"
        # Detect distro
        if os.path.exists("/etc/os-release"):
            try:
                with open("/etc/os-release", "r") as f:
                    lines = f.readlines()
                for line in lines:
                    if line.startswith("ID="):
                        result["distro"] = line.split("=")[1].strip().strip('"')
                        break
            except Exception:
                pass
        
        # Detect desktop
        desktop = os.getenv("XDG_CURRENT_DESKTOP") or os.getenv("DESKTOP_SESSION") or ""
        result["desktop"] = desktop.lower()
        
        # Specifically check if hyprland is active (e.g. env var HYPRLAND_INSTANCE_SIGNATURE)
        if os.getenv("HYPRLAND_INSTANCE_SIGNATURE"):
            result["desktop"] = "hyprland"

    return result
