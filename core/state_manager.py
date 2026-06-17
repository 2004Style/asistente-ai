"""
Manages conversational and assistant runtime states.
"""
import logging
from enum import Enum
from typing import Dict, Any, Optional
from core.events import EventBus

logger = logging.getLogger("StateManager")

class AssistantState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    LISTENING = "listening"
    SPEAKING = "speaking"
    ERROR = "error"

class StateManager:
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self._state = AssistantState.IDLE
        self._history: Dict[str, Any] = {}

    @property
    def state(self) -> AssistantState:
        """Get current assistant state."""
        return self._state

    async def transition_to(self, new_state: AssistantState) -> None:
        """Transition assistant to a new state and notify subscribers."""
        if self._state == new_state:
            return

        old_state = self._state
        self._state = new_state
        logger.info(f"State transition: {old_state} -> {new_state}")

        if self.event_bus:
            await self.event_bus.publish("state_changed", {
                "old_state": old_state.value,
                "new_state": new_state.value
            })

    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Retrieve historical state for a specific session."""
        if session_id not in self._history:
            self._history[session_id] = {
                "messages": [],
                "metadata": {}
            }
        return self._history[session_id]
