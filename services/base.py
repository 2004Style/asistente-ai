"""
Base class for OS service management (systemd, launchd, Windows Service).
"""
from abc import ABC, abstractmethod

class BaseServiceInstaller(ABC):
    @abstractmethod
    def install(self) -> bool:
        """Install the assistant as a background service on the host system."""
        pass

    @abstractmethod
    def uninstall(self) -> bool:
        """Uninstall the assistant service."""
        pass

    @abstractmethod
    def start(self) -> bool:
        """Start the background service."""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop the background service."""
        pass

    @abstractmethod
    def status(self) -> str:
        """Query the status of the service."""
        pass
