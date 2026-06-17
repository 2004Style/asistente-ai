#!/usr/bin/env python3
"""
Entry point for the AI assistant.

This script bootstraps the application and invokes the runtime daemon.
"""
import logging
from app.bootstrap import bootstrap
from app.container import Container
from runtime.instance_lock import InstanceLock
from runtime.signals import setup_signal_handlers
from runtime.daemon import run_daemon

# Bootstrap the container at import time so ASGI/uvicorn works
bootstrap()
logger = logging.getLogger("Main")
from runtime.daemon import app

def main() -> None:
    """Start the assistant."""
    lock = InstanceLock()
    if not lock.acquire():
        logger.error("Another instance of rbot is already running. Exiting.")
        return

    def cleanup():
        logger.info("Performing shutdown cleanups...")
        try:
            if Container.has("scheduler"):
                import asyncio
                sched = Container.resolve("scheduler")
                asyncio.run(sched.stop())
            if Container.has("task_queue"):
                import asyncio
                tq = Container.resolve("task_queue")
                asyncio.run(tq.stop())
        except Exception as e:
            logger.error(f"Error during async components shutdown: {e}")
        lock.release()

    setup_signal_handlers(cleanup)

    try:
        config = Container.resolve("config")
        run_daemon(host=config.app.host, port=config.app.port)
    except Exception as e:
        logger.exception("An error occurred in the daemon runtime:")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
