"""
Tool to analyze an image file (local path or URL) using object detection and classification.
"""
import os
import urllib.request
import logging
import asyncio
from typing import Any
from pydantic import BaseModel, Field
from pathlib import Path
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

logger = logging.getLogger("InspectImageTool")

class InspectImageInput(BaseModel):
    image_path: str = Field(..., description="The local file path or URL of the image to analyze.")

class InspectImageTool(BaseTool):
    manifest = ToolManifest(
        name="inspect_image",
        description="Analyzes the visual contents of a local image file or URL using YOLOv8 object detection and CLIP classification.",
        arguments_schema=InspectImageInput,
        permission_level="medium",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        image_path = kwargs.get("image_path")
        if not image_path:
            return {"error": "Missing parameter: image_path"}
            
        temp_file = None
        try:
            # 1. Handle URL downloads
            if image_path.startswith("http://") or image_path.startswith("https://"):
                logger.info(f"Downloading remote image for analysis: {image_path}")
                import tempfile
                # Setup custom user agent
                headers = {"User-Agent": "Mozilla/5.0"}
                req = urllib.request.Request(image_path, headers=headers)
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    suffix = Path(image_path).suffix or ".png"
                    if suffix.lower() not in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
                        suffix = ".png"
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                        tmp.write(response.read())
                        temp_file = tmp.name
                path_to_read = temp_file
            else:
                # Local file path
                # Resolve paths relative to home if needed
                resolved_path = Path(image_path)
                if not resolved_path.is_absolute():
                    resolved_path = Path.home() / image_path
                if not resolved_path.exists():
                    return {"error": f"Image file not found: {image_path}"}
                path_to_read = str(resolved_path)
                
            logger.info(f"Reading image bytes from: {path_to_read}")
            with open(path_to_read, "rb") as f:
                img_bytes = f.read()
                
            vision_mgr = Container.resolve("vision_manager")
            
            # Run YOLOv8 detection directly to bypass frame skip throttle for one-off analyses
            logger.info("Running YOLOv8 object detection...")
            objects = vision_mgr.yolo.detect(img_bytes)
            
            # Run CLIP scene classification
            logger.info("Running CLIP scene classification...")
            description = await vision_mgr.classify_scene(img_bytes)
            
            return {
                "status": "success",
                "image_path": image_path,
                "detected_objects": [obj["label"] for obj in objects],
                "object_count": len(objects),
                "description": description,
                "display_image": True,
                "preview_path": path_to_read if not temp_file else None # Serve path to preview in UI if local
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze image: {e}")
            return {"error": f"Failed to analyze image: {str(e)}"}
        finally:
            # Clean up temp downloaded file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
