"""
Auditing module to log all tool executions, permissions checks and user approvals.
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("AuditLogger")

class AuditLogger:
    def __init__(self, log_path: str = "data/logs/audit.log"):
        from runtime.paths import resolve_path
        self.log_path = str(resolve_path(log_path))
        # Ensure log folder exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        # Clear log on startup
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                pass
        except Exception as e:
            logger.error(f"Failed to initialize/truncate audit log: {e}")

    def log_action(self, tool_name: str, arguments: Dict[str, Any], permission_level: str, approved: bool, status: str, result: Any = None) -> None:
        """Log a tool execution event to the audit file."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tool_name": tool_name,
            "arguments": arguments,
            "permission_level": permission_level,
            "approved": approved,
            "status": status,
            "result_summary": str(result)[:1000] if result is not None else None
        }
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            # Fallback to standard logging
            logger.info(f"AUDIT: {json.dumps(log_entry)}")
