"""Trend analysis tools — query historical scan data from storage."""

from __future__ import annotations

from agents import function_tool

from opencmo import storage


async def _get_seo_trends_impl(brand_name: str, url: str) -> str:
    """Core logic for SEO trends — testable without function_tool wrapper."""
    try:
        project_id = await storage.ensure_project(brand_name, url, "")
        history = await storage.get_seo_history(project_id, limit=20)
    except Exception as e:
        return f"Failed to fetch SEO trends: {e}"

    if not history:
        return f"No SEO scan history found for {brand_name} ({url}). Run an SEO audit first."

    lines = [
        f"# SEO Trends: {brand_name}",
        f"**URL**: {url}\n",
        "| Date | Perf Score | LCP (ms) | CLS | TBT (ms) | robots.txt | sitemap | Schema.org |",
        "|------|-----------|----------|-----|----------|------------|---------|------------|",
    ]

    for scan in reversed(history):  # oldest first
        perf = f"{scan['score_performance']:.0%}" if scan["score_performance"] is not None else "—"
        lcp = f"{scan['score_lcp']:.0f}" if scan["score_lcp"] is not None else "—"
        cls_val = f"{scan['score_cls']:.3f}" if scan["score_cls"] is not None else "—"
        tbt = f"{scan['score_tbt']:.0f}" if scan["score_tbt"] is not None else "—"

        def _yn(val):
            return "Yes" if val else ("No" if val is not None else "—")

        lines.append(
            f"| {scan['scanned_at'][:16]} | {perf} | {lcp} | {cls_val} | {tbt} "
            f"| {_yn(scan['has_robots_txt'])} | {_yn(scan['has_sitemap'])} | {_yn(scan['has_schema_org'])} |"
        )

    lines.append(f"\n*{len(history)} scans shown (most recent first in DB, displayed oldest first)*")
    return "\n".join(lines)


async def _get_geo_trends_impl(brand_name: str, category: str) -> str:
    """Core logic for GEO trends — testable without function_tool wrapper."""
    try:
        projects = await storage.list_projects()
        project = next((p for p in projects if p["brand_name"] == brand_name), None)
        if not project:
            return f"No project found for brand '{brand_name}'. Run a GEO scan first."
        history = await storage.get_geo_history(project["id"], limit=20)
    except Exception as e:
        return f"Failed to fetch GEO trends: {e}"

    if not history:
        return f"No GEO scan history found for {brand_name}. Run a GEO scan first."

    lines = [
        f"# GEO Trends: {brand_name}",
        f"**Category**: {category}\n",
        "| Date | GEO Score | Visibility | Position | Sentiment |",
        "|------|-----------|------------|----------|-----------|",
    ]

    for scan in reversed(history):
        vis = scan["visibility_score"] if scan["visibility_score"] is not None else "—"
        pos = scan["position_score"] if scan["position_score"] is not None else "—"
        sent = scan["sentiment_score"] if scan["sentiment_score"] is not None else "—"
        lines.append(
            f"| {scan['scanned_at'][:16]} | {scan['geo_score']} | {vis} | {pos} | {sent} |"
        )

    lines.append(f"\n*{len(history)} scans shown*")
    return "\n".join(lines)


@function_tool
async def get_seo_trends(brand_name: str, url: str) -> str:
    """Get SEO metric trends over time for a project.

    Returns a markdown table of historical SEO scans including performance score,
    Core Web Vitals (LCP/CLS/TBT), and crawlability flags.

    Args:
        brand_name: The brand or product name.
        url: The URL that was audited.
    """
    return await _get_seo_trends_impl(brand_name, url)


@function_tool
async def get_geo_trends(brand_name: str, category: str) -> str:
    """Get GEO score trends over time for a project.

    Returns a markdown table of historical GEO scans including score breakdown
    and per-platform results.

    Args:
        brand_name: The brand or product name.
        category: The product category.
    """
    return await _get_geo_trends_impl(brand_name, category)
