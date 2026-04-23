"""Opportunity and topic-cluster summaries built from existing monitoring data."""

from __future__ import annotations

import asyncio
import re
from collections import Counter

from opencmo import storage

_GENERIC_TOKENS = {
    "a", "an", "and", "app", "apps", "best", "compare", "comparison", "for",
    "free", "guide", "how", "in", "of", "on", "open", "or", "platform",
    "review", "reviews", "software", "source", "the", "to", "tool", "tools",
    "vs", "with",
}

_OPPORTUNITY_TYPES = (
    "quick_win",
    "competitor_gap",
    "community_activation",
    "topic_cluster_gap",
)


def _keyword_tokens(keyword: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", keyword.lower())


def _cluster_name(keyword: str) -> str:
    tokens = [token for token in _keyword_tokens(keyword) if token not in _GENERIC_TOKENS]
    if not tokens:
        tokens = _keyword_tokens(keyword)
    if not tokens:
        return keyword.strip().lower()
    if len(tokens) >= 3 and tokens[0] in {"ai", "llm"}:
        return " ".join(tokens[:3])
    if len(tokens) >= 2:
        return " ".join(tokens[:2])
    return tokens[0]


def _priority_from_score(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def _metric_ref(domain: str, source: str, key: str, value: str, url: str | None = None) -> dict:
    return {
        "domain": domain,
        "source": source,
        "key": key,
        "value": value,
        "url": url,
    }


def _build_cluster_summary(
    tracked_keywords: list[dict],
    serp_latest: list[dict],
    competitor_keywords: list[dict],
) -> dict:
    brand_keywords = [item["keyword"] for item in tracked_keywords]
    brand_set = {keyword.lower() for keyword in brand_keywords}
    serp_positions = {
        item["keyword"].lower(): item.get("position")
        for item in serp_latest
    }

    clusters: dict[str, dict] = {}

    for keyword in brand_keywords:
        name = _cluster_name(keyword)
        cluster = clusters.setdefault(
            name,
            {
                "name": name,
                "brand_keywords": [],
                "competitor_keywords": [],
                "gap_keywords": [],
                "quick_win_keywords": [],
            },
        )
        cluster["brand_keywords"].append(keyword)
        position = serp_positions.get(keyword.lower())
        if position is not None and 11 <= position <= 20:
            cluster["quick_win_keywords"].append(keyword)

    for item in competitor_keywords:
        keyword = item["keyword"]
        name = _cluster_name(keyword)
        cluster = clusters.setdefault(
            name,
            {
                "name": name,
                "brand_keywords": [],
                "competitor_keywords": [],
                "gap_keywords": [],
                "quick_win_keywords": [],
            },
        )
        cluster["competitor_keywords"].append(keyword)
        if keyword.lower() not in brand_set:
            cluster["gap_keywords"].append(keyword)

    cluster_cards: list[dict] = []
    gap_keywords: list[str] = []
    for cluster in clusters.values():
        unique_gaps = list(dict.fromkeys(cluster["gap_keywords"]))
        unique_brand = list(dict.fromkeys(cluster["brand_keywords"]))
        unique_competitor = list(dict.fromkeys(cluster["competitor_keywords"]))
        unique_quick_wins = list(dict.fromkeys(cluster["quick_win_keywords"]))
        score = min(
            100,
            len(unique_gaps) * 25
            + len(unique_quick_wins) * 20
            + max(0, len(unique_competitor) - len(unique_brand)) * 10,
        )
        gap_keywords.extend(unique_gaps)
        cluster_cards.append(
            {
                "name": cluster["name"],
                "brand_keyword_count": len(unique_brand),
                "competitor_keyword_count": len(unique_competitor),
                "gap_keywords": unique_gaps[:5],
                "quick_win_keywords": unique_quick_wins[:3],
                "opportunity_score": score,
            }
        )

    cluster_cards.sort(
        key=lambda item: (
            -item["opportunity_score"],
            -len(item["gap_keywords"]),
            item["name"],
        )
    )

    return {
        "top_clusters": cluster_cards[:3],
        "gap_keywords": list(dict.fromkeys(gap_keywords))[:8],
    }


def _build_opportunities(
    tracked_keywords: list[dict],
    serp_latest: list[dict],
    latest_scans: dict,
    discussions: list[dict],
    competitor_keywords: list[dict],
    cluster_summary: dict,
) -> dict:
    tracked_lookup = {item["keyword"].lower() for item in tracked_keywords}
    competitor_counts = Counter(
        item["keyword"].lower()
        for item in competitor_keywords
        if item["keyword"].lower() not in tracked_lookup
    )
    competitor_lookup: dict[str, dict] = {}
    for item in competitor_keywords:
        competitor_lookup.setdefault(item["keyword"].lower(), item)

    items: list[dict] = []

    for serp in serp_latest:
        position = serp.get("position")
        if position is None or not 11 <= position <= 20:
            continue
        score = max(55, 95 - (position - 11) * 5)
        items.append(
            {
                "type": "quick_win",
                "domain": "serp",
                "title": f"Push '{serp['keyword']}' onto page 1",
                "summary": f"Currently ranking at #{position}. Tighten the target page and internal links to move into the top 10.",
                "priority": _priority_from_score(score),
                "score": score,
                "recommended_action": "Refresh the ranking page and strengthen internal linking around this keyword.",
                "evidence_refs": [
                    _metric_ref(
                        "serp",
                        "serp_snapshot",
                        "position",
                        str(position),
                        serp.get("url_found"),
                    )
                ],
            }
        )

    for keyword_lower, competitor_count in competitor_counts.most_common(2):
        item = competitor_lookup[keyword_lower]
        score = min(90, 55 + competitor_count * 15)
        items.append(
            {
                "type": "competitor_gap",
                "domain": "graph",
                "title": f"Cover competitor-owned term '{item['keyword']}'",
                "summary": "Tracked competitors are already visible on this term, but it is missing from your current keyword baseline.",
                "priority": _priority_from_score(score),
                "score": score,
                "recommended_action": "Add this keyword to tracking and build supporting content around the cluster.",
                "evidence_refs": [
                    _metric_ref(
                        "graph",
                        "competitor_keyword",
                        "competitor_mentions",
                        str(competitor_count),
                        item.get("competitor_url"),
                    )
                ],
            }
        )

    community_hits = (latest_scans.get("community") or {}).get("total_hits")
    if community_hits == 0 or not discussions:
        score = 68
        items.append(
            {
                "type": "community_activation",
                "domain": "community",
                "title": "Seed visibility in discussion-heavy communities",
                "summary": "The latest scan did not find live brand discussions, so your discovery loop still depends on direct publishing and outreach.",
                "priority": _priority_from_score(score),
                "score": score,
                "recommended_action": "Create founder-led posts and replies in channels where buyers compare alternatives.",
                "evidence_refs": [
                    _metric_ref(
                        "community",
                        "community_scan",
                        "total_hits",
                        str(community_hits or 0),
                    )
                ],
            }
        )

    top_cluster = cluster_summary["top_clusters"][0] if cluster_summary["top_clusters"] else None
    if top_cluster and top_cluster["gap_keywords"]:
        score = min(88, 50 + len(top_cluster["gap_keywords"]) * 12 + top_cluster["opportunity_score"] // 4)
        items.append(
            {
                "type": "topic_cluster_gap",
                "domain": "content",
                "title": f"Build authority in the '{top_cluster['name']}' cluster",
                "summary": f"{len(top_cluster['gap_keywords'])} related gap keywords are still owned by competitors in this cluster.",
                "priority": _priority_from_score(score),
                "score": score,
                "recommended_action": "Plan a cluster-level content pass instead of shipping one isolated page.",
                "evidence_refs": [
                    _metric_ref(
                        "content",
                        "cluster_summary",
                        "gap_keywords",
                        str(len(top_cluster["gap_keywords"])),
                    )
                ],
            }
        )

    items.sort(key=lambda item: (-item["score"], item["title"]))
    summary = {key: 0 for key in _OPPORTUNITY_TYPES}
    for item in items:
        summary[item["type"]] = summary.get(item["type"], 0) + 1
    summary["total"] = len(items)

    return {
        "summary": summary,
        "top": items[:5],
    }


async def build_project_opportunity_snapshot(project_id: int) -> dict:
    """Build a compact opportunity and cluster summary for a project."""
    (
        tracked_keywords,
        serp_latest,
        latest_scans,
        discussions,
        competitors,
    ) = await asyncio.gather(
        storage.list_tracked_keywords(project_id),
        storage.get_all_serp_latest(project_id),
        storage.get_latest_scans(project_id),
        storage.get_tracked_discussions(project_id),
        storage.list_competitors(project_id),
    )

    competitor_keywords: list[dict] = []
    if competitors:
        keyword_lists = await asyncio.gather(
            *[storage.list_competitor_keywords(item["id"]) for item in competitors]
        )
        for competitor, keywords in zip(competitors, keyword_lists):
            for keyword in keywords:
                competitor_keywords.append(
                    {
                        "keyword": keyword["keyword"],
                        "competitor_name": competitor["name"],
                        "competitor_url": competitor.get("url"),
                    }
                )

    cluster_summary = _build_cluster_summary(tracked_keywords, serp_latest, competitor_keywords)
    opportunities = _build_opportunities(
        tracked_keywords,
        serp_latest,
        latest_scans,
        discussions,
        competitor_keywords,
        cluster_summary,
    )

    return {
        "opportunities": opportunities,
        "cluster_summary": cluster_summary,
    }
