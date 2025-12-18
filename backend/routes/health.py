"""
Health check endpoints.

Provides service and database health monitoring.
"""
from __future__ import annotations

import time

from fastapi import APIRouter
from psycopg2 import Error as PsycopgError

from ..database import get_cursor, handle_db_error

router = APIRouter(tags=["health"])


@router.get("/health")
async def service_health():
    """Service health check."""
    return {"status": "ok", "service": "rueko-admin"}


@router.get("/admin/db-health")
def database_health():
    """Database connectivity, latency, and status check."""
    try:
        start = time.perf_counter()
        with get_cursor() as cur:
            # Get server time
            cur.execute("SELECT NOW() AS server_time")
            row = cur.fetchone() or {}
            server_time = row.get("server_time")
            
            # Get total counts
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users) as total_users,
                    (SELECT COUNT(*) FROM conversations) as total_conversations,
                    (SELECT COUNT(*) FROM messages) as total_messages,
                    (SELECT COUNT(*) FROM messages WHERE timestamp > NOW() - INTERVAL '1 hour') as messages_last_hour,
                    (SELECT COUNT(*) FROM messages WHERE error IS NOT NULL) as total_errors
            """)
            stats = cur.fetchone() or {}
        
        latency_ms = int(round((time.perf_counter() - start) * 1000))
        
        return {
            "status": "ok",
            "latency_ms": latency_ms,
            "server_time": server_time,
            "stats": {
                "users": stats.get("total_users", 0),
                "conversations": stats.get("total_conversations", 0),
                "messages": stats.get("total_messages", 0),
                "messages_last_hour": stats.get("messages_last_hour", 0),
                "errors": stats.get("total_errors", 0),
            }
        }
    except PsycopgError as e:
        raise handle_db_error(e)

