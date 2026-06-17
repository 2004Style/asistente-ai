"""
Reads a file's content.
"""
import os
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

class ReadFileInput(BaseModel):
    file_path: str = Field(..., description="The absolute or relative path to the file to read.")

class ReadFileTool(BaseTool):
    manifest = ToolManifest(
        name="read_file",
        description="Reads the contents of a file on the host filesystem.",
        arguments_schema=ReadFileInput,
        permission_level="medium",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        file_path = kwargs.get("file_path")
        if not file_path:
            return {"error": "Missing parameter: file_path"}
        
        # Resolve to absolute path
        abs_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_path):
            return {"error": f"File not found: {file_path}"}
            
        if os.path.isdir(abs_path):
            return {"error": f"Path is a directory, not a file: {file_path}"}

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(5000) # Limit read to 5000 chars to avoid overloading LLM context
                if len(content) >= 5000:
                    content += "\n... [TRUNCATED due to size]"
                return {"content": content, "file_path": abs_path}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
