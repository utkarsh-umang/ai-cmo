"""SEO, GEO, and Community scan storage + history queries."""

from __future__ import annotations

from opencmo.storage._db import get_db


def _normalized_seo_score(score_performance: float | None, seo_health_score: float | None) -> float | None:
    """Return the UI-facing SEO score in [0, 1]."""
    if score_performance is not None:
        return score_performance
    if seo_health_score is not None:
        return seo_health_score / 100
    return None


async def save_seo_scan(
    project_id: int,
    url: str,
    report_json: str,
    *,
    score_performance: float | None = None,
    score_lcp: float | None = None,
    score_cls: float | None = None,
    score_tbt: float | None = None,
    has_robots_txt: bool | None = None,
    has_sitemap: bool | None = None,
    has_schema_org: bool | None = None,
    seo_health_score: float | None = None,
) -> int:
    """Save an SEO scan snapshot. Returns scan id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO seo_scans
               (project_id, url, report_json,
                score_performance, score_lcp, score_cls, score_tbt,
                has_robots_txt, has_sitemap, has_schema_org, seo_health_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id, url, report_json,
                score_performance, score_lcp, score_cls, score_tbt,
                int(has_robots_txt) if has_robots_txt is not None else None,
                int(has_sitemap) if has_sitemap is not None else None,
                int(has_schema_org) if has_schema_org is not None else None,
                seo_health_score,
            ),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def save_geo_scan(
    project_id: int,
    geo_score: int | None,
    *,
    visibility_score: int | None = None,
    position_score: int | None = None,
    sentiment_score: int | None = None,
    crawl_success_rate: float | None = None,
    platform_results_json: str = "{}",
) -> int:
    """Save a GEO scan snapshot. Returns scan id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO geo_scans
               (project_id, geo_score, visibility_score, position_score,
                sentiment_score, crawl_success_rate, platform_results_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            # Coerce None → 0: existing databases have geo_score NOT NULL from
            # before migration v9, and SQLite cannot ALTER COLUMN to drop it.
            (project_id, geo_score if geo_score is not None else 0,
             visibility_score, position_score,
             sentiment_score, crawl_success_rate, platform_results_json),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def save_community_scan(
    project_id: int,
    total_hits: int,
    results_json: str,
) -> int:
    """Save a community scan snapshot. Returns scan id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO community_scans (project_id, total_hits, results_json) VALUES (?, ?, ?)",
            (project_id, total_hits, results_json),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_seo_history(project_id: int, limit: int = 20) -> list[dict]:
    """Return recent SEO scans for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, url, scanned_at, score_performance, score_lcp, score_cls,
                      score_tbt, has_robots_txt, has_sitemap, has_schema_org,
                      seo_health_score
               FROM seo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "url": r[1], "scanned_at": r[2],
                "score_performance": r[3], "score_lcp": r[4], "score_cls": r[5],
                "score_tbt": r[6], "has_robots_txt": bool(r[7]) if r[7] is not None else None,
                "has_sitemap": bool(r[8]) if r[8] is not None else None,
                "has_schema_org": bool(r[9]) if r[9] is not None else None,
                "seo_health_score": r[10],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_geo_history(project_id: int, limit: int = 20) -> list[dict]:
    """Return recent GEO scans for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, scanned_at, geo_score, visibility_score, position_score,
                      sentiment_score, crawl_success_rate, platform_results_json
               FROM geo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "scanned_at": r[1], "geo_score": r[2],
                "visibility_score": r[3], "position_score": r[4],
                "sentiment_score": r[5], "crawl_success_rate": r[6],
                "platform_results_json": r[7],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_community_history(project_id: int, limit: int = 20) -> list[dict]:
    """Return recent community scans for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, scanned_at, total_hits, results_json
               FROM community_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "scanned_at": r[1], "total_hits": r[2], "results_json": r[3]}
            for r in rows
        ]
    finally:
        await db.close()


async def get_latest_scans(project_id: int) -> dict:
    """Get the latest scan of each type for a project, including SERP summary."""
    db = await get_db()
    try:
        seo = await db.execute(
            """SELECT scanned_at, score_performance, seo_health_score
               FROM seo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1""",
            (project_id,),
        )
        seo_row = await seo.fetchone()

        geo = await db.execute(
            "SELECT scanned_at, geo_score FROM geo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1",
            (project_id,),
        )
        geo_row = await geo.fetchone()

        comm = await db.execute(
            "SELECT scanned_at, total_hits FROM community_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1",
            (project_id,),
        )
        comm_row = await comm.fetchone()

        # SERP: latest snapshot per keyword (error IS NULL only)
        serp_cur = await db.execute(
            """SELECT keyword, position, checked_at FROM serp_snapshots
               WHERE project_id = ? AND error IS NULL
               AND id IN (
                   SELECT MAX(id) FROM serp_snapshots
                   WHERE project_id = ? AND error IS NULL
                   GROUP BY keyword
               )
               ORDER BY keyword""",
            (project_id, project_id),
        )
        serp_rows = await serp_cur.fetchall()
        serp_summary = [
            {"keyword": r[0], "position": r[1], "checked_at": r[2]}
            for r in serp_rows
        ] if serp_rows else []

        return {
            "seo": {
                "scanned_at": seo_row[0],
                "score": _normalized_seo_score(seo_row[1], seo_row[2]),
                "performance_score": seo_row[1],
                "health_score": seo_row[2],
            } if seo_row else None,
            "geo": {"scanned_at": geo_row[0], "score": geo_row[1]} if geo_row else None,
            "community": {"scanned_at": comm_row[0], "total_hits": comm_row[1]} if comm_row else None,
            "serp": serp_summary,
        }
    finally:
        await db.close()


async def get_previous_scans(project_id: int) -> dict | None:
    """Get the second-most-recent scan of each type (for delta calculation)."""
    db = await get_db()
    try:
        seo = await db.execute(
            """SELECT scanned_at, score_performance, seo_health_score
               FROM seo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1 OFFSET 1""",
            (project_id,),
        )
        seo_row = await seo.fetchone()

        geo = await db.execute(
            "SELECT scanned_at, geo_score FROM geo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1 OFFSET 1",
            (project_id,),
        )
        geo_row = await geo.fetchone()

        if not seo_row and not geo_row:
            return None

        result = {}
        if seo_row:
            result["seo"] = {
                "scanned_at": seo_row[0],
                "score": _normalized_seo_score(seo_row[1], seo_row[2]),
                "performance_score": seo_row[1],
                "health_score": seo_row[2],
            }
        if geo_row:
            result["geo"] = {"scanned_at": geo_row[0], "score": geo_row[1]}
        return result
    finally:
        await db.close()
