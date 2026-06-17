"""
Base adapter for Windows hosts.

Defines common functionality for interacting with the Windows operating system.
"""
import logging
from host.adapters.base import BaseHostAdapter

logger = logging.getLogger("WindowsBaseAdapter")

class WindowsBaseAdapter(BaseHostAdapter):
    """Base class containing shared logic for different Windows execution modes."""
    pass
