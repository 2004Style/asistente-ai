"""
Writes content to a file.
"""
import os
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("WriteFileTool")

class WriteFileInput(BaseModel):
    file_path: str = Field(..., description="The path of the file to write to.")
    content: str = Field(..., description="The text content to write into the file.")

class WriteFileTool(BaseTool):
    manifest = ToolManifest(
        name="write_file",
        description="Creates or overwrites a file with the specified text content.",
        arguments_schema=WriteFileInput,
        permission_level="high",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        if not file_path or content is None:
            return {"error": "Missing file_path or content"}
            
        # Resolve paths: if relative, default to Downloads folder!
        from pathlib import Path
        path = Path(file_path)
        if not path.is_absolute():
            if file_path.startswith("~"):
                abs_path = str(path.expanduser())
            else:
                from tools.web.actions.download_media import resolve_directory
                downloads_dir = resolve_directory(None, default_type="downloads")
                abs_path = str(downloads_dir / file_path)
        else:
            abs_path = str(path)
            
        logger.info(f"Write file: {abs_path}")
        
        try:
            # Ensure folder exists
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "message": f"Successfully wrote file at {abs_path}.", "file_path": abs_path}
        except Exception as e:
            logger.error(f"Failed to write file: {e}")
            return {"error": str(e)}
