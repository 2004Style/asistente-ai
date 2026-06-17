"""
Adapter for Arch Linux commands and package management.
Provides functions to install packages, manage services and query system information specific to Arch.
"""
import subprocess
import logging

logger = logging.getLogger("ArchAdapter")

class ArchAdapter:
    def install_package(self, package_name: str) -> bool:
        """Install a package using pacman."""
        try:
            logger.info(f"Attempting to install package: {package_name} via pacman")
            # In a real environment, this might require password-less sudo or fail.
            result = subprocess.run(
                ["sudo", "pacman", "-S", "--noconfirm", package_name],
                capture_output=True, text=True, check=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to install package {package_name} on Arch: {e}")
            return False

    def manage_service(self, service_name: str, action: str) -> bool:
        """Manage systemd services."""
        if action not in ("start", "stop", "restart", "status"):
            logger.error(f"Invalid service action: {action}")
            return False
        try:
            logger.info(f"Running systemctl {action} {service_name}")
            result = subprocess.run(
                ["sudo", "systemctl", action, service_name],
                capture_output=True, text=True, check=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to perform systemctl {action} on {service_name}: {e}")
            return False
