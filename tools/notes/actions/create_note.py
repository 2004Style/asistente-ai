"""
Creates a new note.
"""
import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

class CreateNoteInput(BaseModel):
    filename: str = Field(..., description="The name of the note file to create (e.g. 'ideas.md' or 'todo.txt').")
    content: str = Field(..., description="The markdown or text content of the note.")

class CreateNoteTool(BaseTool):
    manifest = ToolManifest(
        name="create_note",
        description="Creates a new markdown or text note inside the assistant's notes folder.",
        arguments_schema=CreateNoteInput,
        permission_level="low",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        filename = kwargs.get("filename")
        content = kwargs.get("content")
        if not filename or content is None:
            return {"error": "Missing filename or content"}
            
        try:
            # Resolve to data/notes standard directory
            from runtime.paths import resolve_path
            notes_dir = resolve_path("data/notes")
            notes_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean filename to avoid path traversal
            safe_filename = os.path.basename(filename)
            note_path = notes_dir / safe_filename
            
            with open(note_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return {"status": "success", "message": f"Successfully created note '{safe_filename}'.", "path": str(note_path)}
        except Exception as e:
            return {"error": f"Failed to create note: {str(e)}"}
