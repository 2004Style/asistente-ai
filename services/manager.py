"""
Manager module to select and execute the appropriate OS service installer.
"""
import sys
import logging
from services.base import BaseServiceInstaller
from services.systemd import SystemdInstaller
from services.launchd import LaunchdInstaller
from services.windows_service import WindowsServiceInstaller

logger = logging.getLogger("ServiceManager")

def get_service_installer() -> BaseServiceInstaller:
    """Return the service installer matching the host operating system."""
    os_name = sys.platform
    logger.info(f"Resolving service installer for OS: {os_name}")
    
    if os_name.startswith("linux"):
        return SystemdInstaller()
    elif os_name == "darwin":
        return LaunchdInstaller()
    elif os_name == "win32":
        return WindowsServiceInstaller()
    else:
        # Fallback to systemd as default
        logger.warning(f"OS '{os_name}' not natively supported, falling back to Systemd installer")
        return SystemdInstaller()
