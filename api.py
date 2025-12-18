"""
Admin Dashboard API

FastAPI endpoints for the admin dashboard, served from the main app.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta
import logging
import os
import threading
import time
from typing import Any, Optional

import psycopg2
from fastapi import APIRouter, HTTPException, Query
from psycopg2 import Error as PsycopgError
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


_DB_POOL: ThreadedConnectionPool | None = None
_DB_POOL_LOCK = threading.Lock()


def _to_int(value: Any, *, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _date_end_exclusive(date_to: date) -> date:
    return date_to + timedelta(days=1)


def _db_connect_kwargs() -> dict[str, Any]:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "ruko_admin"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
        "connect_timeout": int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "5")),
        "application_name": os.getenv("POSTGRES_APP_NAME", "ruko-admin-dashboard"),
    }


def init_db_pool() -> None:
    global _DB_POOL
    if _DB_POOL is not None:
        return

    with _DB_POOL_LOCK:
        if _DB_POOL is not None:
            return
        minconn = int(os.getenv("DB_POOL_MIN", "1"))
        maxconn = int(os.getenv("DB_POOL_MAX", "10"))
        _DB_POOL = ThreadedConnectionPool(minconn=minconn, maxconn=maxconn, **_db_connect_kwargs())


def close_db_pool() -> None:
    global _DB_POOL
    with _DB_POOL_LOCK:
        if _DB_POOL is None:
            return
        _DB_POOL.closeall()
        _DB_POOL = None


@contextmanager
def db_cursor():
    init_db_pool()
    if _DB_POOL is None:  # pragma: no cover (defensive)
        raise HTTPException(status_code=503, detail="Database pool not initialized")

    conn = _DB_POOL.getconn()
    try:
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
        finally:
            cur.close()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            _DB_POOL.putconn(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass


def _db_http_exception(exc: PsycopgError) -> HTTPException:
    if isinstance(exc, psycopg2.OperationalError):
        logger.warning("Database unavailable: %s", exc)
        return HTTPException(status_code=503, detail="Database unavailable")

    logger.exception("Database query failed")
    return HTTPException(status_code=500, detail="Database query failed")


@router.get("/stats")
def get_stats():
    """Get dashboard statistics (counts + KPIs)."""
    try:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM users) AS total_users,
                    (SELECT COUNT(*) FROM conversations) AS total_conversations,
                    (SELECT COUNT(*) FROM messages) AS total_messages,
                    (SELECT COUNT(*) FROM messages WHERE timestamp >= CURRENT_DATE) AS messages_today,
                    (SELECT COUNT(*) FROM messages WHERE timestamp >= NOW() - INTERVAL '24 hours') AS messages_24h,
                    (SELECT COUNT(*) FROM messages WHERE error IS NOT NULL AND timestamp >= NOW() - INTERVAL '24 hours') AS errors_24h,
                    (SELECT COUNT(*) FROM messages WHERE role = 'assistant' AND timestamp >= NOW() - INTERVAL '24 hours') AS assistant_messages_24h,
                    (SELECT COUNT(DISTINCT user_id) FROM conversations WHERE last_message_at >= CURRENT_DATE) AS active_users_today,
                    (SELECT MAX(timestamp) FROM messages) AS last_message_at,
                    (
                        SELECT ROUND(AVG(response_time_ms))
                        FROM messages
                        WHERE role = 'assistant'
                          AND response_time_ms IS NOT NULL
                          AND timestamp >= NOW() - INTERVAL '7 days'
                    ) AS avg_response_time_ms_7d,
                    (
                        SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY response_time_ms)
                        FROM messages
                        WHERE role = 'assistant'
                          AND response_time_ms IS NOT NULL
                          AND timestamp >= NOW() - INTERVAL '7 days'
                    ) AS p50_response_time_ms_7d,
                    (
                        SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY response_time_ms)
                        FROM messages
                        WHERE role = 'assistant'
                          AND response_time_ms IS NOT NULL
                          AND timestamp >= NOW() - INTERVAL '7 days'
                    ) AS p95_response_time_ms_7d
                """
            )
            row = cur.fetchone() or {}

            return {
                "generated_at": datetime.utcnow(),
                "total_users": _to_int(row.get("total_users")),
                "total_conversations": _to_int(row.get("total_conversations")),
                "total_messages": _to_int(row.get("total_messages")),
                "messages_today": _to_int(row.get("messages_today")),
                "messages_24h": _to_int(row.get("messages_24h")),
                "errors_24h": _to_int(row.get("errors_24h")),
                "assistant_messages_24h": _to_int(row.get("assistant_messages_24h")),
                "active_users_today": _to_int(row.get("active_users_today")),
                "last_message_at": row.get("last_message_at"),
                "avg_response_time_ms_7d": _to_int(row.get("avg_response_time_ms_7d")),
                "p50_response_time_ms_7d": _to_int(row.get("p50_response_time_ms_7d")),
                "p95_response_time_ms_7d": _to_int(row.get("p95_response_time_ms_7d")),
            }
    except PsycopgError as e:
        raise _db_http_exception(e)


