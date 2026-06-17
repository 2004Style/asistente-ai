"""
Unit tests for the tools subsystem of the assistant.
"""
import pytest
from pydantic import BaseModel
from tools.base import BaseTool
from tools.manifest import ToolManifest
from tools.registry import ToolRegistry
from tools.files.actions.read_file import ReadFileTool

class DummyInput(BaseModel):
    val: str

class DummyTool(BaseTool):
    manifest = ToolManifest(
        name="dummy",
        description="A dummy tool for testing.",
        arguments_schema=DummyInput,
        permission_level="low",
        risk="read_only"
    )
    async def execute(self, **kwargs):
        return {"value": kwargs.get("val")}

def test_tool_registry():
    registry = ToolRegistry()
    dummy = DummyTool()
    registry.register(dummy)
    
    assert registry.get_tool("dummy") == dummy
    assert len(registry.list_tools()) == 1
    assert registry.get_tool("missing") is None

@pytest.mark.anyio
async def test_read_file_tool(tmp_path):
    test_file = tmp_path / "hello.txt"
    test_file.write_text("Hello Tools!", encoding="utf-8")
    
    tool = ReadFileTool()
    # Execute tool directly
    result = await tool.execute(file_path=str(test_file))
    
    assert "error" not in result
    assert "Hello Tools!" in result["content"]
