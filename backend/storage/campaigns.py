"""Campaign runs and artifacts storage."""

from __future__ import annotations

import json

from opencmo.storage._db import get_db


async def create_campaign_run(
    project_id: int, goal: str, channels: list[str],
) -> dict:
    """Create a new campaign run."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO campaign_runs (project_id, goal, channels) VALUES (?, ?, ?)",
            (project_id, goal, json.dumps(channels)),
        )
        await db.commit()
        run_id = cursor.lastrowid
        return {"id": run_id, "project_id": project_id, "goal": goal,
                "channels": channels, "status": "drafting"}
    finally:
        await db.close()


async def add_campaign_artifact(
    run_id: int, artifact_type: str, content: str,
    channel: str | None = None, title: str = "",
) -> int:
    """Add an artifact (research_brief, angle_matrix, channel_draft, review) to a campaign."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO campaign_artifacts (run_id, artifact_type, channel, title, content) "
            "VALUES (?, ?, ?, ?, ?)",
            (run_id, artifact_type, channel, title, content),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def update_campaign_status(run_id: int, status: str) -> None:
    """Update campaign run status."""
    db = await get_db()
    try:
        completed = "datetime('now')" if status in ("completed", "cancelled") else "NULL"
        await db.execute(
            f"UPDATE campaign_runs SET status = ?, completed_at = {completed} WHERE id = ?",
            (status, run_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_campaign_run(run_id: int) -> dict | None:
    """Get a campaign run with its artifacts."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, project_id, goal, channels, status, created_at, completed_at "
            "FROM campaign_runs WHERE id = ?", (run_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        run = {
            "id": row[0], "project_id": row[1], "goal": row[2],
            "channels": json.loads(row[3]), "status": row[4],
            "created_at": row[5], "completed_at": row[6],
        }
        cursor = await db.execute(
            "SELECT id, artifact_type, channel, title, content, created_at "
            "FROM campaign_artifacts WHERE run_id = ? ORDER BY id",
            (run_id,),
        )
        rows = await cursor.fetchall()
        run["artifacts"] = [
            {"id": r[0], "artifact_type": r[1], "channel": r[2],
             "title": r[3], "content": r[4], "created_at": r[5]}
            for r in rows
        ]
        return run
    finally:
        await db.close()


async def list_campaign_runs(project_id: int, limit: int = 20) -> list[dict]:
    """List recent campaign runs for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT cr.id, cr.goal, cr.channels, cr.status, cr.created_at, cr.completed_at, "
            "(SELECT COUNT(*) FROM campaign_artifacts ca WHERE ca.run_id = cr.id) as artifact_count "
            "FROM campaign_runs cr WHERE cr.project_id = ? ORDER BY cr.id DESC LIMIT ?",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "goal": r[1], "channels": json.loads(r[2]),
             "status": r[3], "created_at": r[4], "completed_at": r[5],
             "artifact_count": r[6]}
            for r in rows
        ]
    finally:
        await db.close()