@router.get("/activity")
def get_activity():
    """Time series for charts (hourly 24h + daily 14d)."""
    try:
        with db_cursor() as cur:
            cur.execute(
                """
                WITH series AS (
                    SELECT generate_series(
                        date_trunc('hour', NOW() - INTERVAL '23 hours'),
                        date_trunc('hour', NOW()),
                        INTERVAL '1 hour'
                    ) AS bucket
                ),
                counts AS (
                    SELECT
                        date_trunc('hour', timestamp) AS bucket,
                        COUNT(*) AS messages,
                        COUNT(*) FILTER (WHERE error IS NOT NULL) AS errors
                    FROM messages
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    GROUP BY 1
                )
                SELECT
                    s.bucket,
                    COALESCE(c.messages, 0) AS messages,
                    COALESCE(c.errors, 0) AS errors
                FROM series s
                LEFT JOIN counts c USING (bucket)
                ORDER BY s.bucket
                """
            )
            hourly = cur.fetchall()

            cur.execute(
                """
                WITH series AS (
                    SELECT generate_series(
                        date_trunc('day', NOW() - INTERVAL '13 days'),
                        date_trunc('day', NOW()),
                        INTERVAL '1 day'
                    ) AS bucket
                ),
                counts AS (
                    SELECT
                        date_trunc('day', timestamp) AS bucket,
                        COUNT(*) AS messages,
                        COUNT(*) FILTER (WHERE error IS NOT NULL) AS errors
                    FROM messages
                    WHERE timestamp >= NOW() - INTERVAL '14 days'
                    GROUP BY 1
                )
                SELECT
                    s.bucket,
                    COALESCE(c.messages, 0) AS messages,
                    COALESCE(c.errors, 0) AS errors
                FROM series s
                LEFT JOIN counts c USING (bucket)
                ORDER BY s.bucket
                """
            )
            daily = cur.fetchall()

            return {"generated_at": datetime.utcnow(), "hourly": hourly, "daily": daily}
    except PsycopgError as e:
        raise _db_http_exception(e)


