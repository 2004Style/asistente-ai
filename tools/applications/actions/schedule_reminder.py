"""
Schedules a future reminder task.
"""
import logging
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any
from tools.base import BaseTool
from tools.manifest import ToolManifest
from app.container import Container

logger = logging.getLogger("ScheduleReminderTool")

class ScheduleReminderInput(BaseModel):
    text: str = Field(..., description="The reminder message text (e.g., 'Reunión de equipo en 1 hora').")
    datetime_str: str = Field(..., description="The ISO datetime when the reminder should trigger (e.g., '2026-06-17T11:00:00').")

class ScheduleReminderTool(BaseTool):
    manifest = ToolManifest(
        name="schedule_reminder",
        description="Schedules a future reminder or task notification. Computes the delay and runs it in the background.",
        arguments_schema=ScheduleReminderInput,
        permission_level="low",
        risk="read_only"
    )

    async def execute(self, **kwargs) -> Any:
        text = kwargs.get("text")
        datetime_str = kwargs.get("datetime_str")
        
        if not text or not datetime_str:
            return {"error": "Missing parameters: text and datetime_str are required."}
            
        try:
            # Parse target datetime
            target_dt = datetime.fromisoformat(datetime_str)
            now = datetime.now()
            
            delay_seconds = (target_dt - now).total_seconds()
            
            if delay_seconds <= 0:
                return {"error": f"Target datetime {datetime_str} must be in the future. Current time is {now.isoformat()}"}
                
            reminder_mgr = Container.resolve("reminder_manager")
            trigger_time = await reminder_mgr.set_reminder(text, delay_seconds)
            
            return {
                "status": "success",
                "text": text,
                "trigger_time": trigger_time.isoformat(),
                "delay_seconds": delay_seconds,
                "message": f"Recordatorio programado con éxito para el {trigger_time.isoformat()}"
            }
        except ValueError as ve:
            logger.error(f"Invalid datetime format: {datetime_str}. Error: {ve}")
            return {"error": f"Invalid ISO datetime format: {datetime_str}. Please use 'YYYY-MM-DDTHH:MM:SS' format."}
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {e}")
            return {"error": f"Failed to schedule reminder: {str(e)}"}
