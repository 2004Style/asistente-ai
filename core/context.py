"""
Manages conversation context and ephemeral session variables.
"""
from typing import Dict, Any, Optional

class ConversationContext:
    def __init__(self, conversation_id: str = "default"):
        self.conversation_id: str = conversation_id
        self.variables: Dict[str, Any] = {}
        self.current_task: Optional[str] = None

    def set(self, key: str, value: Any) -> None:
        """Set a contextual variable."""
        self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a contextual variable's value."""
        return self.variables.get(key, default)

    def remove(self, key: str) -> None:
        """Remove a contextual variable."""
        self.variables.pop(key, None)

    def clear(self) -> None:
        """Clear all variables and status in the context."""
        self.variables.clear()
        self.current_task = None
