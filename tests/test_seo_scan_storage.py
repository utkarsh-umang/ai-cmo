from unittest.mock import patch

import pytest

from opencmo import storage


@pytest.mark.asyncio
async def test_latest_seo_score_falls_back_to_health_score(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        project_id = await storage.ensure_project("SEO Health", "https://seo-health.test", "testing")
        await storage.save_seo_scan(
            project_id,
            "https://seo-health.test",
            "{}",
            seo_health_score=73.0,
            has_robots_txt=True,
            has_sitemap=True,
            has_schema_org=True,
        )

        latest = await storage.get_latest_scans(project_id)
        history = await storage.get_seo_history(project_id)

    assert latest["seo"]["score"] == 0.73
    assert latest["seo"]["performance_score"] is None
    assert latest["seo"]["health_score"] == 73.0
    assert history[0]["seo_health_score"] == 73.0
