"""
User management endpoints.

Provides user listing and detail views.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from psycopg2 import Error as PsycopgError

from ..database import get_cursor, handle_db_error, to_int

router = APIRouter(prefix="/admin", tags=["users"])


@router.get("/users")
def get_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
):
    """Get paginated list of users with aggregated stats."""
    try:
        with get_cursor() as cur:
            # Build query with optional search filter
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
                query += """
                    AND (u.display_name ILIKE %s 
                         OR u.email ILIKE %s 
                         OR u.ms_user_id ILIKE %s)
                """
                like_pattern = f"%{search}%"
                params.extend([like_pattern, like_pattern, like_pattern])

            query += " GROUP BY u.id ORDER BY u.last_active DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            users = cur.fetchall()

            # Get total count for pagination
            total = _get_user_count(cur, search)

            return {
                "users": users,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    except PsycopgError as e:
        raise handle_db_error(e)


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    conversations_limit: int = Query(25, ge=1, le=200),
    conversations_offset: int = Query(0, ge=0),
):
    """Get user details with their conversations."""
    try:
        with get_cursor() as cur:
            # Get user with aggregated stats
            cur.execute("""
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
            """, (user_id,))
            
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Get user's conversations
            cur.execute("""
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
            """, (user_id, conversations_limit, conversations_offset))
            
            conversations = cur.fetchall()

            return {
                "user": user,
                "conversations": conversations,
                "conversations_limit": conversations_limit,
                "conversations_offset": conversations_offset,
            }
    except PsycopgError as e:
        raise handle_db_error(e)


def _get_user_count(cur, search: Optional[str]) -> int:
    """Get total user count with optional search filter."""
    query = "SELECT COUNT(*) AS count FROM users u WHERE 1=1"
    params: list[Any] = []
    
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
