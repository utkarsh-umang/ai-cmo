"""Tracked keywords and SERP snapshot storage."""

from __future__ import annotations

from opencmo.storage._db import get_db


async def add_tracked_keyword(project_id: int, keyword: str) -> int:
    """Add a keyword to the tracked list. Returns keyword id."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO tracked_keywords (project_id, keyword) VALUES (?, ?)",
            (project_id, keyword),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM tracked_keywords WHERE project_id = ? AND keyword = ?",
            (project_id, keyword),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def list_tracked_keywords(project_id: int) -> list[dict]:
    """Return all tracked keywords for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, keyword, created_at FROM tracked_keywords WHERE project_id = ? ORDER BY id",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "keyword": r[1], "created_at": r[2]} for r in rows]
    finally:
        await db.close()


async def remove_tracked_keyword(keyword_id: int) -> bool:
    """Remove a tracked keyword by id. Returns True if deleted."""
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM tracked_keywords WHERE id = ?", (keyword_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def save_serp_snapshot(
    project_id: int,
    keyword: str,
    position: int | None,
    url_found: str | None,
    provider: str,
    error: str | None,
) -> int:
    """Save a SERP ranking snapshot. Returns snapshot id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO serp_snapshots
               (project_id, keyword, position, url_found, provider, error)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, keyword, position, url_found, provider, error),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_serp_history(
    project_id: int, keyword: str, limit: int = 20
) -> list[dict]:
    """Return recent SERP snapshots for a project+keyword."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, keyword, position, url_found, provider, error, checked_at
               FROM serp_snapshots
               WHERE project_id = ? AND keyword = ?
               ORDER BY checked_at DESC LIMIT ?""",
            (project_id, keyword, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "keyword": r[1], "position": r[2], "url_found": r[3],
                "provider": r[4], "error": r[5], "checked_at": r[6],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_all_serp_latest(project_id: int) -> list[dict]:
    """Return latest SERP snapshot per keyword for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT keyword, position, url_found, provider, error, checked_at
               FROM serp_snapshots
               WHERE project_id = ?
               AND id IN (
                   SELECT MAX(id) FROM serp_snapshots
                   WHERE project_id = ?
                   GROUP BY keyword
               )
               ORDER BY keyword""",
            (project_id, project_id),
        )
        rows = await cursor.fetchall()
        return [
            {
                "keyword": r[0], "position": r[1], "url_found": r[2],
                "provider": r[3], "error": r[4], "checked_at": r[5],
            }
            for r in rows
        ]
    finally:
        await db.close()
