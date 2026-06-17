"""
Registry module to manage and fetch available tools configured in the system.
"""
from typing import Dict, List, Optional
from tools.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        name = tool.manifest.name
        self._tools[name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Fetch a registered tool by its name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """List all currently registered tools."""
        return list(self._tools.values())

def load_default_tools() -> ToolRegistry:
    """Helper to instantiate and return a ToolRegistry with default tools registered."""
    registry = ToolRegistry()
    
    # Import actions
    from tools.window.actions.list_windows import ListWindowsTool
    from tools.window.actions.close import CloseWindowTool
    from tools.window.actions.focus import FocusWindowTool
    from tools.window.actions.move_resize import MoveResizeWindowTool
    from tools.window.actions.inspect_screen import InspectScreenTool
    from tools.window.actions.inspect_camera import InspectCameraTool
    from tools.window.actions.inspect_image import InspectImageTool
    
    from tools.workspace.actions.list_workspaces import ListWorkspacesTool
    from tools.workspace.actions.switch_workspace import SwitchWorkspaceTool
    from tools.workspace.actions.create_project import CreateProjectTool
    
    from tools.applications.actions.list_apps import ListAppsTool
    from tools.applications.actions.open_app import OpenAppTool
    from tools.applications.actions.close_app import CloseAppTool
    from tools.applications.actions.schedule_reminder import ScheduleReminderTool
    
    from tools.files.actions.read_file import ReadFileTool
    from tools.files.actions.copy_file import CopyFileTool
    from tools.files.actions.delete_file import DeleteFileTool
    from tools.files.actions.move_file import MoveFileTool
    from tools.files.actions.write_file import WriteFileTool
    from tools.files.actions.create_word_document import CreateWordDocumentTool
    from tools.files.actions.create_pdf_document import CreatePDFDocumentTool
    
    from tools.notes.actions.list_notes import ListNotesTool
    from tools.notes.actions.create_note import CreateNoteTool
    from tools.notes.actions.delete_note import DeleteNoteTool

    # Terminal actions
    from tools.terminal.actions.run_command import RunCommandTool
    from tools.terminal.actions.run_in_background import RunInBackgroundTool
    from tools.terminal.actions.kill_process import KillProcessTool

    # Keyboard actions
    from tools.keyboard.actions.type_text import TypeTextTool
    from tools.keyboard.actions.press_key import PressKeyTool
    from tools.keyboard.actions.shortcut import KeyboardShortcutTool

    # Mouse actions
    from tools.mouse.actions.move import MouseMoveTool
    from tools.mouse.actions.click import MouseClickTool
    from tools.mouse.actions.scroll import MouseScrollTool

    # Web actions
    from tools.web.actions.open_tab import OpenTabTool
    from tools.web.actions.close_tab import CloseTabTool
    from tools.web.actions.open_whatsapp import OpenWhatsappTool
    from tools.web.actions.open_youtube import OpenYoutubeTool
    from tools.web.actions.search import WebSearchTool
    from tools.web.actions.web_search_direct import WebSearchDirectTool
    from tools.web.actions.google_maps import GoogleMapsTool
    from tools.web.actions.download_media import DownloadMediaTool
    
    # Register actions
    registry.register(ListWindowsTool())
    registry.register(CloseWindowTool())
    registry.register(FocusWindowTool())
    registry.register(MoveResizeWindowTool())
    registry.register(InspectScreenTool())
    registry.register(InspectCameraTool())
    registry.register(InspectImageTool())
    
    registry.register(ListWorkspacesTool())
    registry.register(SwitchWorkspaceTool())
    registry.register(CreateProjectTool())
    
    registry.register(ListAppsTool())
    registry.register(OpenAppTool())
    registry.register(CloseAppTool())
    registry.register(ScheduleReminderTool())
    
    registry.register(ReadFileTool())
    registry.register(CopyFileTool())
    registry.register(DeleteFileTool())
    registry.register(MoveFileTool())
    registry.register(WriteFileTool())
    registry.register(CreateWordDocumentTool())
    registry.register(CreatePDFDocumentTool())
    
    registry.register(ListNotesTool())
    registry.register(CreateNoteTool())
    registry.register(DeleteNoteTool())

    # Register Terminal actions
    registry.register(RunCommandTool())
    registry.register(RunInBackgroundTool())
    registry.register(KillProcessTool())

    # Register Keyboard actions
    registry.register(TypeTextTool())
    registry.register(PressKeyTool())
    registry.register(KeyboardShortcutTool())

    # Register Mouse actions
    registry.register(MouseMoveTool())
    registry.register(MouseClickTool())
    registry.register(MouseScrollTool())

    # Register Web actions
    registry.register(OpenTabTool())
    registry.register(CloseTabTool())
    registry.register(OpenWhatsappTool())
    registry.register(OpenYoutubeTool())
    registry.register(WebSearchTool())
    registry.register(WebSearchDirectTool())
    registry.register(GoogleMapsTool())
    registry.register(DownloadMediaTool())
    
    # Validate and sync Python tools with YAML manifests (XDG CONFIG_DIR / manifests)
    try:
        validate_and_sync_manifests(registry)
    except Exception as e:
        import logging
        logging.getLogger("ToolRegistry").error(f"Failed to validate/sync manifests: {e}")
        
    return registry

def validate_and_sync_manifests(registry: ToolRegistry) -> None:
    """
    Finds and loads all manifest.yml files in CONFIG_DIR/manifests,
    validates that registered tools match their YAML manifest definitions,
    and syncs metadata (like Spanish descriptions) from YAML to the registered tool manifests.
    """
    from runtime.paths import CONFIG_DIR
    import yaml
    from pathlib import Path
    import logging

    logger = logging.getLogger("ToolRegistry")
    
    manifests_dir = CONFIG_DIR / "manifests"
    if not manifests_dir.exists():
        logger.warning(f"Manifests directory {manifests_dir} does not exist. Skipping validation.")
        return

    yaml_files = list(manifests_dir.glob("*.yml"))
    if not yaml_files:
        logger.warning(f"No manifest .yml files found in {manifests_dir}. Skipping validation.")
        return

    logger.info(f"Validating registry against {len(yaml_files)} YAML manifest files in {manifests_dir}...")
    
    mismatch_map = {
        "search": "web_search",
        "focus": "focus_window",
        "close": "close_window",
        "move_resize": "move_resize_window",
        "shortcut": "keyboard_shortcut",
        "click_mouse": "mouse_click",
        "move_mouse": "mouse_move",
        "scroll_mouse": "mouse_scroll"
    }

    # Reverse map for python tools to YAML actions
    py_to_yaml_map = {v: k for k, v in mismatch_map.items()}

    for yaml_path in yaml_files:
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                continue
                
            group_name = data.get("name", "unknown")
            actions = data.get("actions", {})
            
            for action_name, action_info in actions.items():
                expected_py_names = [action_name]
                if action_name in mismatch_map:
                    expected_py_names.append(mismatch_map[action_name])
                if action_name in py_to_yaml_map:
                    expected_py_names.append(py_to_yaml_map[action_name])
                
                tool = None
                for py_name in expected_py_names:
                    tool = registry.get_tool(py_name)
                    if tool:
                        break
                        
                if not tool:
                    logger.warning(f"Manifest action '{action_name}' in group '{group_name}' is declared in YAML but no Python tool is registered.")
                    continue
                    
                # Sync metadata from manifest.yml to Python ToolManifest
                yaml_desc = action_info.get("description")
                if yaml_desc:
                    tool.manifest.description = yaml_desc
                    
                yaml_permission = action_info.get("permission_level")
                if yaml_permission:
                    tool.manifest.permission_level = yaml_permission
                    
                yaml_risk = action_info.get("risk")
                if yaml_risk:
                    tool.manifest.risk = yaml_risk
                    
            logger.info(f"Successfully validated and synchronized manifest group '{group_name}' from {yaml_path.name}")
        except Exception as e:
            logger.error(f"Error loading/validating manifest {yaml_path}: {e}")

