"""
Deletes a specified note.
"""
import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

class DeleteNoteInput(BaseModel):
    filename: str = Field(..., description="The name of the note file to delete (e.g. 'ideas.md').")

class DeleteNoteTool(BaseTool):
    manifest = ToolManifest(
        name="delete_note",
        description="Permanently deletes a markdown or text note inside the assistant's notes folder.",
        arguments_schema=DeleteNoteInput,
        permission_level="medium",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        filename = kwargs.get("filename")
        if not filename:
            return {"error": "Missing filename"}
            
        try:
            from runtime.paths import resolve_path
            notes_dir = resolve_path("data/notes")
            
            safe_filename = os.path.basename(filename)
            note_path = notes_dir / safe_filename
            
            if not note_path.exists():
                return {"error": f"Note file not found: {safe_filename}"}
                
            os.remove(note_path)
            return {"status": "success", "message": f"Successfully deleted note '{safe_filename}'."}
        except Exception as e:
            return {"error": f"Failed to delete note: {str(e)}"}
