"""
Abstractions for common Linux package manager operations.

Defines a uniform interface for installing, removing and updating software across different distributions.
"""
import logging
from host.detector import detect_system

logger = logging.getLogger("LinuxPackageManager")

def get_distro_adapter():
    """Detect distro and return the appropriate adapter class."""
    sys_info = detect_system()
    distro = sys_info.get("distro", "unknown").lower()
    
    if "arch" in distro:
        from host.adapters.linux.distros.arch import ArchAdapter
        return ArchAdapter()
    elif "debian" in distro or "ubuntu" in distro or "mint" in distro:
        from host.adapters.linux.distros.debian import DebianAdapter
        return DebianAdapter()
    elif "fedora" in distro or "redhat" in distro or "centos" in distro:
        from host.adapters.linux.distros.fedora import FedoraAdapter
        return FedoraAdapter()
    else:
        # Fallback to Arch or a generic one
        from host.adapters.linux.distros.arch import ArchAdapter
        return ArchAdapter()
