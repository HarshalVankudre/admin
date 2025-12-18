"""
Statistics and activity endpoints.

Provides dashboard KPIs, charts data, and tool usage analytics.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query
from psycopg2 import Error as PsycopgError

from ..database import get_cursor, handle_db_error, to_int

router = APIRouter(prefix="/admin", tags=["stats"])


@router.get("/stats")
def get_stats():
    """Get dashboard statistics (counts + KPIs)."""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users) AS total_users,
                    (SELECT COUNT(*) FROM conversations) AS total_conversations,
                    (SELECT COUNT(*) FROM messages) AS total_messages,
                    (SELECT COUNT(*) FROM messages 
                     WHERE timestamp >= CURRENT_DATE) AS messages_today,
                    (SELECT COUNT(*) FROM messages 
                     WHERE timestamp >= NOW() - INTERVAL '24 hours') AS messages_24h,
                    (SELECT COUNT(*) FROM messages 
                     WHERE error IS NOT NULL 
                     AND timestamp >= NOW() - INTERVAL '24 hours') AS errors_24h,
                    (SELECT COUNT(*) FROM messages 
                     WHERE role = 'assistant' 
                     AND timestamp >= NOW() - INTERVAL '24 hours') AS assistant_messages_24h,
                    (SELECT COUNT(DISTINCT user_id) FROM conversations 
                     WHERE last_message_at >= CURRENT_DATE) AS active_users_today,
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
            """)
            row = cur.fetchone() or {}

            return {
                "generated_at": datetime.utcnow(),
                "total_users": to_int(row.get("total_users")),
                "total_conversations": to_int(row.get("total_conversations")),
                "total_messages": to_int(row.get("total_messages")),
                "messages_today": to_int(row.get("messages_today")),
                "messages_24h": to_int(row.get("messages_24h")),
                "errors_24h": to_int(row.get("errors_24h")),
                "assistant_messages_24h": to_int(row.get("assistant_messages_24h")),
                "active_users_today": to_int(row.get("active_users_today")),
                "last_message_at": row.get("last_message_at"),
                "avg_response_time_ms_7d": to_int(row.get("avg_response_time_ms_7d")),
                "p50_response_time_ms_7d": to_int(row.get("p50_response_time_ms_7d")),
                "p95_response_time_ms_7d": to_int(row.get("p95_response_time_ms_7d")),
            }
    except PsycopgError as e:
        raise handle_db_error(e)


@router.get("/activity")
def get_activity():
    """Time series for charts (hourly 24h + daily 14d)."""
    try:
        with get_cursor() as cur:
            # Hourly data (last 24 hours)
            cur.execute("""
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
            """)
            hourly = cur.fetchall()

            # Daily data (last 14 days)
            cur.execute("""
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
            """)
            daily = cur.fetchall()

            return {
                "generated_at": datetime.utcnow(),
                "hourly": hourly,
                "daily": daily
            }
    except PsycopgError as e:
        raise handle_db_error(e)


@router.get("/tools")
def get_tools(limit: int = Query(8, ge=1, le=50)):
    """Top tools used by the assistant (last 7 days)."""
    try:
        with get_cursor() as cur:
            cur.execute("""
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
            """, (limit,))
            
            return {
                "generated_at": datetime.utcnow(),
                "tools": cur.fetchall()
            }
    except PsycopgError as e:
        raise handle_db_error(e)
