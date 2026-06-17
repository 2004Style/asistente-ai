"""
Deletes a file.
"""
import os
import logging
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

logger = logging.getLogger("DeleteFileTool")

class DeleteFileInput(BaseModel):
    file_path: str = Field(..., description="The path of the file to delete.")

class DeleteFileTool(BaseTool):
    manifest = ToolManifest(
        name="delete_file",
        description="Deletes a file from the host filesystem.",
        arguments_schema=DeleteFileInput,
        permission_level="high",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        file_path = kwargs.get("file_path")
        if not file_path:
            return {"error": "Missing file_path"}
            
        abs_path = os.path.abspath(file_path)
        logger.info(f"Delete file request: {abs_path}")
        
        if not os.path.exists(abs_path):
            return {"error": f"File not found: {file_path}"}
            
        if os.path.isdir(abs_path):
            return {"error": f"Path is a directory. delete_file only deletes files: {file_path}"}
            
        try:
            os.remove(abs_path)
            return {"status": "success", "message": f"Successfully deleted file {abs_path}."}
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return {"error": str(e)}
