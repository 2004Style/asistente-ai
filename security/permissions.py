"""
Defines permission levels and verification helpers for tool execution.
"""
from enum import IntEnum

class PermissionLevel(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

    @classmethod
    def from_str(cls, val: str) -> "PermissionLevel":
        val = val.lower()
        if val == "low":
            return cls.LOW
        elif val == "medium":
            return cls.MEDIUM
        elif val == "high":
            return cls.HIGH
        elif val == "critical":
            return cls.CRITICAL
        return cls.LOW
