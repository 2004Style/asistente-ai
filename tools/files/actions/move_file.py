"""
Moves a file.
"""
import shutil
import os
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("MoveFileTool")

class MoveFileInput(BaseModel):
    source_path: str = Field(..., description="The current path of the file.")
    dest_path: str = Field(..., description="The target path where the file should be moved.")

class MoveFileTool(BaseTool):
    manifest = ToolManifest(
        name="move_file",
        description="Moves or renames a file on the host filesystem.",
        arguments_schema=MoveFileInput,
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
        
        logger.info(f"Move file: {src_abs} -> {dest_abs}")
        
        if not os.path.exists(src_abs):
            return {"error": f"Source file does not exist: {src}"}
            
        try:
            # Ensure target folder exists
            os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
            shutil.move(src_abs, dest_abs)
            return {"status": "success", "message": f"Successfully moved file to {dest_abs}."}
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return {"error": str(e)}
