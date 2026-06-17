"""
Implements controlled shutdown of the assistant.

Ensures resources are cleaned up properly when stopping.
"""
import logging
from app.container import Container

logger = logging.getLogger("Shutdown")

async def shutdown_all() -> None:
    """Shut down all systems and release resources."""
    logger.info("Initiating graceful shutdown of assistant subsystems...")
    
    # 1. Stop TaskQueue and Scheduler
    try:
        scheduler = Container.resolve("scheduler")
        if hasattr(scheduler, "stop"):
            await scheduler.stop()
            logger.info("Scheduler stopped.")
    except Exception as e:
        logger.debug(f"Failed to stop scheduler: {e}")

    try:
        task_queue = Container.resolve("task_queue")
        if hasattr(task_queue, "stop"):
            await task_queue.stop()
            logger.info("Task queue stopped.")
    except Exception as e:
        logger.debug(f"Failed to stop task queue: {e}")
        
    # 2. Release InstanceLock
    try:
        if Container.has("instance_lock"):
            lock = Container.resolve("instance_lock")
            lock.release()
    except Exception as e:
        logger.debug(f"Failed to release instance lock: {e}")

    logger.info("Shutdown sequence completed.")
