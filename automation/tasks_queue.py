"""
Queue to process asynchronous tasks sequentially in the background.
"""
import asyncio
import logging
from typing import Callable, Any

logger = logging.getLogger("TaskQueue")

class TaskQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.worker_task = None

    def start(self) -> None:
        """Start the background worker task."""
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("Task queue worker started.")

    async def stop(self) -> None:
        """Stop the background worker task."""
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Task queue worker stopped.")

    async def add_task(self, name: str, coro_func: Callable[..., Any], *args, **kwargs) -> None:
        """Add a new task to the queue."""
        await self.queue.put((name, coro_func, args, kwargs))
        logger.info(f"Task '{name}' queued.")

    async def _worker(self):
        try:
            while True:
                name, coro_func, args, kwargs = await self.queue.get()
                logger.info(f"Running task '{name}'...")
                try:
                    if asyncio.iscoroutinefunction(coro_func):
                        await coro_func(*args, **kwargs)
                    else:
                        coro_func(*args, **kwargs)
                    logger.info(f"Task '{name}' completed.")
                except Exception as e:
                    logger.error(f"Task '{name}' failed: {e}", exc_info=True)
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            pass
