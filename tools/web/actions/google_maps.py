"""
Opens Google Maps to search for locations or compute route directions.
"""
import urllib.parse
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest
from tools.web.browser_utils import open_browser_url

logger = logging.getLogger("GoogleMapsTool")

class GoogleMapsInput(BaseModel):
    query: Optional[str] = Field(None, description="The location, address, or business to search for (e.g., 'Coliseo Romano').")
    action: str = Field(
        "search",
        description="The action to perform: 'search' (search for a place) or 'directions' (find directions/route between origin and destination)."
    )
    origin: Optional[str] = Field(None, description="The starting location for directions (if empty, Google Maps will use current location).")
    destination: Optional[str] = Field(None, description="The destination location for directions.")
    travel_mode: str = Field(
        "driving",
        description="The travel mode: 'driving', 'walking', 'bicycling', or 'transit'."
    )
    browser: str = Field("default", description="The specific browser to use: 'default', 'chrome', 'firefox', 'brave', 'chromium', or 'edge'.")

class GoogleMapsTool(BaseTool):
    manifest = ToolManifest(
        name="google_maps",
        description="Opens Google Maps in the browser to search for addresses, places, or get route directions.",
        arguments_schema=GoogleMapsInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        action = kwargs.get("action", "search").lower().strip()
        query = kwargs.get("query")
        origin = kwargs.get("origin")
        destination = kwargs.get("destination")
        travel_mode = kwargs.get("travel_mode", "driving").lower().strip()
        browser = kwargs.get("browser", "default").lower().strip()

        # Build url
        if action == "directions":
            if not destination:
                return {"error": "Missing parameter: destination is required for directions action."}
            
            encoded_dest = urllib.parse.quote(destination)
            url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_dest}"
            
            if origin:
                encoded_origin = urllib.parse.quote(origin)
                url += f"&origin={encoded_origin}"
                
            if travel_mode in ["driving", "walking", "bicycling", "transit"]:
                url += f"&travelmode={travel_mode}"
                
            logger.info(f"Opening Google Maps directions to: {destination} via travel mode: {travel_mode}")
        else:
            # Default to search
            if not query:
                url = "https://www.google.com/maps/"
                logger.info("Opening Google Maps homepage.")
            else:
                encoded_query = urllib.parse.quote(query)
                url = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
                logger.info(f"Opening Google Maps search for: {query}")

        open_res = open_browser_url(url, browser)
        return open_res
