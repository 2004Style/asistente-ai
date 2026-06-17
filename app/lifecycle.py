"""
Lifecycle manager for the assistant process.

Manages the states of the daemon itself (starting, running, stopping).
"""
import time
import logging
from enum import Enum

logger = logging.getLogger("Lifecycle")

class DaemonState(Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"

class LifecycleManager:
    def __init__(self):
        self.state = DaemonState.STARTING
        self.start_time = time.time()

    def set_state(self, new_state: DaemonState) -> None:
        """Update the running state of the daemon."""
        logger.info(f"Lifecycle state transition: {self.state.value} -> {new_state.value}")
        self.state = new_state

    def get_uptime(self) -> float:
        """Get the daemon uptime in seconds."""
        return time.time() - self.start_time

    def get_status(self) -> dict:
        """Get serializable status details."""
        return {
            "state": self.state.value,
            "uptime_seconds": round(self.get_uptime(), 2),
            "start_time_iso": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.start_time))
        }
