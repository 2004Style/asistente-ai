"""
Defines schemas for tool capabilities, input/output structures, and permission declarations.
"""
from typing import Type
from pydantic import BaseModel, Field

class ToolManifest(BaseModel):
    name: str
    description: str
    arguments_schema: Type[BaseModel]
    permission_level: str = Field(default="low")  # low, medium, high
    risk: str = Field(default="read_only")        # read_only, modification, execution
