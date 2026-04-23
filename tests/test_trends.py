"""Tests for trend analysis tools."""

from unittest.mock import patch

import pytest

from opencmo import storage
from opencmo.tools.trends import _get_geo_trends_impl, _get_seo_trends_impl


@pytest.mark.asyncio
async def test_seo_trends_no_data(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        result = await _get_seo_trends_impl("TestBrand", "https://test.com")
        assert "No SEO scan history" in result


@pytest.mark.asyncio
async def test_seo_trends_with_data(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        pid = await storage.ensure_project("TestBrand", "https://test.com", "testing")
        await storage.save_seo_scan(pid, "https://test.com", "{}", score_performance=0.85, score_lcp=2000)
        await storage.save_seo_scan(pid, "https://test.com", "{}", score_performance=0.9, score_lcp=1800)

        result = await _get_seo_trends_impl("TestBrand", "https://test.com")
        assert "SEO Trends" in result
        assert "2 scans" in result


@pytest.mark.asyncio
async def test_geo_trends_no_data(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        result = await _get_geo_trends_impl("TestBrand", "testing")
        assert "No project found" in result


@pytest.mark.asyncio
async def test_geo_trends_with_data(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        pid = await storage.ensure_project("TestBrand", "https://test.com", "testing")
        await storage.save_geo_scan(pid, 45, visibility_score=20, position_score=10, sentiment_score=15)
        await storage.save_geo_scan(pid, 60, visibility_score=30, position_score=15, sentiment_score=15)

        result = await _get_geo_trends_impl("TestBrand", "testing")
        assert "GEO Trends" in result
        assert "2 scans" in result
