"""GitHub leads storage — discovery runs and lead management."""

from __future__ import annotations

import json

from opencmo.storage._db import get_db


def _lead_row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "project_id": row[1],
        "login": row[2],
        "github_id": row[3],
        "name": row[4],
        "bio": row[5],
        "company": row[6],
        "location": row[7],
        "email": row[8],
        "blog": row[9],
        "twitter_username": row[10],
        "hireable": bool(row[11]) if row[11] is not None else None,
        "followers": row[12],
        "following": row[13],
        "public_repos": row[14],
        "created_at_gh": row[15],
        "top_languages": json.loads(row[16] or "[]"),
        "total_stars": row[17],
        "top_repos": json.loads(row[18] or "[]"),
        "source": row[19],
        "seed_username": row[20],
        "outreach_score": row[21],
        "outreach_status": row[22],
        "outreach_channel": row[23],
        "outreach_note": row[24],
        "enriched": bool(row[25]),
        "created_at": row[26],
        "updated_at": row[27],
    }


_LEAD_COLUMNS = (
    "id, project_id, login, github_id, name, bio, company, location, email, blog,"
    " twitter_username, hireable, followers, following, public_repos, created_at_gh,"
    " top_languages, total_stars, top_repos_json, source, seed_username,"
    " outreach_score, outreach_status, outreach_channel, outreach_note,"
    " enriched, created_at, updated_at"
)


# ---------------------------------------------------------------------------
# Lead CRUD
# ---------------------------------------------------------------------------


