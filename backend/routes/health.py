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
    return {"status": "ok", "service": "ruko-admin"}


@router.get("/admin/db-health")
def database_health():
    """Database connectivity and latency check."""
    try:
        start = time.perf_counter()
        with get_cursor() as cur:
            cur.execute("SELECT NOW() AS server_time")
            row = cur.fetchone() or {}
            server_time = row.get("server_time")
        
        latency_ms = int(round((time.perf_counter() - start) * 1000))
        
        return {
            "status": "ok",
            "latency_ms": latency_ms,
            "server_time": server_time
        }
    except PsycopgError as e:
        raise handle_db_error(e)
