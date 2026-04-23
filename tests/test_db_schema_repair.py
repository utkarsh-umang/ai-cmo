from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest

from opencmo import storage


@pytest.mark.asyncio
async def test_ensure_db_repairs_missing_scan_columns_when_schema_version_is_already_current(tmp_path):
    db_path = tmp_path / "broken.db"

    with sqlite3.connect(db_path) as db:
        db.executescript(
            """
            CREATE TABLE schema_version (
                version INTEGER NOT NULL
            );

            INSERT INTO schema_version (version) VALUES (9);
            INSERT INTO schema_version (version) VALUES (10);

            CREATE TABLE seo_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
                report_json TEXT NOT NULL,
                score_performance REAL,
                score_lcp REAL,
                score_cls REAL,
                score_tbt REAL,
                has_robots_txt INTEGER,
                has_sitemap INTEGER,
                has_schema_org INTEGER
            );

            CREATE TABLE geo_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
                geo_score INTEGER,
                visibility_score INTEGER,
                position_score INTEGER,
                sentiment_score INTEGER,
                platform_results_json TEXT NOT NULL
            );
            """
        )

    with patch.object(storage, "_DB_PATH", db_path), patch.object(storage, "_SCHEMA_READY_FOR", None):
        await storage.ensure_db()

    with sqlite3.connect(db_path) as db:
        seo_columns = {row[1] for row in db.execute("PRAGMA table_info(seo_scans)")}
        geo_columns = {row[1] for row in db.execute("PRAGMA table_info(geo_scans)")}

    assert "seo_health_score" in seo_columns
    assert "crawl_success_rate" in geo_columns
