"""
Defines message formats and history management for LLM interactions.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
