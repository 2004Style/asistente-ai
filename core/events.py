"""
Defines a simple event bus to publish and subscribe to events (e.g. task start, completion, errors).
"""
import asyncio
import logging
from typing import Dict, List, Callable, Any, Awaitable, Union

logger = logging.getLogger("EventBus")

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Union[None, Awaitable[None]]]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any], Union[None, Awaitable[None]]]) -> None:
        """Subscribe a callback to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], Union[None, Awaitable[None]]]) -> None:
        """Unsubscribe a callback from a specific event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    async def publish(self, event_type: str, data: Any) -> None:
        """Publish an event to all subscribers asynchronously."""
        if event_type not in self._subscribers:
            return

        tasks = []
        for callback in self._subscribers[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(data))
                else:
                    # Execute synchronous callbacks in a separate thread or immediately
                    callback(data)
            except Exception as e:
                logger.error(f"Error running callback for event '{event_type}': {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
