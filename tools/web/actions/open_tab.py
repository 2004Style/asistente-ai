"""
Opens a new tab in the web browser.
"""
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest
from tools.web.browser_utils import open_browser_url

logger = logging.getLogger("OpenTabTool")

class OpenTabInput(BaseModel):
    url: str = Field(..., description="The URL to open in the browser.")
    browser: str = Field("default", description="The specific browser to use: 'default', 'chrome', 'firefox', 'brave', 'chromium', or 'edge'.")

class OpenTabTool(BaseTool):
    manifest = ToolManifest(
        name="open_tab",
        description="Opens a URL in a new tab of the web browser.",
        arguments_schema=OpenTabInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        url = kwargs.get("url")
        browser = kwargs.get("browser", "default").lower().strip()
        if not url:
            return {"error": "Missing parameter: url"}
            
        # Ensure url starts with a protocol
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
            
        logger.info(f"Opening tab with URL: {url} inside browser: {browser}")
        open_res = open_browser_url(url, browser)
        return open_res
