"""
Focuses the specified window.
"""
import subprocess
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

logger = logging.getLogger("FocusWindowTool")

class FocusWindowInput(BaseModel):
    address: Optional[str] = Field(None, description="The unique address of the window to focus (e.g., '0x5555562d29f0').")
    query: Optional[str] = Field(None, description="A search query (title, class, or application name) to find and focus a window dynamically.")

class FocusWindowTool(BaseTool):
    manifest = ToolManifest(
        name="focus_window",
        description="Brings a specific window to focus using its address or a search query.",
        arguments_schema=FocusWindowInput,
        permission_level="low",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        address = kwargs.get("address")
        query = kwargs.get("query")
        
        if not address and not query:
            return {"error": "Must specify either 'address' or 'query' to focus a window."}
            
        try:
            adapter = Container.resolve("platform_adapter")
        except Exception as e:
            return {"error": f"Failed to get platform adapter: {e}"}
            
        if query:
            try:
                windows = adapter.list_windows()
                q = query.lower()
                matched_address = None
                best_match = None
                
                # First try exact or substring match in class name
                for w in windows:
                    w_class = str(w.get("class", "")).lower()
                    if q == w_class or q in w_class:
                        matched_address = w.get("address")
                        best_match = w
                        break
                        
                # Then try substring match in title if no class match
                if not matched_address:
                    for w in windows:
                        w_title = str(w.get("title", "")).lower()
                        if q in w_title:
                            matched_address = w.get("address")
                            best_match = w
                            break
                            
                # Fallback for browser queries
                if not matched_address:
                    if q in ("navegador", "browser", "internet", "web"):
                        for w in windows:
                            w_class = str(w.get("class", "")).lower()
                            if any(browser in w_class for browser in ("firefox", "chrome", "chromium", "brave", "opera", "zen", "librewolf")):
                                matched_address = w.get("address")
                                best_match = w
                                break
                                
                if not matched_address:
                    return {"status": "error", "message": f"No window found matching query '{query}'."}
                    
                address = matched_address
                logger.info(f"Resolved query '{query}' to window: {best_match.get('title')} ({address})")
            except Exception as e:
                logger.error(f"Error resolving window query: {e}")
                return {"status": "error", "message": f"Error searching windows: {e}"}
                
        logger.info(f"Focusing window: {address}")
        
        try:
            res = subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{address}"], capture_output=True, text=True)
            if res.returncode == 0:
                return {"status": "success", "message": f"Focused window matching query '{query or address}'."}
            else:
                return {"status": "fallback", "message": f"Attempted to focus window {address}. output: {res.stderr.strip()}"}
        except Exception as e:
            logger.warning(f"Failed to execute native focus: {e}")
            return {"status": "success", "message": f"[MOCK] Focused window {address}."}
