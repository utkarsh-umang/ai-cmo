"""Chat session storage."""

from __future__ import annotations

from opencmo.storage._db import get_db


async def create_chat_session(
    session_id: str, title: str = "", project_id: int | None = None
) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO chat_sessions (id, title, project_id) VALUES (?, ?, ?)",
            (session_id, title, project_id),
        )
        await db.commit()
    finally:
        await db.close()


async def list_chat_sessions() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.id, s.title, s.created_at, s.updated_at, s.project_id, p.brand_name
               FROM chat_sessions s
               LEFT JOIN projects p ON p.id = s.project_id
               ORDER BY s.updated_at DESC, s.id DESC"""
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "title": r[1],
                "created_at": r[2],
                "updated_at": r[3],
                "project_id": r[4],
                "project_name": r[5],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_chat_session(session_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.id, s.title, s.input_items, s.created_at, s.updated_at, s.project_id, p.brand_name
               FROM chat_sessions s
               LEFT JOIN projects p ON p.id = s.project_id
               WHERE s.id = ?""",
            (session_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "title": row[1], "input_items": row[2],
            "created_at": row[3], "updated_at": row[4],
            "project_id": row[5], "project_name": row[6],
        }
    finally:
        await db.close()


async def update_chat_session(
    session_id: str, input_items_json: str, title: str | None = None
) -> None:
    db = await get_db()
    try:
        if title is not None:
            await db.execute(
                "UPDATE chat_sessions SET input_items = ?, title = ?, updated_at = datetime('now') WHERE id = ?",
                (input_items_json, title, session_id),
            )
        else:
            await db.execute(
                "UPDATE chat_sessions SET input_items = ?, updated_at = datetime('now') WHERE id = ?",
                (input_items_json, session_id),
            )
        await db.commit()
    finally:
        await db.close()


async def delete_chat_session(session_id: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def clear_chat_sessions() -> None:
    db = await get_db()
    try:
        await db.execute("DELETE FROM chat_sessions")
        await db.commit()
    finally:
        await db.close()
