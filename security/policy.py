"""
Describes the security policy and enforcement rules.
"""
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("SecurityPolicy")

class SecurityPolicy:
    def __init__(self):
        # List of sensitive system file patterns that should never be read/modified
        self.banned_patterns = [
            "/etc/shadow",
            "/etc/passwd",
            "/etc/sudoers",
            "~/.ssh",
            ".ssh/"
        ]

    def validate_action(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Validate if a tool execution complies with security policies."""
        # 1. Path traversal check for file actions
        if "file_path" in arguments:
            path = arguments["file_path"]
            if self._has_traversal_or_banned_files(path):
                logger.warning(f"Security Policy violation: Blocked access to path '{path}'")
                return False
                
        if "source_path" in arguments:
            path = arguments["source_path"]
            if self._has_traversal_or_banned_files(path):
                logger.warning(f"Security Policy violation: Blocked access to source path '{path}'")
                return False
                
        if "dest_path" in arguments:
            path = arguments["dest_path"]
            if self._has_traversal_or_banned_files(path):
                logger.warning(f"Security Policy violation: Blocked access to destination path '{path}'")
                return False

        # 2. Risk checks on CLI arguments for execution actions
        if "app_name" in arguments:
            app = arguments["app_name"]
            # Block shell pipe combinations in name
            if any(char in app for char in [";", "&&", "||", "|", "`", "$"]):
                logger.warning(f"Security Policy violation: Blocked dangerous characters in command '{app}'")
                return False

        return True

    def _has_traversal_or_banned_files(self, path: str) -> bool:
        # Check for directory traversal attempts
        normalized = os.path.normpath(path)
        
        # Check for banned system patterns
        for pattern in self.banned_patterns:
            if pattern in normalized or pattern in path:
                return True
                
        return False
