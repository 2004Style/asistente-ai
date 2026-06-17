"""
Creates a programming project with files and folder structures in a specified location.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path
from tools.base import BaseTool
from tools.manifest import ToolManifest
from tools.web.actions.download_media import resolve_directory

logger = logging.getLogger("CreateProjectTool")

class ProjectFile(BaseModel):
    path: str = Field(..., description="Relative file path from the project root (e.g., 'index.html' or 'css/styles.css').")
    content: str = Field(..., description="The code or text content to write to the file.")

class CreateProjectInput(BaseModel):
    project_name: str = Field(..., description="The name of the project folder (e.g., 'tienda', 'calculadora').")
    files: List[ProjectFile] = Field(..., description="The list of files to generate in the project structure.")
    base_dir: Optional[str] = Field(
        None,
        description="The base folder to create the project folder in (e.g., 'descargas', 'documentos', or empty for home/projects)."
    )

class CreateProjectTool(BaseTool):
    manifest = ToolManifest(
        name="create_project",
        description="Generates a multi-file programming project (web apps, scripts, Go/Python programs) in a specified base directory.",
        arguments_schema=CreateProjectInput,
        permission_level="medium",
        risk="modification"
    )

    async def execute(self, **kwargs) -> Any:
        project_name = kwargs.get("project_name")
        files_input = kwargs.get("files")
        base_dir_str = kwargs.get("base_dir")
        
        if not project_name or not files_input:
            return {"error": "Missing parameters: project_name and files are required."}
            
        # Resolve base directory
        # If base_dir_str is empty/None, resolve_directory resolves to the home/rbot/projects
        base_dir = resolve_directory(base_dir_str, default_type="projects")
        
        # Check if project folder exists, and if so, append suffix to make it unique
        project_dir = base_dir / project_name
        if project_dir.exists():
            counter = 1
            while True:
                candidate = base_dir / f"{project_name}_{counter}"
                if not candidate.exists():
                    project_dir = candidate
                    project_name = f"{project_name}_{counter}"
                    break
                counter += 1
        
        try:
            logger.info(f"Creating project '{project_name}' in: {project_dir}")
            project_dir.mkdir(parents=True, exist_ok=True)
            
            created_files = []
            for file_item in files_input:
                # Handle dictionary conversion if input was passed raw
                if isinstance(file_item, dict):
                    file_path_rel = file_item.get("path")
                    file_content = file_item.get("content", "")
                else:
                    file_path_rel = file_item.path
                    file_content = file_item.content
                    
                if not file_path_rel:
                    continue
                    
                # Compute absolute path for file
                full_file_path = project_dir / file_path_rel
                
                # Create parent directories
                full_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write content
                with open(full_file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                    
                created_files.append(file_path_rel)
                
            return {
                "status": "success",
                "project_name": project_name,
                "project_dir": str(project_dir),
                "created_files": created_files,
                "message": f"Proyecto '{project_name}' creado correctamente en: {project_dir}"
            }
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return {"error": f"Failed to create project: {str(e)}"}
