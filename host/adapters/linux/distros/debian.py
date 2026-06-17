"""
Adapter for Debian and derivative distributions.

Implements apt package operations and system services.
"""
import subprocess
import logging

logger = logging.getLogger("DebianAdapter")

class DebianAdapter:
    def install_package(self, package_name: str) -> bool:
        """Install a package using apt-get."""
        try:
            logger.info(f"Attempting to install package: {package_name} via apt-get")
            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", package_name],
                capture_output=True, text=True, check=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to install package {package_name} on Debian/Ubuntu: {e}")
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
