"""
Unit tests for the new features: dynamic directory mapping, confirmation bypass,
incremental project directories, and clean vision descriptors.
"""
import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.web.actions.download_media import resolve_directory, DownloadMediaTool
from tools.workspace.actions.create_project import CreateProjectTool
from tools.files.actions.write_file import WriteFileTool
from security.confirmation import ConfirmationManager
from vision.detectors.clip import CLIPClassifier
from app.container import Container

@pytest.mark.anyio
async def test_resolve_directory_defaults():
    # Test project default path
    proj_dir = resolve_directory(None, default_type="projects")
    assert proj_dir == Path.home() / "rbot" / "projects"
    assert proj_dir.exists()

    # Test music default path
    music_dir = resolve_directory(None, default_type="music")
    assert music_dir == Path.home() / "Music"
    assert music_dir.exists()

    # Test videos default path
    videos_dir = resolve_directory(None, default_type="videos")
    assert videos_dir == Path.home() / "Videos"
    assert videos_dir.exists()

    # Test downloads default path
    downloads_dir = resolve_directory(None, default_type="downloads")
    assert downloads_dir == Path.home() / "Downloads"
    assert downloads_dir.exists()

    # Test Spanish mappings
    assert resolve_directory("descargas") == Path.home() / "Downloads"
    assert resolve_directory("documentos") == Path.home() / "Documents"
    assert resolve_directory("escritorio") == Path.home() / "Desktop"

@pytest.mark.anyio
async def test_create_project_unique_directories(tmp_path):
    tool = CreateProjectTool()
    
    # Create first project
    res1 = await tool.execute(
        project_name="tienda",
        files=[{"path": "index.html", "content": "hello"}],
        base_dir=str(tmp_path)
    )
    assert res1["status"] == "success"
    assert Path(res1["project_dir"]) == tmp_path / "tienda"
    assert (tmp_path / "tienda").exists()

    # Create duplicate project (should append _1)
    res2 = await tool.execute(
        project_name="tienda",
        files=[{"path": "index.html", "content": "hello"}],
        base_dir=str(tmp_path)
    )
    assert res2["status"] == "success"
    assert Path(res2["project_dir"]) == tmp_path / "tienda_1"
    assert (tmp_path / "tienda_1").exists()

    # Create third duplicate project (should append _2)
    res3 = await tool.execute(
        project_name="tienda",
        files=[{"path": "index.html", "content": "hello"}],
        base_dir=str(tmp_path)
    )
    assert res3["status"] == "success"
    assert Path(res3["project_dir"]) == tmp_path / "tienda_2"
    assert (tmp_path / "tienda_2").exists()

@pytest.mark.anyio
async def test_write_file_relative_path_redirection():
    tool = WriteFileTool()
    filename = "test_write_relative_redirect.txt"
    
    # Execute with relative filename
    res = await tool.execute(
        file_path=filename,
        content="Contenido de prueba para redireccion"
    )
    assert res["status"] == "success"
    expected_path = Path.home() / "Downloads" / filename
    assert Path(res["file_path"]) == expected_path
    assert expected_path.exists()
    
    # Clean up
    if expected_path.exists():
        expected_path.unlink()

def test_confirmation_manager_read_only_bypass():
    # Setup ToolRegistry mock and container
    from tools.registry import ToolRegistry
    from tools.window.actions.inspect_camera import InspectCameraTool
    from tools.terminal.actions.run_command import RunCommandTool
    
    registry = ToolRegistry()
    registry.register(InspectCameraTool()) # risk: read_only, level: low
    registry.register(RunCommandTool())    # risk: critical, level: high
    
    Container.register("tool_registry", registry)
    
    confirm_mgr = ConfirmationManager(min_permission_level="medium", require_confirmation=True)
    
    # inspect_camera is read_only, should bypass confirmation (return False for needs_confirmation)
    assert confirm_mgr.needs_confirmation("low", "inspect_camera") is False
    assert confirm_mgr.needs_confirmation("medium", "inspect_camera") is False
    assert confirm_mgr.needs_confirmation("high", "inspect_camera") is False

    # run_command is high permission level and NOT read_only, should trigger confirmation (return True)
    assert confirm_mgr.needs_confirmation("medium", "run_command") is True
    assert confirm_mgr.needs_confirmation("high", "run_command") is True

@patch("vision.detectors.clip.CLIPClassifier.classify")
def test_clip_classifier_clean_description(mock_classify):
    # Mock scores returned by classify
    mock_classify.return_value = {
        "a terminal window with code": 0.05,
        "a web browser": 0.95,
        "a video game": 0.01
    }
    
    classifier = CLIPClassifier()
    description = classifier.describe(b"dummy_image_data")
    
    # Assert description only returns the clean label, without confidence scores or prefixes
    assert description == "a web browser"
