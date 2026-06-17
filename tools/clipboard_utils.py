"""
Shared clipboard and GUI modifier utilities.
Provides multi-platform (Linux Wayland/X11, macOS, Windows) support.
"""
import sys
import os
import subprocess
import logging
from host.detector import detect_system

logger = logging.getLogger("ClipboardUtils")

def get_platform_modifiers() -> tuple[str, str]:
    """
    Returns the appropriate modifier keys for the host OS.
    Returns:
        (ctrl_modifier, alt_modifier)
    """
    sys_info = detect_system()
    os_name = sys_info["os"]
    
    if os_name == "macos":
        return "command", "option"
    else:
        return "ctrl", "alt"

def read_clipboard_text() -> str:
    """Multi-platform helper to read clipboard text using native tools or pyperclip."""
    os_name = sys.platform.lower()
    
    # 1. macOS (Darwin)
    if "darwin" in os_name:
        try:
            return subprocess.check_output(["pbpaste"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
        except Exception:
            pass
            
    # 2. Linux (Wayland / X11)
    elif "linux" in os_name:
        # Try Wayland paste
        try:
            return subprocess.check_output(["wl-paste"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
        except Exception:
            pass
        # Try X11 xclip paste
        try:
            return subprocess.check_output(["xclip", "-selection", "clipboard", "-o"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
        except Exception:
            pass
        # Try X11 xsel paste
        try:
            return subprocess.check_output(["xsel", "--clipboard", "--output"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
        except Exception:
            pass
            
    # 3. Windows / Fallback
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception as e:
        logger.error(f"Failed to read clipboard: {e}")
        
    return ""

def write_clipboard_text(text: str) -> None:
    """Multi-platform helper to write text to clipboard using native tools or pyperclip."""
    os_name = sys.platform.lower()
    
    # 1. macOS (Darwin)
    if "darwin" in os_name:
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p.communicate(input=text.encode("utf-8"))
            return
        except Exception:
            pass
            
    # 2. Linux (Wayland / X11)
    elif "linux" in os_name:
        # Try Wayland copy
        try:
            p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p.communicate(input=text.encode("utf-8"))
            return
        except Exception:
            pass
        # Try X11 xclip copy
        try:
            p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p.communicate(input=text.encode("utf-8"))
            return
        except Exception:
            pass
        # Try X11 xsel copy
        try:
            p = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p.communicate(input=text.encode("utf-8"))
            return
        except Exception:
            pass
            
    # 3. Windows / Fallback
    try:
        import pyperclip
        pyperclip.copy(text)
    except Exception as e:
        logger.error(f"Failed to write to clipboard: {e}")

async def paste_text_via_gui(text: str) -> None:
    """Type text into current focused element using clipboard pasting (Ctrl+V or Cmd+V)."""
    import asyncio
    import pyautogui
    ctrl, _ = get_platform_modifiers()
    write_clipboard_text(text)
    await asyncio.sleep(0.3)
    pyautogui.hotkey(ctrl, 'v')
    await asyncio.sleep(0.3)
