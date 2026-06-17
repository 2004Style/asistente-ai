"""
Browser utilities for launching specific web browsers or falling back to default.
Supports multi-platform (Linux, Windows, macOS) and multi-desktop configurations.
"""
import os
import sys
import shutil
import subprocess
import webbrowser
import logging
from typing import Dict, Any, List

logger = logging.getLogger("BrowserUtils")

def find_browser_binary(browser_name: str) -> Dict[str, Any]:
    """
    Finds the command or path to run a specific browser based on the operating system.
    
    Returns:
        A dict containing:
        - "found": bool
        - "cmd": List[str] (the base command to launch the browser)
    """
    os_name = sys.platform.lower()
    
    # 1. macOS (Darwin)
    if "darwin" in os_name:
        mac_apps = {
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "brave": "Brave Browser",
            "chromium": "Chromium",
            "edge": "Microsoft Edge",
            "opera": "Opera",
            "safari": "Safari"
        }
        app_name = mac_apps.get(browser_name)
        if app_name:
            # Check standard Mac App locations
            app_paths = [
                f"/Applications/{app_name}.app",
                os.path.expanduser(f"~/Applications/{app_name}.app")
            ]
            for path in app_paths:
                if os.path.exists(path):
                    return {"found": True, "cmd": ["open", "-a", app_name]}
                    
    # 2. Windows (win32)
    elif "win32" in os_name:
        # Check if in PATH first
        win_binaries = {
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "brave": "brave.exe",
            "chromium": "chromium.exe",
            "edge": "msedge.exe",
            "opera": "opera.exe"
        }
        bin_name = win_binaries.get(browser_name)
        if bin_name:
            path = shutil.which(bin_name)
            if path:
                return {"found": True, "cmd": [path]}
                
        # Fallback to standard installation folders
        prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        local_app_data = os.environ.get("LocalAppData", os.path.expanduser("~\\AppData\\Local"))
        
        windows_paths = {
            "chrome": [
                os.path.join(prog_files, "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(prog_files_x86, "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(local_app_data, "Google\\Chrome\\Application\\chrome.exe"),
            ],
            "firefox": [
                os.path.join(prog_files, "Mozilla Firefox\\firefox.exe"),
                os.path.join(prog_files_x86, "Mozilla Firefox\\firefox.exe"),
            ],
            "brave": [
                os.path.join(prog_files, "BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
                os.path.join(local_app_data, "BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
            ],
            "edge": [
                os.path.join(prog_files, "Microsoft\\Edge\\Application\\msedge.exe"),
                os.path.join(prog_files_x86, "Microsoft\\Edge\\Application\\msedge.exe"),
            ],
            "opera": [
                os.path.join(prog_files, "Opera\\launcher.exe"),
                os.path.join(local_app_data, "Programs\\Opera\\launcher.exe"),
            ]
        }
        
        paths = windows_paths.get(browser_name, [])
        for path in paths:
            if os.path.exists(path):
                return {"found": True, "cmd": [path]}

    # 3. Linux / generic Unix-like
    else:
        linux_binaries = {
            "chrome": ["google-chrome", "chrome", "google-chrome-stable"],
            "firefox": ["firefox", "firefox-bin"],
            "brave": ["brave", "brave-browser"],
            "chromium": ["chromium", "chromium-browser"],
            "opera": ["opera"],
            "edge": ["microsoft-edge-stable", "microsoft-edge", "edge"]
        }
        
        bins = linux_binaries.get(browser_name, [])
        for bin_name in bins:
            path = shutil.which(bin_name)
            if path:
                return {"found": True, "cmd": [path]}
                
    return {"found": False, "cmd": []}

def open_browser_url(url: str, browser_name: str = "default") -> Dict[str, Any]:
    """
    Opens a URL in a specific browser, with graceful fallback to the system default.
    Works across Linux, macOS, and Windows.
    
    Args:
        url: The URL to open.
        browser_name: The target browser name (e.g., 'chrome', 'firefox', 'brave', 'chromium', 'edge', 'opera').
                      If 'default' or empty, the system default browser is used.
                      
    Returns:
        A dict with 'status', 'browser_used', 'url', and optional 'warning' / 'error'.
    """
    browser_name = (browser_name or "default").lower().strip()
    warning_msg = None
    
    if browser_name != "default":
        search_res = find_browser_binary(browser_name)
        if search_res["found"]:
            try:
                cmd = search_res["cmd"] + [url]
                logger.info(f"Launching custom browser '{browser_name}' command: {cmd}")
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return {"status": "success", "browser_used": browser_name, "url": url}
            except Exception as e:
                logger.error(f"Failed to launch browser '{browser_name}' binary: {e}")
                warning_msg = f"Error al intentar abrir el navegador '{browser_name}': {e}. Usando el navegador por defecto."
        else:
            warning_msg = (
                f"El navegador '{browser_name}' no se encuentra instalado en el sistema. "
                "Se utilizará el navegador por defecto."
            )
            logger.warning(warning_msg)
            
    # Fallback to system default
    try:
        logger.info(f"Opening default browser for URL: {url}")
        webbrowser.open(url)
        res = {"status": "success", "browser_used": "default", "url": url}
        if warning_msg:
            res["warning"] = warning_msg
        return res
    except Exception as e:
        logger.error(f"Failed to open default browser: {e}")
        return {"error": f"Failed to open browser: {e}"}
