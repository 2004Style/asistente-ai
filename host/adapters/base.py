"""
Base interface for host platform adapters.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseHostAdapter(ABC):
    @abstractmethod
    def list_windows(self) -> List[Dict[str, Any]]:
        """List active windows in the environment."""
        pass

    @abstractmethod
    def list_apps(self) -> List[Dict[str, Any]]:
        """List installed applications on the system."""
        pass

    @abstractmethod
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List active workspaces/virtual desktops."""
        pass

    @abstractmethod
    def switch_workspace(self, workspace_id: str) -> bool:
        """Switch the active session to a different workspace."""
        pass

    @abstractmethod
    def open_app(self, app_name: str) -> bool:
        """Launch an application."""
        pass

    @abstractmethod
    def move_mouse(self, x: int, y: int) -> bool:
        """Move cursor to screen coordinates (x, y)."""
        pass

    @abstractmethod
    def install_package(self, package_name: str) -> bool:
        """Install a package using the system package manager."""
        pass

    @abstractmethod
    def manage_service(self, service_name: str, action: str) -> bool:
        """Manage systemd or similar OS services (start, stop, status)."""
        pass
