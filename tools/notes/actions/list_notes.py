"""
Lists note files.
"""
import os
from typing import Any
from pathlib import Path
from pydantic import BaseModel
from tools.base import BaseTool
from tools.manifest import ToolManifest

class ListNotesInput(BaseModel):
    pass

class ListNotesTool(BaseTool):
    manifest = ToolManifest(
        name="list_notes",
        description="Lists all markdown and text notes inside the assistant's notes directory.",
        arguments_schema=ListNotesInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        try:
            # Locate data/notes standard directory
            from runtime.paths import resolve_path
            notes_dir = resolve_path("data/notes")
            
            # Ensure folder exists
            notes_dir.mkdir(parents=True, exist_ok=True)
            
            notes = []
            for file in os.listdir(notes_dir):
                if file.endswith((".md", ".txt")):
                    full_path = notes_dir / file
                    stat = full_path.stat()
                    # Get snippet
                    snippet = ""
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            snippet = f.read(100).strip()
                    except Exception:
                        pass
                    
                    notes.append({
                        "filename": file,
                        "size_bytes": stat.st_size,
                        "snippet": snippet,
                        "path": str(full_path)
                    })
            
            return {"notes": notes, "notes_dir": str(notes_dir)}
        except Exception as e:
            return {"error": f"Failed to list notes: {str(e)}"}