async def upsert_github_lead(project_id: int, lead_data: dict) -> dict:
    """Insert or update a GitHub lead by (project_id, login)."""
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO github_leads (
                   project_id, login, github_id, name, bio, company, location,
                   email, blog, twitter_username, hireable, followers, following,
                   public_repos, created_at_gh, top_languages, total_stars,
                   top_repos_json, source, seed_username, outreach_score, enriched,
                   updated_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(project_id, login) DO UPDATE SET
                   github_id = COALESCE(excluded.github_id, github_id),
                   name = CASE WHEN excluded.name != '' THEN excluded.name ELSE name END,
                   bio = CASE WHEN excluded.bio != '' THEN excluded.bio ELSE bio END,
                   company = CASE WHEN excluded.company != '' THEN excluded.company ELSE company END,
                   location = CASE WHEN excluded.location != '' THEN excluded.location ELSE location END,
                   email = CASE WHEN excluded.email != '' THEN excluded.email ELSE email END,
                   blog = CASE WHEN excluded.blog != '' THEN excluded.blog ELSE blog END,
                   twitter_username = CASE WHEN excluded.twitter_username != '' THEN excluded.twitter_username ELSE twitter_username END,
                   hireable = COALESCE(excluded.hireable, hireable),
                   followers = excluded.followers,
                   following = excluded.following,
                   public_repos = excluded.public_repos,
                   created_at_gh = CASE WHEN excluded.created_at_gh != '' THEN excluded.created_at_gh ELSE created_at_gh END,
                   top_languages = CASE WHEN excluded.top_languages != '[]' THEN excluded.top_languages ELSE top_languages END,
                   total_stars = excluded.total_stars,
                   top_repos_json = CASE WHEN excluded.top_repos_json != '[]' THEN excluded.top_repos_json ELSE top_repos_json END,
                   enriched = MAX(enriched, excluded.enriched),
                   updated_at = datetime('now')
            """,
            (
                project_id,
                lead_data.get("login", ""),
                lead_data.get("github_id") or lead_data.get("id"),
                lead_data.get("name", ""),
                lead_data.get("bio", ""),
                lead_data.get("company", ""),
                lead_data.get("location", ""),
                lead_data.get("email", ""),
                lead_data.get("blog", ""),
                lead_data.get("twitter_username", ""),
                lead_data.get("hireable"),
                lead_data.get("followers", 0),
                lead_data.get("following", 0),
                lead_data.get("public_repos", 0),
                lead_data.get("created_at_gh") or lead_data.get("created_at", ""),
                json.dumps(lead_data.get("top_languages", []), ensure_ascii=False),
                lead_data.get("total_stars", 0),
                json.dumps(lead_data.get("top_repos", []), ensure_ascii=False),
                lead_data.get("source", ""),
                lead_data.get("seed_username", ""),
                lead_data.get("outreach_score", 0),
                1 if lead_data.get("enriched") else 0,
            ),
        )
        await db.commit()
    finally:
        await db.close()

    return await get_github_lead(project_id, lead_data["login"]) or {}


async def batch_upsert_github_leads(project_id: int, leads: list[dict]) -> int:
    """Bulk insert/update leads. Returns count of rows affected."""
    count = 0
    db = await get_db()
    try:
        for lead in leads:
            await db.execute(
                """INSERT INTO github_leads (
                       project_id, login, github_id, source, seed_username
                   ) VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(project_id, login) DO UPDATE SET
                       github_id = COALESCE(excluded.github_id, github_id),
                       updated_at = datetime('now')
                """,
                (
                    project_id,
                    lead.get("login", ""),
                    lead.get("github_id") or lead.get("id"),
                    lead.get("source", ""),
                    lead.get("seed_username", ""),
                ),
            )
            count += 1
        await db.commit()
    finally:
        await db.close()
    return count


async def get_github_lead(project_id: int, login: str) -> dict | None:
    """Return a single GitHub lead."""
    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT {_LEAD_COLUMNS} FROM github_leads WHERE project_id = ? AND login = ?",
            (project_id, login),
        )
        row = await cursor.fetchone()
        return _lead_row_to_dict(row) if row else None
    finally:
        await db.close()


async def list_github_leads(
    project_id: int,
    *,
    status: str | None = None,
    min_score: float | None = None,
    has_email: bool | None = None,
    has_twitter: bool | None = None,
    language: str | None = None,
    location: str | None = None,
    enriched: bool | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    """List GitHub leads with optional filters, highest score first."""
    conditions = ["project_id = ?"]
    params: list = [project_id]

    if status:
        conditions.append("outreach_status = ?")
        params.append(status)
    if min_score is not None:
        conditions.append("outreach_score >= ?")
        params.append(min_score)
    if has_email:
        conditions.append("email != ''")
    if has_twitter:
        conditions.append("twitter_username != ''")
    if language:
        conditions.append("top_languages LIKE ?")
        params.append(f"%{language}%")
    if location:
        conditions.append("location LIKE ?")
        params.append(f"%{location}%")
    if enriched is not None:
        conditions.append("enriched = ?")
        params.append(1 if enriched else 0)

    where = " AND ".join(conditions)
    params.extend([limit, offset])

    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT {_LEAD_COLUMNS} FROM github_leads WHERE {where}"
            " ORDER BY outreach_score DESC, created_at DESC LIMIT ? OFFSET ?",
            params,
        )
        rows = await cursor.fetchall()
        return [_lead_row_to_dict(r) for r in rows]
    finally:
        await db.close()


async def count_github_leads(
    project_id: int,
    *,
    status: str | None = None,
    has_email: bool | None = None,
    has_twitter: bool | None = None,
    enriched: bool | None = None,
) -> int:
    """Count leads matching filters."""
    conditions = ["project_id = ?"]
    params: list = [project_id]
    if status:
        conditions.append("outreach_status = ?")
        params.append(status)
    if has_email:
        conditions.append("email != ''")
    if has_twitter:
        conditions.append("twitter_username != ''")
    if enriched is not None:
        conditions.append("enriched = ?")
        params.append(1 if enriched else 0)

    where = " AND ".join(conditions)
    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT COUNT(*) FROM github_leads WHERE {where}", params,
        )
        row = await cursor.fetchone()
        return row[0] if row else 0
    finally:
        await db.close()


async def update_lead_outreach(
    project_id: int,
    login: str,
    status: str,
    channel: str = "",
    note: str = "",
) -> bool:
    """Update a lead's outreach status."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """UPDATE github_leads
               SET outreach_status = ?, outreach_channel = ?, outreach_note = ?,
                   updated_at = datetime('now')
               WHERE project_id = ? AND login = ?""",
            (status, channel, note, project_id, login),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def update_lead_score(project_id: int, login: str, score: float) -> bool:
    """Update a lead's outreach score."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "UPDATE github_leads SET outreach_score = ?, updated_at = datetime('now') WHERE project_id = ? AND login = ?",
            (score, project_id, login),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def batch_update_enrichment(project_id: int, enriched_leads: list[dict]) -> int:
    """Mark leads as enriched and populate profile fields."""
    count = 0
    db = await get_db()
    try:
        for lead in enriched_leads:
            login = lead.get("login", "")
            if not login:
                continue
            await db.execute(
                """UPDATE github_leads SET
                       name = ?, bio = ?, company = ?, location = ?,
                       email = ?, blog = ?, twitter_username = ?, hireable = ?,
                       followers = ?, following = ?, public_repos = ?,
                       created_at_gh = ?, top_languages = ?, total_stars = ?,
                       top_repos_json = ?, enriched = 1, updated_at = datetime('now')
                   WHERE project_id = ? AND login = ?""",
                (
                    lead.get("name", ""),
                    lead.get("bio", ""),
                    lead.get("company", ""),
                    lead.get("location", ""),
                    lead.get("email", ""),
                    lead.get("blog", ""),
                    lead.get("twitter_username", ""),
                    lead.get("hireable"),
                    lead.get("followers", 0),
                    lead.get("following", 0),
                    lead.get("public_repos", 0),
                    lead.get("created_at_gh") or lead.get("created_at", ""),
                    json.dumps(lead.get("top_languages", []), ensure_ascii=False),
                    lead.get("total_stars", 0),
                    json.dumps(lead.get("top_repos", []), ensure_ascii=False),
                    project_id,
                    login,
                ),
            )
            count += 1
        await db.commit()
    finally:
        await db.close()
    return count


async def get_unenriched_leads(project_id: int, limit: int = 50) -> list[dict]:
    """Fetch leads that haven't been enriched yet."""
    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT {_LEAD_COLUMNS} FROM github_leads WHERE project_id = ? AND enriched = 0 LIMIT ?",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [_lead_row_to_dict(r) for r in rows]
    finally:
        await db.close()


async def delete_github_leads(project_id: int) -> int:
    """Delete all leads for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM github_leads WHERE project_id = ?", (project_id,),
        )
        await db.commit()
        return cursor.rowcount
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Discovery runs
# ---------------------------------------------------------------------------


def _run_row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "project_id": row[1],
        "task_id": row[2],
        "seed_username": row[3],
        "source": row[4],
        "max_hops": row[5],
        "total_discovered": row[6],
        "total_enriched": row[7],
        "status": row[8],
        "error": row[9],
        "created_at": row[10],
        "completed_at": row[11],
    }


_RUN_COLUMNS = (
    "id, project_id, task_id, seed_username, source, max_hops,"
    " total_discovered, total_enriched, status, error, created_at, completed_at"
)


async def create_discovery_run(
    project_id: int,
    task_id: str,
    seed_username: str,
    source: str = "both",
    max_hops: int = 1,
) -> dict:
    """Create a new discovery run record."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO github_discovery_runs
                   (project_id, task_id, seed_username, source, max_hops)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, task_id, seed_username, source, max_hops),
        )
        await db.commit()
        run_id = cursor.lastrowid
    finally:
        await db.close()

    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT {_RUN_COLUMNS} FROM github_discovery_runs WHERE id = ?",
            (run_id,),
        )
        row = await cursor.fetchone()
        return _run_row_to_dict(row) if row else {}
    finally:
        await db.close()


