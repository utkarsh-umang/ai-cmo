"""Tests for Tavily-first shared content fetching."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_fetch_url_content_prefers_tavily_extract():
    """Shared content fetch should use Tavily extraction before crawl fallback."""
    from opencmo.tools import crawl as crawl_module

    if not hasattr(crawl_module, "fetch_url_content"):
        pytest.fail("fetch_url_content helper is missing")

    mock_extract = AsyncMock(return_value="# Tavily content")
    mock_crawler = AsyncMock()
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)
    mock_crawler.arun = AsyncMock(side_effect=AssertionError("crawl fallback should not run"))

    with patch("opencmo.tools.tavily_helper.tavily_extract", mock_extract, create=True), \
         patch("opencmo.tools.crawl.AsyncWebCrawler", return_value=mock_crawler):
        content, source = await crawl_module.fetch_url_content("https://example.com")

    assert content == "# Tavily content"
    assert source == "tavily"
    mock_extract.assert_awaited_once_with(
        "https://example.com",
        extract_depth="advanced",
        format="markdown",
    )
    mock_crawler.arun.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_url_content_falls_back_to_crawl():
    """Shared content fetch should preserve crawl fallback when Tavily returns no content."""
    from opencmo.tools import crawl as crawl_module

    if not hasattr(crawl_module, "fetch_url_content"):
        pytest.fail("fetch_url_content helper is missing")

    mock_extract = AsyncMock(return_value=None)
    mock_result = MagicMock()
    mock_result.markdown = "# Crawl content"
    mock_crawler = AsyncMock()
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)
    mock_crawler.arun = AsyncMock(return_value=mock_result)

    with patch("opencmo.tools.tavily_helper.tavily_extract", mock_extract, create=True), \
         patch("opencmo.tools.crawl.AsyncWebCrawler", return_value=mock_crawler):
        content, source = await crawl_module.fetch_url_content("https://example.com")

    assert content == "# Crawl content"
    assert source == "crawl4ai"
    mock_extract.assert_awaited_once()
    mock_crawler.arun.assert_awaited_once_with(url="https://example.com")


@pytest.mark.asyncio
async def test_fetch_url_content_falls_back_to_html_metadata_when_markdown_is_empty():
    """Shared content fetch should recover page metadata for JS-heavy pages."""
    from opencmo.tools import crawl as crawl_module

    mock_extract = AsyncMock(return_value=None)
    mock_result = MagicMock()
    mock_result.markdown = ""
    mock_result.html = """
        <html>
          <head>
            <title>Coze</title>
            <meta name="description" content="AI agent workspace for teams" />
            <meta property="og:description" content="Build agents quickly" />
          </head>
        </html>
    """
    mock_crawler = AsyncMock()
    mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
    mock_crawler.__aexit__ = AsyncMock(return_value=False)
    mock_crawler.arun = AsyncMock(return_value=mock_result)

    with patch("opencmo.tools.tavily_helper.tavily_extract", mock_extract, create=True), \
         patch("opencmo.tools.crawl.AsyncWebCrawler", return_value=mock_crawler):
        content, source = await crawl_module.fetch_url_content("https://example.com")

    assert source == "html_meta"
    assert "Page title: Coze" in content
    assert "Meta description: AI agent workspace for teams" in content
    assert "Open Graph description: Build agents quickly" in content
