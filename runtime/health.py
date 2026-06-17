"""
Defines a health check endpoint for monitoring the service.

Exposes a /healthz endpoint to report liveness and readiness.
"""
from typing import Dict, Any
import sqlite3
from app.container import Container

def check_health() -> Dict[str, Any]:
    """Check the health status of various subsystems (DB, Config, memory)."""
    status = "ok"
    details = {}
    
    # 1. Check database connection
    try:
        config = Container.resolve("config")
        db_path = config.memory.db_path
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
        details["database"] = "ok"
    except Exception as e:
        status = "degraded"
        details["database"] = f"error: {str(e)}"
        
    # 2. Check config
    try:
        Container.resolve("config")
        details["config"] = "ok"
    except Exception as e:
        status = "degraded"
        details["config"] = f"error: {str(e)}"

    # 3. Check memory manager
    try:
        Container.resolve("memory_manager")
        details["memory_manager"] = "ok"
    except Exception as e:
        status = "degraded"
        details["memory_manager"] = f"error: {str(e)}"

    return {
        "status": status,
        "details": details
    }
