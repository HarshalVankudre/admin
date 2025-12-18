"""
Database connection pool and utilities.

Provides thread-safe connection pooling and helper functions for database operations.
"""
from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from datetime import date, timedelta
from typing import Any, Generator

import psycopg2
from fastapi import HTTPException
from psycopg2 import Error as PsycopgError
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from .config import get_settings

logger = logging.getLogger(__name__)

# Module-level connection pool (singleton pattern)
_pool: ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()


def init_pool() -> None:
    """Initialize the database connection pool."""
    global _pool
    
    if _pool is not None:
        return

    with _pool_lock:
        if _pool is not None:
            return
        
        settings = get_settings()
        _pool = ThreadedConnectionPool(
            minconn=settings.db.pool_min,
            maxconn=settings.db.pool_max,
            **settings.db.to_connect_kwargs()
        )
        logger.info("Database connection pool initialized")


def close_pool() -> None:
    """Close the database connection pool."""
    global _pool
    
    with _pool_lock:
        if _pool is None:
            return
        _pool.closeall()
        _pool = None
        logger.info("Database connection pool closed")


@contextmanager
def get_cursor() -> Generator[RealDictCursor, None, None]:
    """
    Context manager for database cursor with automatic connection handling.
    
    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM users")
            results = cur.fetchall()
    """
    init_pool()
    
    if _pool is None:
        raise HTTPException(status_code=503, detail="Database pool not initialized")

    conn = _pool.getconn()
    try:
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
        finally:
            cursor.close()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            _pool.putconn(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass


def handle_db_error(exc: PsycopgError) -> HTTPException:
    """Convert database exceptions to appropriate HTTP exceptions."""
    if isinstance(exc, psycopg2.OperationalError):
        logger.warning("Database unavailable: %s", exc)
        return HTTPException(status_code=503, detail="Database unavailable")
    
    logger.exception("Database query failed")
    return HTTPException(status_code=500, detail="Database query failed")


# ============================================================================
# Utility Functions
# ============================================================================

def to_int(value: Any, *, default: int = 0) -> int:
    """Safely convert a value to integer."""
    if value is None:
        return default
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def date_end_exclusive(date_to: date) -> date:
    """Convert end date to exclusive (add one day for < comparison)."""
    return date_to + timedelta(days=1)
