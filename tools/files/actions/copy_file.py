"""
Copies a file to a new destination.
"""
import shutil
import os
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("CopyFileTool")

class CopyFileInput(BaseModel):
    source_path: str = Field(..., description="The path of the source file to copy.")
    dest_path: str = Field(..., description="The target path where the file should be copied.")

class CopyFileTool(BaseTool):
    manifest = ToolManifest(
        name="copy_file",
        description="Copies a file from a source location to a destination location.",
        arguments_schema=CopyFileInput,
        permission_level="medium",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        src = kwargs.get("source_path")
        dest = kwargs.get("dest_path")
        if not src or not dest:
            return {"error": "Missing source_path or dest_path"}
            
        src_abs = os.path.abspath(src)
        dest_abs = os.path.abspath(dest)
        
        logger.info(f"Copy file: {src_abs} -> {dest_abs}")
        
        if not os.path.exists(src_abs):
            return {"error": f"Source file does not exist: {src}"}
            
        try:
            # Ensure target folder exists
            os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
            shutil.copy2(src_abs, dest_abs)
            return {"status": "success", "message": f"Successfully copied file to {dest_abs}."}
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return {"error": str(e)}
