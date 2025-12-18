"""
Conversation management endpoints.

Provides conversation listing and detail views.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from psycopg2 import Error as PsycopgError

from ..database import date_end_exclusive, get_cursor, handle_db_error, to_int

router = APIRouter(prefix="/admin", tags=["conversations"])


@router.get("/conversations")
def get_conversations(
    user_id: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    has_error: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get paginated list of conversations with filters."""
    try:
        with get_cursor() as cur:
            # Build main query
            query, params = _build_conversations_query(
                user_id, search, date_from, date_to, has_error
            )
            query += " ORDER BY c.last_message_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            conversations = cur.fetchall()

            # Get total count
            total = _get_conversations_count(
                cur, user_id, search, date_from, date_to, has_error
            )

            return {
                "conversations": conversations,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    except PsycopgError as e:
        raise handle_db_error(e)


@router.get("/conversations/{conversation_id}")
def get_conversation_detail(conversation_id: int):
    """Get conversation with all messages."""
    try:
        with get_cursor() as cur:
            # Get conversation with aggregated stats
            cur.execute("""
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
            """, (conversation_id, conversation_id))
            
            conversation = cur.fetchone()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            # Get all messages for this conversation
            cur.execute("""
                SELECT
                    id, conversation_id, role, content, timestamp,
                    response_time_ms, tools_used, sql_query, sql_results_count, error
                FROM messages
                WHERE conversation_id = %s
                ORDER BY timestamp ASC
            """, (conversation_id,))
            
            messages = cur.fetchall()

            return {"conversation": conversation, "messages": messages}
    except PsycopgError as e:
        raise handle_db_error(e)


def _build_conversations_query(
    user_id: Optional[int],
    search: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    has_error: Optional[bool],
) -> tuple[str, list[Any]]:
    """Build the conversations query with filters."""
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
        params.append(date_end_exclusive(date_to))

    if has_error is True:
        query += " AND COALESCE(ms.error_count, 0) > 0"
    elif has_error is False:
        query += " AND COALESCE(ms.error_count, 0) = 0"

    if search:
        query += """
            AND (u.display_name ILIKE %s 
                 OR u.email ILIKE %s 
                 OR u.ms_user_id ILIKE %s)
        """
        like_pattern = f"%{search}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    return query, params


def _get_conversations_count(
    cur,
    user_id: Optional[int],
    search: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    has_error: Optional[bool],
) -> int:
    """Get total conversation count with filters."""
    query = """
        SELECT COUNT(*) AS count
        FROM conversations c
        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN (
            SELECT conversation_id, COUNT(*) FILTER (WHERE error IS NOT NULL) AS error_count
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
        params.append(date_end_exclusive(date_to))

    if has_error is True:
        query += " AND COALESCE(ms.error_count, 0) > 0"
    elif has_error is False:
        query += " AND COALESCE(ms.error_count, 0) = 0"

    if search:
        query += """
            AND (u.display_name ILIKE %s 
                 OR u.email ILIKE %s 
                 OR u.ms_user_id ILIKE %s)
        """
        like_pattern = f"%{search}%"
        params.extend([like_pattern, like_pattern, like_pattern])

    cur.execute(query, params)
    return to_int((cur.fetchone() or {}).get("count"))
