"""
Performs a programmatic web search returning results directly to the LLM without opening a browser window.
"""
import urllib.request
import urllib.parse
import logging
import asyncio
from typing import Any, List, Dict
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("WebSearchDirectTool")

class WebSearchDirectInput(BaseModel):
    query: str = Field(..., description="The query to search for.")
    max_results: int = Field(5, description="The maximum number of search results to return.")

def scrape_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Programmatically fetches DuckDuckGo HTML search results and parses them."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Connection": "keep-alive"
    }
    
    req = urllib.request.Request(url, headers=headers)
    results = []
    
    try:
        logger.info(f"Programmatic search on DuckDuckGo for: {query}")
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, "html.parser")
        
        for r in soup.select(".result")[:max_results]:
            title_el = r.select_one(".result__a")
            snippet_el = r.select_one(".result__snippet")
            
            if title_el:
                title = title_el.get_text(strip=True)
                raw_link = title_el.get("href", "")
                
                # Clean up DuckDuckGo redirect link
                link = raw_link
                if "duckduckgo.com/l/?uddg=" in raw_link or raw_link.startswith("/l/?uddg="):
                    if raw_link.startswith("/"):
                        raw_link = "https://duckduckgo.com" + raw_link
                    parsed_url = urllib.parse.urlparse(raw_link)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    if "uddg" in query_params:
                        link = query_params["uddg"][0]
                
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                
                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })
                
    except Exception as e:
        logger.error(f"Error scraping DuckDuckGo: {e}")
        
    return results

class WebSearchDirectTool(BaseTool):
    manifest = ToolManifest(
        name="web_search_direct",
        description="Performs a direct programmatic search on the web and returns the title, URL, and snippets of the top results.",
        arguments_schema=WebSearchDirectInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        query = kwargs.get("query")
        max_results = kwargs.get("max_results", 5)
        
        if not query:
            return {"error": "Missing parameter: query"}
            
        results = await asyncio.to_thread(scrape_duckduckgo, query, max_results)
        
        return {
            "status": "success",
            "query": query,
            "results": results
        }
