"""
Handles POSIX signals (SIGINT, SIGTERM) to ensure clean process termination.
"""
import signal
import sys
import logging
from typing import Callable

logger = logging.getLogger("Signals")

def setup_signal_handlers(cleanup_callback: Callable[[], None]) -> None:
    """Set up handlers for SIGINT and SIGTERM that trigger the provided cleanup callback."""
    def handle_signal(signum, frame):
        logger.info(f"Signal {signum} caught. Triggering clean shutdown callback...")
        try:
            cleanup_callback()
        except Exception as e:
            logger.error(f"Error executing shutdown callback: {e}")
        finally:
            logger.info("Exiting.")
            sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    logger.info("Signal handlers for SIGINT and SIGTERM registered.")
