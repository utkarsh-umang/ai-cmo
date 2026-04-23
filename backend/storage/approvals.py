"""Approval queue storage."""

from __future__ import annotations

import json

from opencmo.storage._db import get_db


def _approval_row_to_dict(row) -> dict:
    d = {
        "id": row[0],
        "project_id": row[1],
        "channel": row[2],
        "approval_type": row[3],
        "status": row[4],
        "title": row[5],
        "target_label": row[6],
        "target_url": row[7],
        "agent_name": row[8],
        "content": row[9],
        "payload": json.loads(row[10] or "{}"),
        "preview": json.loads(row[11] or "{}"),
        "publish_result": json.loads(row[12]) if row[12] else None,
        "decision_note": row[13],
        "created_at": row[14],
        "decided_at": row[15],
    }
    # Autopilot fields (may not exist in older rows)
    if len(row) > 16:
        d["source_insight_id"] = row[16]
        d["pre_metrics_json"] = row[17] or "{}"
        d["post_metrics_json"] = row[18] or "{}"
    return d


async def create_approval(
    project_id: int,
    channel: str,
    approval_type: str,
    content: str,
    payload: dict,
    preview: dict,
    *,
    title: str = "",
    target_label: str = "",
    target_url: str = "",
    agent_name: str = "",
) -> dict:
    """Insert a pending approval and return the stored record."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO approvals (
                   project_id, channel, approval_type, title, target_label, target_url,
                   agent_name, content, payload_json, preview_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                channel,
                approval_type,
                title,
                target_label,
                target_url,
                agent_name,
                content,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(preview, ensure_ascii=False),
            ),
        )
        await db.commit()
        approval_id = cursor.lastrowid
    finally:
        await db.close()

    return await get_approval(approval_id)


async def get_approval(approval_id: int) -> dict | None:
    """Return one approval item."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, project_id, channel, approval_type, status, title, target_label,
                      target_url, agent_name, content, payload_json, preview_json,
                      publish_result_json, decision_note, created_at, decided_at,
                      source_insight_id, pre_metrics_json, post_metrics_json
               FROM approvals WHERE id = ?""",
            (approval_id,),
        )
        row = await cursor.fetchone()
        return _approval_row_to_dict(row) if row else None
    finally:
        await db.close()


async def list_approvals(status: str | None = None, limit: int = 50) -> list[dict]:
    """List approvals, newest first."""
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                """SELECT id, project_id, channel, approval_type, status, title, target_label,
                          target_url, agent_name, content, payload_json, preview_json,
                          publish_result_json, decision_note, created_at, decided_at
                   FROM approvals
                   WHERE status = ?
                   ORDER BY created_at DESC, id DESC
                   LIMIT ?""",
                (status, limit),
            )
        else:
            cursor = await db.execute(
                """SELECT id, project_id, channel, approval_type, status, title, target_label,
                          target_url, agent_name, content, payload_json, preview_json,
                          publish_result_json, decision_note, created_at, decided_at
                   FROM approvals
                   ORDER BY created_at DESC, id DESC
                   LIMIT ?""",
                (limit,),
            )
        rows = await cursor.fetchall()
        return [_approval_row_to_dict(row) for row in rows]
    finally:
        await db.close()


async def update_approval_status(
    approval_id: int,
    status: str,
    *,
    decision_note: str = "",
    publish_result: dict | None = None,
) -> bool:
    """Update approval decision state and optional publish result."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """UPDATE approvals
               SET status = ?, decision_note = ?, publish_result_json = ?, decided_at = datetime('now')
               WHERE id = ?""",
            (
                status,
                decision_note,
                json.dumps(publish_result, ensure_ascii=False) if publish_result is not None else None,
                approval_id,
            ),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def create_approval_with_source(
    project_id: int,
    channel: str,
    approval_type: str,
    content: str,
    payload: dict,
    preview: dict,
    *,
    title: str = "",
    target_label: str = "",
    target_url: str = "",
    agent_name: str = "",
    source_insight_id: int | None = None,
    pre_metrics_json: str = "{}",
) -> dict:
    """Insert a pending approval with source tracking and return the stored record."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO approvals (
                   project_id, channel, approval_type, title, target_label, target_url,
                   agent_name, content, payload_json, preview_json,
                   source_insight_id, pre_metrics_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id, channel, approval_type, title, target_label, target_url,
                agent_name, content,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(preview, ensure_ascii=False),
                source_insight_id, pre_metrics_json,
            ),
        )
        await db.commit()
        approval_id = cursor.lastrowid
    finally:
        await db.close()
    return await get_approval(approval_id)
