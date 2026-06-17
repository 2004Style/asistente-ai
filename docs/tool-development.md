# Tool Development Guide

Every tool in `rbot` inherits from the `BaseTool` class and provides a `ToolManifest` containing metadata.

## Structure of a Tool

```python
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest

class ExampleInput(BaseModel):
    param: str = Field(..., description="An example parameter.")

class ExampleTool(BaseTool):
    manifest = ToolManifest(
        name="example_tool",
        description="Does something example-like.",
        arguments_schema=ExampleInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> dict:
        param = kwargs.get("param")
        return {"status": "success", "result": f"Processed {param}"}
```

Register your tool by adding it to `tools/registry.py`.