async def update_discovery_run(run_id: int, **fields) -> bool:
    """Update fields on a discovery run."""
    if not fields:
        return False
    allowed = {
        "total_discovered", "total_enriched", "status", "error", "completed_at",
    }
    updates = []
    params: list = []
    for key, val in fields.items():
        if key in allowed:
            updates.append(f"{key} = ?")
            params.append(val)
    if not updates:
        return False
    params.append(run_id)
    db = await get_db()
    try:
        cursor = await db.execute(
            f"UPDATE github_discovery_runs SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def list_discovery_runs(project_id: int, limit: int = 20) -> list[dict]:
    """List discovery runs for a project, newest first."""
    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT {_RUN_COLUMNS} FROM github_discovery_runs WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [_run_row_to_dict(r) for r in rows]
    finally:
        await db.close()


async def get_github_lead_stats(project_id: int) -> dict:
    """Return aggregated stats for the GitHub leads of a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT
                   COUNT(*) AS total,
                   SUM(CASE WHEN enriched = 1 THEN 1 ELSE 0 END) AS enriched_count,
                   SUM(CASE WHEN email != '' THEN 1 ELSE 0 END) AS has_email,
                   SUM(CASE WHEN twitter_username != '' THEN 1 ELSE 0 END) AS has_twitter,
                   ROUND(AVG(CASE WHEN enriched = 1 THEN outreach_score END), 1) AS avg_score
               FROM github_leads WHERE project_id = ?""",
            (project_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return {"total": 0, "enriched": 0, "has_email": 0, "has_twitter": 0, "avg_score": 0}
        return {
            "total": row[0] or 0,
            "enriched": row[1] or 0,
            "has_email": row[2] or 0,
            "has_twitter": row[3] or 0,
            "avg_score": row[4] or 0,
        }
    finally:
        await db.close()
