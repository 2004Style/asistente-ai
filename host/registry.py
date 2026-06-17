"""
Registry of active host adapters.

Loads and activates adapters based on the platform configuration.
"""
import logging
from host.detector import detect_system
from host.adapters.base import BaseHostAdapter
from host.adapters.linux.desktops.hyprland import HyprlandAdapter
from host.adapters.linux.desktops.gnome import GnomeAdapter
from host.adapters.linux.desktops.kde import KdeAdapter
from host.adapters.mock import MockHostAdapter

logger = logging.getLogger("HostRegistry")

_active_adapter: BaseHostAdapter = None

def get_host_adapter() -> BaseHostAdapter:
    """Get or initialize the active host adapter based on detected environment."""
    global _active_adapter
    if _active_adapter is not None:
        return _active_adapter

    sys_info = detect_system()
    os_name = sys_info["os"]
    desktop = sys_info["desktop"] or ""

    logger.info(f"Host environment detected: OS={os_name}, Desktop={desktop}")

    if os_name == "linux":
        if desktop == "hyprland":
            logger.info("Activating Hyprland adapter")
            _active_adapter = HyprlandAdapter()
        elif "gnome" in desktop:
            logger.info("Activating GNOME adapter")
            _active_adapter = GnomeAdapter()
        elif "kde" in desktop or "plasma" in desktop:
            logger.info("Activating KDE adapter")
            _active_adapter = KdeAdapter()
        else:
            logger.info("Activating Hyprland adapter as generic Linux fallback")
            _active_adapter = HyprlandAdapter()
    elif os_name == "windows":
        logger.info("Activating Windows adapter")
        from host.adapters.windows.win32 import WindowsAdapter
        _active_adapter = WindowsAdapter()
    elif os_name == "macos":
        logger.info("Activating macOS adapter")
        from host.adapters.macos.base import MacOSAdapter
        _active_adapter = MacOSAdapter()
    else:
        logger.info("No concrete adapter found for environment, activating fallback MockHostAdapter")
        _active_adapter = MockHostAdapter()

    return _active_adapter
