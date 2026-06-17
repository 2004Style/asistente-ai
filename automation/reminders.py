"""
Handles delayed reminder notifications.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from app.container import Container

logger = logging.getLogger("Reminders")

class ReminderManager:
    def __init__(self):
        pass

    async def set_reminder(self, text: str, delay_seconds: float, session_id: str = "default") -> datetime:
        """Set a reminder that will trigger after delay_seconds."""
        trigger_time = datetime.now() + timedelta(seconds=delay_seconds)
        logger.info(f"Setting reminder: '{text}' in {delay_seconds} seconds (at {trigger_time})")
        
        # Schedule the reminder execution in the background
        asyncio.create_task(self._reminder_task(text, delay_seconds, session_id))
        return trigger_time

    async def _reminder_task(self, text: str, delay_seconds: float, session_id: str):
        await asyncio.sleep(delay_seconds)
        logger.info(f"Reminder triggered: '{text}' for session '{session_id}'")
        
        # Publish event
        try:
            event_bus = Container.resolve("event_bus")
            await event_bus.publish("reminder_triggered", {
                "message": text,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to publish reminder event: {e}")
