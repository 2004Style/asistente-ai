"""
Fallback mock adapter for unsupported environments or quick local testing.
"""
from typing import List, Dict, Any
from host.adapters.base import BaseHostAdapter

class MockHostAdapter(BaseHostAdapter):
    def list_windows(self) -> List[Dict[str, Any]]:
        return [
            {"address": "0x11111", "workspace": {"id": 1, "name": "1"}, "class": "terminal", "title": "Mock Terminal", "pid": 111},
            {"address": "0x22222", "workspace": {"id": 2, "name": "2"}, "class": "browser", "title": "Mock Browser", "pid": 222}
        ]

    def list_apps(self) -> List[Dict[str, Any]]:
        return [
            {"name": "Terminal", "exec": "terminal", "description": "Command Line Interface", "file": "terminal.desktop"},
            {"name": "Browser", "exec": "browser", "description": "Web browser", "file": "browser.desktop"},
            {"name": "Notes", "exec": "notes", "description": "Take notes", "file": "notes.desktop"}
        ]

    def list_workspaces(self) -> List[Dict[str, Any]]:
        return [
            {"id": 1, "name": "1", "windows": 1},
            {"id": 2, "name": "2", "windows": 1}
        ]

    def switch_workspace(self, workspace_id: str) -> bool:
        print(f"[MOCK ADAPTER] Switching to workspace: {workspace_id}")
        return True

    def open_app(self, app_name: str) -> bool:
        print(f"[MOCK ADAPTER] Opening app: {app_name}")
        return True

    def move_mouse(self, x: int, y: int) -> bool:
        print(f"[MOCK ADAPTER] Moving mouse to ({x}, {y})")
        return True

    def install_package(self, package_name: str) -> bool:
        print(f"[MOCK ADAPTER] Installing package: {package_name}")
        return True

    def manage_service(self, service_name: str, action: str) -> bool:
        print(f"[MOCK ADAPTER] Managing service: {service_name} -> {action}")
        return True
