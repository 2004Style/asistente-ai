"""
Background scheduler to run periodic jobs or reminders.
"""
import time
import asyncio
import logging
from typing import Callable, List, Dict, Any

logger = logging.getLogger("Scheduler")

class ScheduledJob:
    def __init__(self, name: str, interval_seconds: float, callback: Callable[..., Any], args, kwargs):
        self.name = name
        self.interval = interval_seconds
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        self.last_run = time.time()

class Scheduler:
    def __init__(self):
        self.jobs: List[ScheduledJob] = []
        self._loop_task = None
        self._running = False

    def add_job(self, name: str, interval_seconds: float, callback: Callable[..., Any], *args, **kwargs) -> None:
        """Register a new periodic job."""
        job = ScheduledJob(name, interval_seconds, callback, args, kwargs)
        self.jobs.append(job)
        logger.info(f"Registered periodic job '{name}' every {interval_seconds}s.")

    def start(self) -> None:
        """Start the scheduler execution loop."""
        self._running = True
        self._loop_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler loop started.")

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            logger.info("Scheduler loop stopped.")

    async def _scheduler_loop(self):
        try:
            while self._running:
                now = time.time()
                for job in self.jobs:
                    if now - job.last_run >= job.interval:
                        job.last_run = now
                        logger.info(f"Triggering scheduled job: '{job.name}'")
                        try:
                            if asyncio.iscoroutinefunction(job.callback):
                                asyncio.create_task(job.callback(*job.args, **job.kwargs))
                            else:
                                job.callback(*job.args, **job.kwargs)
                        except Exception as e:
                            logger.error(f"Error running scheduled job '{job.name}': {e}")
                
                await asyncio.sleep(1) # check once per second
        except asyncio.CancelledError:
            pass
