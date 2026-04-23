"""Competitor and competitor keyword storage."""

from __future__ import annotations

from opencmo.storage._db import get_db


async def add_competitor(
    project_id: int, name: str, url: str | None = None, category: str | None = None
) -> int:
    """Add a competitor. Returns competitor id."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO competitors (project_id, name, url, category) VALUES (?, ?, ?, ?)",
            (project_id, name, url, category),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM competitors WHERE project_id = ? AND name = ?",
            (project_id, name),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def list_competitors(project_id: int) -> list[dict]:
    """Return all competitors for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, name, url, category, created_at FROM competitors WHERE project_id = ? ORDER BY id",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "name": r[1], "url": r[2], "category": r[3], "created_at": r[4]}
            for r in rows
        ]
    finally:
        await db.close()


async def get_competitor(competitor_id: int) -> dict | None:
    """Return a single competitor by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, project_id, name, url FROM competitors WHERE id = ?",
            (competitor_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {"id": row[0], "project_id": row[1], "name": row[2], "url": row[3]}
    finally:
        await db.close()


async def remove_competitor(competitor_id: int) -> bool:
    """Remove a competitor and its keywords."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM competitor_keywords WHERE competitor_id = ?", (competitor_id,))
        cursor = await db.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def add_competitor_keyword(competitor_id: int, keyword: str) -> int:
    """Add a keyword to a competitor. Returns keyword id."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO competitor_keywords (competitor_id, keyword) VALUES (?, ?)",
            (competitor_id, keyword),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM competitor_keywords WHERE competitor_id = ? AND keyword = ?",
            (competitor_id, keyword),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def list_competitor_keywords(competitor_id: int) -> list[dict]:
    """Return all keywords for a competitor."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, keyword, created_at FROM competitor_keywords WHERE competitor_id = ? ORDER BY id",
            (competitor_id,),
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "keyword": r[1], "created_at": r[2]} for r in rows]
    finally:
        await db.close()


async def batch_list_competitor_keywords(competitor_ids: list[int]) -> dict[int, list[dict]]:
    """Batch fetch keywords for multiple competitors. Returns {competitor_id: [keywords]} dict."""
    if not competitor_ids:
        return {}

    db = await get_db()
    try:
        # Build placeholders for IN clause
        placeholders = ",".join("?" * len(competitor_ids))
        cursor = await db.execute(
            f"SELECT competitor_id, id, keyword, created_at FROM competitor_keywords "
            f"WHERE competitor_id IN ({placeholders}) ORDER BY competitor_id, id",
            competitor_ids,
        )
        rows = await cursor.fetchall()

        # Group by competitor_id
        result: dict[int, list[dict]] = {cid: [] for cid in competitor_ids}
        for row in rows:
            comp_id = row[0]
            result[comp_id].append({
                "id": row[1],
                "keyword": row[2],
                "created_at": row[3],
            })

        return result
    finally:
        await db.close()
