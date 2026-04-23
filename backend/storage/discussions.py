"""Community discussion tracking and snapshots."""

from __future__ import annotations

from opencmo.storage._db import get_db


async def upsert_tracked_discussion(project_id: int, hit: dict) -> int:
    """Upsert a tracked discussion from a DiscussionHit dict. Returns discussion id."""
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO tracked_discussions (project_id, platform, detail_id, title, url)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(project_id, platform, detail_id)
               DO UPDATE SET last_checked_at = datetime('now'), title = excluded.title""",
            (project_id, hit["platform"], hit["detail_id"], hit["title"], hit["url"]),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM tracked_discussions WHERE project_id = ? AND platform = ? AND detail_id = ?",
            (project_id, hit["platform"], hit["detail_id"]),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def save_discussion_snapshot(
    discussion_id: int,
    raw_score: int,
    comments_count: int,
    engagement_score: int,
) -> int:
    """Save a discussion engagement snapshot. Returns snapshot id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO discussion_snapshots
               (discussion_id, raw_score, comments_count, engagement_score)
               VALUES (?, ?, ?, ?)""",
            (discussion_id, raw_score, comments_count, engagement_score),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_tracked_discussions(project_id: int) -> list[dict]:
    """Return tracked discussions with latest snapshot for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT td.id, td.platform, td.detail_id, td.title, td.url,
                      td.first_seen_at, td.last_checked_at,
                      ds.raw_score, ds.comments_count, ds.engagement_score
               FROM tracked_discussions td
               LEFT JOIN discussion_snapshots ds ON ds.discussion_id = td.id
                 AND ds.id = (SELECT MAX(id) FROM discussion_snapshots WHERE discussion_id = td.id)
               WHERE td.project_id = ?
               ORDER BY ds.engagement_score DESC NULLS LAST""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "platform": r[1], "detail_id": r[2], "title": r[3],
                "url": r[4], "first_seen_at": r[5], "last_checked_at": r[6],
                "raw_score": r[7], "comments_count": r[8], "engagement_score": r[9],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_discussion_snapshots(discussion_id: int) -> list[dict]:
    """Return all snapshots for a discussion (time series)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, checked_at, raw_score, comments_count, engagement_score
               FROM discussion_snapshots WHERE discussion_id = ? ORDER BY checked_at""",
            (discussion_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "checked_at": r[1], "raw_score": r[2],
                "comments_count": r[3], "engagement_score": r[4],
            }
            for r in rows
        ]
    finally:
        await db.close()
