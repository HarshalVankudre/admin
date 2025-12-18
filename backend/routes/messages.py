"""
Message management endpoints.

Provides message listing, search, and error filtering.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Query
from psycopg2 import Error as PsycopgError

from ..database import date_end_exclusive, get_cursor, handle_db_error, to_int

router = APIRouter(prefix="/admin", tags=["messages"])


@router.get("/messages")
def get_messages(
    conversation_id: Optional[int] = None,
    role: Optional[str] = None,
    has_error: Optional[bool] = None,
    search: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get paginated messages with filters."""
    try:
        with get_cursor() as cur:
            # Build main query
            query, params = _build_messages_query(
                conversation_id, role, has_error, search, date_from, date_to
            )
            query += " ORDER BY m.timestamp DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            messages = cur.fetchall()

            # Get total count
            total = _get_messages_count(
                cur, conversation_id, role, has_error, search, date_from, date_to
            )

            return {
                "messages": messages,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    except PsycopgError as e:
        raise handle_db_error(e)


@router.get("/errors")
def get_errors(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
):
    """Get messages with errors (convenience endpoint)."""
    return get_messages(
        has_error=True,
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )


def _build_messages_query(
    conversation_id: Optional[int],
    role: Optional[str],
    has_error: Optional[bool],
    search: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
) -> tuple[str, list[Any]]:
    """Build the messages query with filters."""
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
        params.append(date_end_exclusive(date_to))

    if search:
        query += " AND m.content ILIKE %s"
        params.append(f"%{search}%")

    if has_error is True:
        query += " AND m.error IS NOT NULL"
    elif has_error is False:
        query += " AND m.error IS NULL"

    return query, params


def _get_messages_count(
    cur,
    conversation_id: Optional[int],
    role: Optional[str],
    has_error: Optional[bool],
    search: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
) -> int:
    """Get total message count with filters."""
    query = "SELECT COUNT(*) AS count FROM messages m WHERE 1=1"
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
        params.append(date_end_exclusive(date_to))

    if search:
        query += " AND m.content ILIKE %s"
        params.append(f"%{search}%")

    if has_error is True:
        query += " AND m.error IS NOT NULL"
    elif has_error is False:
        query += " AND m.error IS NULL"

    cur.execute(query, params)
    return to_int((cur.fetchone() or {}).get("count"))
