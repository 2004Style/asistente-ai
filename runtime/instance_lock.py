"""
Prevents running multiple instances of the assistant daemon concurrently using a file lock.
"""
import os
import sys
import fcntl
import logging

logger = logging.getLogger("InstanceLock")

class InstanceLock:
    def __init__(self, lock_file: str = "data/rbot.lock"):
        from runtime.paths import resolve_path
        self.lock_file = str(resolve_path(lock_file))
        self.fp = None

    def acquire(self) -> bool:
        """Acquire an exclusive lock. Returns True if successful, False if already locked."""
        # Ensure data folder exists
        os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
        try:
            self.fp = open(self.lock_file, "w")
            # Acquire exclusive lock in a non-blocking way
            fcntl.flock(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fp.write(str(os.getpid()))
            self.fp.flush()
            logger.info(f"Lock acquired on {self.lock_file} with PID {os.getpid()}")
            return True
        except (IOError, OSError):
            logger.warning("Failed to acquire lock. Another instance is already running.")
            return False

    def release(self) -> None:
        """Release the file lock and clean up the lockfile."""
        if self.fp:
            try:
                fcntl.flock(self.fp, fcntl.LOCK_UN)
                self.fp.close()
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
                logger.info("Lock released.")
            except Exception as e:
                logger.error(f"Error releasing lock: {e}")
            finally:
                self.fp = None
