"""
Performs a web search in the browser.
"""
import urllib.parse
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest
from tools.web.browser_utils import open_browser_url

logger = logging.getLogger("WebSearchTool")

class WebSearchInput(BaseModel):
    query: str = Field(..., description="The query to search for.")
    browser: str = Field("default", description="The specific browser to use: 'default', 'chrome', 'firefox', 'brave', 'chromium', or 'edge'.")

class WebSearchTool(BaseTool):
    manifest = ToolManifest(
        name="web_search",
        description="Performs a Google search using a new browser tab/window.",
        arguments_schema=WebSearchInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        query = kwargs.get("query")
        browser = kwargs.get("browser", "default").lower().strip()
        if not query:
            return {"error": "Missing parameter: query"}
            
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        
        logger.info(f"Performing web search: {query} -> {url} inside browser: {browser}")
        open_res = open_browser_url(url, browser)
        return open_res