@router.get("/tools")
def get_tools(limit: int = Query(8, ge=1, le=50)):
    """Top tools used by the assistant (last 7 days)."""
    try:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT tool, COUNT(*) AS count
                FROM (
                    SELECT unnest(tools_used) AS tool
                    FROM messages
                    WHERE tools_used IS NOT NULL
                      AND timestamp >= NOW() - INTERVAL '7 days'
                ) t
                GROUP BY tool
                ORDER BY count DESC
                LIMIT %s
                """,
                (limit,),
            )
            return {"generated_at": datetime.utcnow(), "tools": cur.fetchall()}
    except PsycopgError as e:
        raise _db_http_exception(e)


@router.get("/db-health")
def db_health():
    """Database connectivity and latency check."""
    try:
        start = time.perf_counter()
        with db_cursor() as cur:
            cur.execute("SELECT NOW() AS server_time")
            server_time = (cur.fetchone() or {}).get("server_time")
        latency_ms = int(round((time.perf_counter() - start) * 1000))
        return {"status": "ok", "latency_ms": latency_ms, "server_time": server_time}
    except PsycopgError as e:
        raise _db_http_exception(e)


@router.get("/users")
def get_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
):
    """Get list of all users."""
    try:
        with db_cursor() as cur:
            query = """
                SELECT
                    u.*,
                    COUNT(DISTINCT c.id) AS conversation_count,
                    COUNT(m.id) AS message_count,
                    COUNT(m.id) FILTER (WHERE m.error IS NOT NULL) AS error_count
                FROM users u
                LEFT JOIN conversations c ON u.id = c.user_id
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE 1=1
            """
            params: list[Any] = []

            if search:
                query += " AND (u.display_name ILIKE %s OR u.email ILIKE %s OR u.ms_user_id ILIKE %s)"
                like = f"%{search}%"
                params.extend([like, like, like])

            query += " GROUP BY u.id ORDER BY u.last_active DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            users = cur.fetchall()

            count_query = "SELECT COUNT(*) AS count FROM users u WHERE 1=1"
            count_params: list[Any] = []
            if search:
                count_query += " AND (u.display_name ILIKE %s OR u.email ILIKE %s OR u.ms_user_id ILIKE %s)"
                like = f"%{search}%"
                count_params.extend([like, like, like])

            cur.execute(count_query, count_params)
            total = _to_int((cur.fetchone() or {}).get("count"))

            return {"users": users, "total": total, "limit": limit, "offset": offset}
    except PsycopgError as e:
        raise _db_http_exception(e)


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    conversations_limit: int = Query(25, ge=1, le=200),
    conversations_offset: int = Query(0, ge=0),
):
    """Get a user plus their conversations (paged)."""
    try:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    u.*,
                    COUNT(DISTINCT c.id) AS conversation_count,
                    COUNT(m.id) AS message_count,
                    COUNT(m.id) FILTER (WHERE m.error IS NOT NULL) AS error_count
                FROM users u
                LEFT JOIN conversations c ON u.id = c.user_id
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE u.id = %s
                GROUP BY u.id
                """,
                (user_id,),
            )
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            cur.execute(
                """
                SELECT
                    c.*,
                    COALESCE(ms.error_count, 0) AS error_count,
                    COALESCE(ms.avg_assistant_response_time_ms, 0) AS avg_assistant_response_time_ms
                FROM conversations c
                LEFT JOIN (
                    SELECT
                        conversation_id,
                        COUNT(*) FILTER (WHERE error IS NOT NULL) AS error_count,
                        ROUND(
                            AVG(response_time_ms) FILTER (
                                WHERE role = 'assistant' AND response_time_ms IS NOT NULL
                            )
                        ) AS avg_assistant_response_time_ms
                    FROM messages
                    GROUP BY conversation_id
                ) ms ON ms.conversation_id = c.id
                WHERE c.user_id = %s
                ORDER BY c.last_message_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, conversations_limit, conversations_offset),
            )
            conversations = cur.fetchall()

            return {
                "user": user,
                "conversations": conversations,
                "conversations_limit": conversations_limit,
                "conversations_offset": conversations_offset,
            }
    except PsycopgError as e:
        raise _db_http_exception(e)


@router.get("/conversations")
def get_conversations(
    user_id: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    has_error: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get list of conversations with filters."""
    try:
        with db_cursor() as cur:
            query = """
                SELECT
                    c.*,
                    u.display_name,
                    u.email,
                    u.ms_user_id,
                    COALESCE(ms.error_count, 0) AS error_count,
                    COALESCE(ms.avg_assistant_response_time_ms, 0) AS avg_assistant_response_time_ms,
                    ms.last_error_at
                FROM conversations c
                LEFT JOIN users u ON c.user_id = u.id
                LEFT JOIN (
                    SELECT
                        conversation_id,
                        COUNT(*) FILTER (WHERE error IS NOT NULL) AS error_count,
                        MAX(timestamp) FILTER (WHERE error IS NOT NULL) AS last_error_at,
                        ROUND(
                            AVG(response_time_ms) FILTER (
                                WHERE role = 'assistant' AND response_time_ms IS NOT NULL
                            )
                        ) AS avg_assistant_response_time_ms
                    FROM messages
                    GROUP BY conversation_id
                ) ms ON ms.conversation_id = c.id
                WHERE 1=1
            """
            params: list[Any] = []

            if user_id is not None:
                query += " AND c.user_id = %s"
                params.append(user_id)

            if date_from is not None:
                query += " AND c.started_at >= %s"
                params.append(date_from)

            if date_to is not None:
                query += " AND c.started_at < %s"
                params.append(_date_end_exclusive(date_to))

            if has_error is True:
                query += " AND COALESCE(ms.error_count, 0) > 0"
            elif has_error is False:
                query += " AND COALESCE(ms.error_count, 0) = 0"

            if search:
                query += " AND (u.display_name ILIKE %s OR u.email ILIKE %s OR u.ms_user_id ILIKE %s)"
                like = f"%{search}%"
                params.extend([like, like, like])

            query += " ORDER BY c.last_message_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            conversations = cur.fetchall()

            count_query = """
                SELECT COUNT(*) AS count
                FROM conversations c
                LEFT JOIN users u ON c.user_id = u.id
                LEFT JOIN (
                    SELECT
                        conversation_id,
                        COUNT(*) FILTER (WHERE error IS NOT NULL) AS error_count
                    FROM messages
                    GROUP BY conversation_id
                ) ms ON ms.conversation_id = c.id
                WHERE 1=1
            """
            count_params: list[Any] = []
            if user_id is not None:
                count_query += " AND c.user_id = %s"
                count_params.append(user_id)
            if date_from is not None:
                count_query += " AND c.started_at >= %s"
                count_params.append(date_from)
            if date_to is not None:
                count_query += " AND c.started_at < %s"
                count_params.append(_date_end_exclusive(date_to))
            if has_error is True:
                count_query += " AND COALESCE(ms.error_count, 0) > 0"
            elif has_error is False:
                count_query += " AND COALESCE(ms.error_count, 0) = 0"
            if search:
                count_query += " AND (u.display_name ILIKE %s OR u.email ILIKE %s OR u.ms_user_id ILIKE %s)"
                like = f"%{search}%"
                count_params.extend([like, like, like])

            cur.execute(count_query, count_params)
            total = _to_int((cur.fetchone() or {}).get("count"))

            return {"conversations": conversations, "total": total, "limit": limit, "offset": offset}
    except PsycopgError as e:
        raise _db_http_exception(e)


@router.get("/conversations/{conversation_id}")
def get_conversation_detail(conversation_id: int):
    """Get conversation with all messages."""
    try:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.*,
                    u.display_name,
                    u.email,
                    u.ms_user_id,
                    COALESCE(ms.total_messages, 0) AS total_messages,
                    COALESCE(ms.user_messages, 0) AS user_messages,
                    COALESCE(ms.assistant_messages, 0) AS assistant_messages,
                    COALESCE(ms.error_count, 0) AS error_count,
                    COALESCE(ms.avg_assistant_response_time_ms, 0) AS avg_assistant_response_time_ms,
                    ms.first_message_at,
                    ms.last_message_at
                FROM conversations c
                LEFT JOIN users u ON c.user_id = u.id
                LEFT JOIN (
                    SELECT
                        conversation_id,
                        COUNT(*) AS total_messages,
                        COUNT(*) FILTER (WHERE role = 'user') AS user_messages,
                        COUNT(*) FILTER (WHERE role = 'assistant') AS assistant_messages,
                        COUNT(*) FILTER (WHERE error IS NOT NULL) AS error_count,
                        MIN(timestamp) AS first_message_at,
                        MAX(timestamp) AS last_message_at,
                        ROUND(
                            AVG(response_time_ms) FILTER (
                                WHERE role = 'assistant' AND response_time_ms IS NOT NULL
                            )
                        ) AS avg_assistant_response_time_ms
                    FROM messages
                    WHERE conversation_id = %s
                    GROUP BY conversation_id
                ) ms ON ms.conversation_id = c.id
                WHERE c.id = %s
                """,
                (conversation_id, conversation_id),
            )
            conversation = cur.fetchone()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            cur.execute(
                """
                SELECT
                    id,
                    conversation_id,
                    role,
                    content,
                    timestamp,
                    response_time_ms,
                    tools_used,
                    sql_query,
                    sql_results_count,
                    error
                FROM messages
                WHERE conversation_id = %s
                ORDER BY timestamp ASC
                """,
                (conversation_id,),
            )
            messages = cur.fetchall()

            return {"conversation": conversation, "messages": messages}
    except PsycopgError as e:
        raise _db_http_exception(e)


@router.get("/messages")
def get_messages(
    conversation_id: Optional[int] = None,
    role: Optional[str] = None,
    has_error: Optional[bool] = None,
    search: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get messages with filters."""
    try:
        with db_cursor() as cur:
            query = """
                SELECT
                    m.id,
                    m.conversation_id,
                    m.role,
                    m.content,
                    m.timestamp,
                    m.response_time_ms,
                    m.tools_used,
                    m.sql_query,
                    m.sql_results_count,
                    m.error,
                    u.display_name,
                    u.email,
                    u.ms_user_id
                FROM messages m
                LEFT JOIN conversations c ON m.conversation_id = c.id
                LEFT JOIN users u ON c.user_id = u.id
                WHERE 1=1
            """
            params: list[Any] = []

            if conversation_id is not None:
                query += " AND m.conversation_id = %s"
                params.append(conversation_id)

            if role:
                query += " AND m.role = %s"
                params.append(role)

            if date_from is not None:
                query += " AND m.timestamp >= %s"
                params.append(date_from)

            if date_to is not None:
                query += " AND m.timestamp < %s"
                params.append(_date_end_exclusive(date_to))

            if search:
                query += " AND m.content ILIKE %s"
                params.append(f"%{search}%")

            if has_error is True:
                query += " AND m.error IS NOT NULL"
            elif has_error is False:
                query += " AND m.error IS NULL"

            query += " ORDER BY m.timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            messages = cur.fetchall()

            count_query = "SELECT COUNT(*) AS count FROM messages m WHERE 1=1"
            count_params: list[Any] = []
            if conversation_id is not None:
                count_query += " AND m.conversation_id = %s"
                count_params.append(conversation_id)
            if role:
                count_query += " AND m.role = %s"
                count_params.append(role)
            if date_from is not None:
                count_query += " AND m.timestamp >= %s"
                count_params.append(date_from)
            if date_to is not None:
                count_query += " AND m.timestamp < %s"
                count_params.append(_date_end_exclusive(date_to))
            if search:
                count_query += " AND m.content ILIKE %s"
                count_params.append(f"%{search}%")
            if has_error is True:
                count_query += " AND m.error IS NOT NULL"
            elif has_error is False:
                count_query += " AND m.error IS NULL"

            cur.execute(count_query, count_params)
            total = _to_int((cur.fetchone() or {}).get("count"))

            return {"messages": messages, "total": total, "limit": limit, "offset": offset}
    except PsycopgError as e:
        raise _db_http_exception(e)


@router.get("/errors")
def get_errors(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
):
    """Get messages with errors (paged)."""
    return get_messages(
        has_error=True,
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
