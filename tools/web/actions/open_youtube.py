"""
Opens YouTube, searches for videos, or plays the first result directly in a browser.
"""
import urllib.request
import urllib.parse
import re
import logging
import asyncio
from typing import Any, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest
from tools.web.browser_utils import open_browser_url

logger = logging.getLogger("OpenYoutubeTool")

class OpenYoutubeInput(BaseModel):
    query: Optional[str] = Field(None, description="The video title, artist, song, or search query to find.")
    action: str = Field(
        "open_youtube",
        description="The action to perform: 'open_youtube' (just open homepage), 'search' (open search results page), or 'play' (play the first search result directly)."
    )
    browser: str = Field("default", description="The specific browser to use: 'default', 'chrome', 'firefox', 'brave', 'chromium', or 'edge'.")

def scrape_youtube_first_result(query: str) -> str:
    """Scrapes YouTube search page to extract the video ID of the first result, bypassing bot headers."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    # Custom headers to bypass YouTube bot detection/header restrictions
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8,en-US;q=0.7",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        logger.info(f"Scraping YouTube first result for query: {query}")
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            
        # Extract video ID from standard ytInitialData JSON structure
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        if video_ids:
            # Filter out duplicates and return first
            return video_ids[0]
            
        # Fallback to standard URL watch format in HTML
        matches = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
        if matches:
            return matches[0]
            
    except Exception as e:
        logger.error(f"Error scraping YouTube first result: {e}")
        
    return ""

class OpenYoutubeTool(BaseTool):
    manifest = ToolManifest(
        name="open_youtube",
        description=(
            "Opens YouTube. If a query is provided, it can search for it, "
            "or play the first result directly in the browser (useful for playing music/videos)."
        ),
        arguments_schema=OpenYoutubeInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        query = kwargs.get("query")
        action = kwargs.get("action", "open_youtube").lower().strip()
        browser = kwargs.get("browser", "default").lower().strip()

        url = "https://www.youtube.com/"

        # 1. Play first result directly
        if action == "play" and query:
            # Run the scraper in a separate thread to avoid blocking asyncio
            video_id = await asyncio.to_thread(scrape_youtube_first_result, query)
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Found first video ID '{video_id}' for query '{query}'. Playing directly...")
                open_res = open_browser_url(url, browser)
                if "error" in open_res:
                    return open_res
                return {
                    "status": "success",
                    "action": "play",
                    "query": query,
                    "video_id": video_id,
                    "url": url,
                    "browser": open_res.get("browser_used"),
                    "warning": open_res.get("warning") if "warning" in open_res else None,
                    "message": "Playing the first video result directly in browser."
                }
            else:
                logger.warning(f"Could not find a specific video for query '{query}'. Falling back to search page.")
                action = "search"

        # 2. Search YouTube results
        if action == "search" and query:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            logger.info(f"Opening YouTube search for: {query}")
            open_res = open_browser_url(url, browser)
            if "error" in open_res:
                return open_res
            return {
                "status": "success",
                "action": "search",
                "query": query,
                "url": url,
                "browser": open_res.get("browser_used"),
                "warning": open_res.get("warning") if "warning" in open_res else None,
                "message": "Opened YouTube search results in browser."
            }

        # 3. Open YouTube home
        logger.info(f"Opening YouTube homepage: {url}")
        open_res = open_browser_url(url, browser)
        return open_res
