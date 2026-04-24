"""AI CMO report generation for strategic briefs and periodic reports."""

from __future__ import annotations

import asyncio
import html
import json
import logging
from datetime import datetime, timedelta, timezone

from aicmo import storage
from aicmo.opportunities import build_project_opportunity_snapshot

logger = logging.getLogger(__name__)

_REPORT_MODEL_DEFAULT = "gpt-5.4"
_PERIODIC_WINDOW_DAYS = 7
_REPORT_LLM_TIMEOUT_SECONDS = 300.0
_REPORT_SYSTEM_COMMON = (
    "You are the AI CMO (Chief Marketing Officer), equipped with a comprehensive multi-agent marketing system: "
    "SEO Audit Expert, GEO (AI Search Visibility) Analyst, SERP Rank Tracker, Community Sentiment Monitor "
    "(Reddit, HN, Dev.to, Twitter, etc.), AI Citability Assessment Engine, AI Crawler Detection Module, "
    "Brand Footprint Scanner, Competitive Knowledge Graph, and Insights Engine.\n\n"
    "The following facts are primary data collected by these agents during real-time operations.\n\n"
    "[Scoring & Scale Standards (100-point scale)]\n"
    "- All core health metrics must use a strict **0-100 scale** for evaluation and display:\n"
    "  - `seo_health_score` (0-100): SEO rating combining technical foundations and page quality.\n"
    "  - `geo_score` (0-100): AI visibility rating combining mention rate and sentiment.\n"
    "  - `engagement_score` (0-100): Algorithm-normalized relative potential and heat of community discussions.\n"
    "- The `raw_score` (e.g., 16,525) in the facts represents the **absolute physical traffic** (views/likes/etc.) and "
    "must **NOT** be used as a 'score'. Instead, interpret it as specific 'traffic performance' and 'growth bottlenecks' "
    "in cross-comparison (e.g., high traffic but extremely low search growth).\n\n"
    "Core Principles:\n"
    "1. You must deeply interpret every category of data in the facts; do not omit output from any agent.\n"
    "2. Do not use vague 'score' expressions; specify 'SEO Health Score', 'Community Traffic Performance', etc., "
    "and do not deviate from factual data.\n"
    "3. Do not just list data; perform business reasoning like a real CMO—why can't high traffic translate to high rankings? "
    "What is the impact on growth? What should be done?\n"
    "4. Do not fabricate data; if data for a dimension is missing, explicitly note it and explain how to obtain it.\n"
    "5. You must use {language} for the output. The report should be sufficiently deep and detailed, like a "
    "business analysis document for a CEO/Investor audience.\n"
)
_REPORT_EVIDENCE_DISCIPLINE = (
    "[Evidence Discipline]\n"
    "- Write confirmed facts first, then inferences, and finally recommendations.\n"
    "- Your expression must distinguish between: Fact / Inference / Recommendation.\n"
    "- Missing data must be explicitly noted; do not fabricate numbers, cases, competitor conclusions, or growth results.\n"
    "- When samples are sparse, reduce tone intensity and state the confidence boundaries of the conclusion.\n"
)


def _compose_report_system_prompt(language: str, *sections: str) -> str:
    return "".join((_REPORT_SYSTEM_COMMON.format(language=language), _REPORT_EVIDENCE_DISCIPLINE, *sections))


def _json_dump(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def _filter_window(items: list[dict], field: str, start: datetime) -> list[dict]:
    result: list[dict] = []
    for item in items:
        timestamp = _parse_ts(item.get(field))
        if timestamp and timestamp >= start:
            result.append(item)
    return result


def _safe_delta(latest, previous):
    if latest is None or previous is None:
        return None
    return latest - previous


def _rank_label(position: int | None) -> str:
    if position is None:
        return "Not Ranked"
    return f"#{position}"


def _classify_findings(findings: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    validated: list[dict] = []
    environment_limitations: list[dict] = []
    hypotheses: list[dict] = []
    for finding in findings:
        metadata = finding.get("metadata") or {}
        status = metadata.get("status", "likely")
        if status == "environment_limitation":
            environment_limitations.append(finding)
        elif status == "hypothesis":
            hypotheses.append(finding)
        else:
            validated.append(finding)
    return validated, environment_limitations, hypotheses


def _simple_markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    html_lines: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html_lines.append("</ul>")
            in_list = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            close_list()
            continue
        if stripped.startswith("### "):
            close_list()
            html_lines.append(f"<h3>{html.escape(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            close_list()
            html_lines.append(f"<h2>{html.escape(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            close_list()
            html_lines.append(f"<h1>{html.escape(stripped[2:])}</h1>")
            continue
        if stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{html.escape(stripped[2:])}</li>")
            continue
        close_list()
        html_lines.append(f"<p>{html.escape(stripped)}</p>")

    close_list()
    return "\n".join(html_lines)


async def _generate_llm_markdown(system_prompt: str, user_prompt: str, *, model_override: str | None = None) -> str:
    """Generate markdown with the configured LLM."""
    from aicmo import llm

    api_key = await llm.get_key_async("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    timeout = await _get_report_timeout_seconds()
    return await llm.chat_completion(
        system_prompt, user_prompt,
        temperature=0.5,
        timeout=timeout,
        model_override=model_override,
    )


async def _generate_llm_markdown_with_empty_retry(
    system_prompt: str,
    user_prompt: str,
    *,
    primary_model: str,
) -> tuple[str, str | None]:
    """Generate markdown and retry once on the same model when the content is empty."""
    content = await _generate_llm_markdown(system_prompt, user_prompt, model_override=primary_model)
    if content.strip():
        return content, None

    retry_content = await _generate_llm_markdown(
        system_prompt,
        user_prompt,
        model_override=primary_model,
    )
    if retry_content.strip():
        return retry_content, primary_model
    raise RuntimeError("LLM returned empty report content.")


async def _get_runtime_setting(key: str, default: str | None = None) -> str | None:
    from aicmo import llm
    return await llm.get_key_async(key, default)


async def _get_report_model() -> str:
    from aicmo import llm
    return await llm.get_model()


async def _get_report_timeout_seconds() -> float:
    raw_value = await _get_runtime_setting(
        "AICMO_REPORT_LLM_TIMEOUT_SECONDS",
        str(_REPORT_LLM_TIMEOUT_SECONDS),
    )
    try:
        timeout = float(raw_value or _REPORT_LLM_TIMEOUT_SECONDS)
    except (TypeError, ValueError):
        return _REPORT_LLM_TIMEOUT_SECONDS
    return max(1.0, timeout)


async def _get_recent_recommendations(project_id: int, limit: int = 6) -> list[dict]:
    db = await storage.get_db()
    try:
        cursor = await db.execute(
            """SELECT rec.domain, rec.priority, rec.owner_type, rec.action_type,
                      rec.title, rec.summary, rec.rationale
               FROM scan_recommendations rec
               JOIN scan_runs r ON r.id = rec.run_id
               WHERE r.project_id = ?
               ORDER BY r.id DESC,
                 CASE rec.priority
                   WHEN 'high' THEN 0
                   WHEN 'medium' THEN 1
                   ELSE 2
                 END,
                 rec.id
               LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "domain": row[0],
                "priority": row[1],
                "owner_type": row[2],
                "action_type": row[3],
                "title": row[4],
                "summary": row[5],
                "rationale": row[6],
            }
            for row in rows
        ]
    finally:
        await db.close()


async def _get_recent_approvals(project_id: int, start: datetime) -> list[dict]:
    db = await storage.get_db()
    try:
        cursor = await db.execute(
            """SELECT id, approval_type, status, title, agent_name, created_at, decided_at
               FROM approvals
               WHERE project_id = ?
               ORDER BY created_at DESC, id DESC
               LIMIT 20""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        approvals = [
            {
                "id": row[0],
                "approval_type": row[1],
                "status": row[2],
                "title": row[3],
                "agent_name": row[4],
                "created_at": row[5],
                "decided_at": row[6],
            }
            for row in rows
        ]
    finally:
        await db.close()
    return _filter_window(approvals, "created_at", start)


async def _build_strategic_facts(project_id: int) -> tuple[dict, dict]:
    project = await storage.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found.")

    # Parallel data aggregation - Phase 1 optimization
    (
        keywords,
        competitors,
        latest,
        previous,
        monitoring,
        findings,
        recommendations,
        previous_human,
        insights,
        citability_history,
        ai_crawler_history,
        brand_presence_history,
        discussions,
        serp_latest,
        opportunity_snapshot,
    ) = await asyncio.gather(
        storage.list_tracked_keywords(project_id),
        storage.list_competitors(project_id),
        storage.get_latest_scans(project_id),
        storage.get_previous_scans(project_id),
        storage.get_latest_monitoring_summary(project_id),
        storage.get_task_findings_by_project(project_id, limit=15),
        _get_recent_recommendations(project_id, limit=12),
        storage.get_latest_report(project_id, "strategic", "human"),
        storage.list_insights(project_id=project_id, limit=15),
        storage.get_citability_history(project_id, limit=3),
        storage.get_ai_crawler_history(project_id, limit=3),
        storage.get_brand_presence_history(project_id, limit=3),
        storage.get_tracked_discussions(project_id),
        storage.get_all_serp_latest(project_id),
        build_project_opportunity_snapshot(project_id),
    )
    findings, environment_limitations, hypothesis_findings = _classify_findings(findings)
    findings, environment_limitations, hypothesis_findings = _classify_findings(findings)

    # Fetch competitor keywords in parallel using batch query
    competitor_cards: list[dict] = []
    if competitors:
        competitor_ids = [comp["id"] for comp in competitors]
        competitor_keywords_map = await storage.batch_list_competitor_keywords(competitor_ids)
        for competitor in competitors:
            competitor_cards.append({
                **competitor,
                "keywords": competitor_keywords_map.get(competitor["id"], []),
            })
    else:
        competitor_cards = []

    # Try to get knowledge graph data for competitive landscape
    graph_data = None
    try:
        expansion = await storage.get_expansion(project_id)
        if expansion:
            graph_data = await storage.get_graph_data(expansion["id"])
    except Exception:
        pass  # graph may not exist yet

    # Recent approvals (last 30 days for strategic context)
    approvals_window = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    recent_approvals = await _get_recent_approvals(project_id, approvals_window)

    seo_score = latest.get("seo", {}).get("score") if latest.get("seo") else None
    geo_score = latest.get("geo", {}).get("score") if latest.get("geo") else None
    community_hits = latest.get("community", {}).get("total_hits") if latest.get("community") else None
    seo_delta = _safe_delta(
        latest.get("seo", {}).get("score") if latest.get("seo") else None,
        previous.get("seo", {}).get("score") if previous and previous.get("seo") else None,
    )
    geo_delta = _safe_delta(
        latest.get("geo", {}).get("score") if latest.get("geo") else None,
        previous.get("geo", {}).get("score") if previous and previous.get("geo") else None,
    )

    strengths: list[str] = []
    if seo_score is not None and seo_score >= 0.8:
        strengths.append(f"SEO health score reached {round(seo_score * 100)}%, technical foundations are stable.")
    if geo_score is not None and geo_score >= 60:
        strengths.append(f"GEO score is {geo_score}/100, AI visibility foundation has been formed.")
    if community_hits:
        strengths.append(f"Found {community_hits} relevant discussions in communities; organic signals are operational.")
    if serp_latest:
        ranked = [item for item in serp_latest if item.get("position")]
        if ranked:
            strengths.append(f"{len(ranked)}/{len(serp_latest)} tracked keywords have entered search results.")
    if citability_history:
        avg = citability_history[0].get("avg_score")
        if avg and avg >= 0.6:
            strengths.append(f"AI Citability score is {round(avg * 100)}%, high potential for content to be cited by AI.")
    if brand_presence_history:
        fp = brand_presence_history[0].get("footprint_score")
        if fp and fp >= 60:
            strengths.append(f"Brand Digital Footprint score is {fp}/100, online presence is established.")
    if ai_crawler_history:
        blocked = ai_crawler_history[0].get("blocked_count", 0)
        total = ai_crawler_history[0].get("total_crawlers", 14)
        if blocked == 0:
            strengths.append(f"All {total} AI crawlers are allowed, fully open to AI indexing.")

    risks: list[str] = []
    if seo_score is None:
        risks.append("SEO baseline is still incomplete.")
    elif seo_score < 0.7:
        risks.append(f"SEO health score is only {round(seo_score * 100)}%, technical side is lagging.")
    if geo_score is None:
        risks.append("GEO data is missing; AI channel awareness is a blind spot.")
    elif geo_score < 45:
        risks.append(f"GEO score is {geo_score}/100, AI platform recognition is weak.")
    if not competitor_cards:
        risks.append("Competitor profiles are still thin.")
    if findings:
        risks.append(f"The most recent monitoring still has {len(findings)} pending findings.")
    if environment_limitations:
        risks.append(f"There are {len(environment_limitations)} monitoring limitations due to environment or provider issues; interpret with caution.")
    if citability_history:
        avg = citability_history[0].get("avg_score")
        if avg is not None and avg < 0.4:
            risks.append(f"AI Citability score is only {round(avg * 100)}%; content structure is insufficient for AI citation.")
    if ai_crawler_history:
        blocked = ai_crawler_history[0].get("blocked_count", 0)
        if blocked > 3:
            risks.append(f"{blocked} AI crawlers are blocked by robots.txt, AI indexing is restricted.")
    if brand_presence_history:
        fp = brand_presence_history[0].get("footprint_score")
        if fp is not None and fp < 30:
            risks.append(f"Brand Digital Footprint score is only {fp}/100, online presence is weak.")
    # Flag critical/warning insights as risks
    critical_insights = [i for i in insights if i.get("severity") in ("critical", "warning")]
    for ins in critical_insights[:3]:
        risks.append(f"[{ins['severity'].upper()}] {ins['title']}: {ins['summary']}")

    change_lines: list[str] = []
    if previous_human:
        if seo_delta is not None:
            change_lines.append(f"SEO changed by {seo_delta:+.2f} compared to the previous version.")
        if geo_delta is not None:
            change_lines.append(f"GEO changed by {geo_delta:+.0f} compared to the previous version.")
        if serp_latest:
            top_keyword = serp_latest[0]
            change_lines.append(
                f"Current top tracked keyword {top_keyword['keyword']} is ranked {_rank_label(top_keyword.get('position'))}."
            )

    facts = {
        "project": project,
        "keywords": keywords,
        "competitors": competitor_cards,
        "latest_scans": latest,
        "previous_scans": previous,
        "monitoring_summary": monitoring,
        "findings": findings,
        "environment_limitations": environment_limitations,
        "hypothesis_findings": hypothesis_findings,
        "recommendations": recommendations,
        "insights": insights,
        "citability": citability_history,
        "ai_crawler": ai_crawler_history,
        "brand_presence": brand_presence_history,
        "discussions": discussions[:12],
        "serp_latest": serp_latest,
        "opportunities": opportunity_snapshot["opportunities"],
        "cluster_summary": opportunity_snapshot["cluster_summary"],
        "graph_data": graph_data,
        "recent_approvals": recent_approvals,
        "strengths": strengths,
        "risks": risks,
        "change_lines": change_lines,
        "previous_report_excerpt": (previous_human["content"][:2000] if previous_human else ""),
    }
    data_sources = [
        latest.get("seo"), latest.get("geo"), latest.get("community"),
        serp_latest, keywords, competitor_cards, insights,
        citability_history, ai_crawler_history, brand_presence_history,
        discussions, graph_data,
    ]
    sample_count = sum(1 for item in data_sources if item)
    meta = {
        "sample_count": sample_count,
        "total_data_sources": len(data_sources),
        "low_sample": sample_count < 3,
        "facts_summary": (
            f"{len(keywords)} keywords, {len(competitor_cards)} competitors, "
            f"{len(findings)} validated findings, {len(recommendations)} recommendations, "
            f"{len(insights)} insights, {len(discussions)} community discussions, "
            f"{len(citability_history)} citation analyses, {len(ai_crawler_history)} crawler checks, "
            f"{len(brand_presence_history)} brand presence analyses"
        ),
        "change_count": len(change_lines),
    }
    return facts, meta


async def _build_periodic_facts(
    project_id: int,
    *,
    now: datetime | None = None,
    window_days: int = _PERIODIC_WINDOW_DAYS,
) -> tuple[dict, dict]:
    project = await storage.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found.")

    if now is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
    elif now.tzinfo is not None:
        now = now.astimezone(timezone.utc).replace(tzinfo=None)
    window_start_dt = now - timedelta(days=window_days)
    window_start = window_start_dt.isoformat(timespec="seconds")
    window_end = now.isoformat(timespec="seconds")

    # Parallel data aggregation - Phase 1 optimization
    (
        seo_history_raw,
        geo_history_raw,
        community_history_raw,
        discussions,
        recent_approvals,
        recommendations,
        findings,
        serp_latest,
        insights,
        citability_history,
        ai_crawler_history,
        brand_presence_history,
        opportunity_snapshot,
    ) = await asyncio.gather(
        storage.get_seo_history(project_id, limit=30),
        storage.get_geo_history(project_id, limit=30),
        storage.get_community_history(project_id, limit=30),
        storage.get_tracked_discussions(project_id),
        _get_recent_approvals(project_id, window_start_dt),
        _get_recent_recommendations(project_id, limit=12),
        storage.get_task_findings_by_project(project_id, limit=15),
        storage.get_all_serp_latest(project_id),
        storage.list_insights(project_id=project_id, limit=15),
        storage.get_citability_history(project_id, limit=5),
        storage.get_ai_crawler_history(project_id, limit=5),
        storage.get_brand_presence_history(project_id, limit=5),
        build_project_opportunity_snapshot(project_id),
    )
    findings, environment_limitations, hypothesis_findings = _classify_findings(findings)

    # Apply time window filtering
    seo_history = _filter_window(seo_history_raw, "scanned_at", window_start_dt)
    geo_history = _filter_window(geo_history_raw, "scanned_at", window_start_dt)
    community_history = _filter_window(community_history_raw, "scanned_at", window_start_dt)

    data_sources = [seo_history, geo_history, community_history, serp_latest,
                    insights, citability_history, ai_crawler_history, brand_presence_history]
    sample_count = sum(1 for items in data_sources if items)
    low_sample = sample_count < 2

    seo_delta = None
    if len(seo_history) >= 2:
        seo_delta = _safe_delta(seo_history[0].get("score_performance"), seo_history[-1].get("score_performance"))
    geo_delta = None
    if len(geo_history) >= 2:
        geo_delta = _safe_delta(geo_history[0].get("geo_score"), geo_history[-1].get("geo_score"))
    community_delta = None
    if len(community_history) >= 2:
        community_delta = _safe_delta(community_history[0].get("total_hits"), community_history[-1].get("total_hits"))

    top_changes: list[str] = []
    if seo_history:
        current = seo_history[0].get("score_performance")
        if current is not None:
            line = f"Latest SEO Score: {round(current * 100)}%"
            if seo_delta is not None:
                line += f", window change: {seo_delta:+.2f}"
            top_changes.append(line + ".")
    if geo_history:
        current = geo_history[0].get("geo_score")
        if current is not None:
            line = f"Latest GEO Score: {current}/100"
            if geo_delta is not None:
                line += f", window change: {geo_delta:+.0f}"
            top_changes.append(line + ".")
    if community_history:
        current = community_history[0].get("total_hits")
        if current is not None:
            line = f"Latest Community Hits: {current}"
            if community_delta is not None:
                line += f", window change: {community_delta:+.0f}"
            top_changes.append(line + ".")
    if serp_latest:
        ranked = [item for item in serp_latest if item.get("position")]
        top_changes.append(f"Currently {len(ranked)}/{len(serp_latest)} keywords have entered organic search results.")
    if citability_history:
        avg = citability_history[0].get("avg_score")
        if avg is not None:
            top_changes.append(f"AI Citability Score: {round(avg * 100)}%.")
    if brand_presence_history:
        fp = brand_presence_history[0].get("footprint_score")
        if fp is not None:
            top_changes.append(f"Brand Digital Footprint: {fp}/100.")
    if low_sample:
        top_changes.insert(0, "Samples are sparse; the following conclusions are for directional judgment only.")

    facts = {
        "project": project,
        "window_start": window_start,
        "window_end": window_end,
        "seo_history": seo_history,
        "geo_history": geo_history,
        "community_history": community_history,
        "discussions": discussions[:12],
        "serp_latest": serp_latest,
        "opportunities": opportunity_snapshot["opportunities"],
        "cluster_summary": opportunity_snapshot["cluster_summary"],
        "findings": findings,
        "environment_limitations": environment_limitations,
        "hypothesis_findings": hypothesis_findings,
        "recommendations": recommendations,
        "insights": insights,
        "citability": citability_history,
        "ai_crawler": ai_crawler_history,
        "brand_presence": brand_presence_history,
        "recent_approvals": recent_approvals,
        "top_changes": top_changes[:5],
    }
    meta = {
        "sample_count": sample_count,
        "total_data_sources": len(data_sources),
        "low_sample": low_sample,
        "facts_summary": (
            f"SEO samples {len(seo_history)}, GEO samples {len(geo_history)}, "
            f"Community samples {len(community_history)}, SERP keywords {len(serp_latest)}, "
            f"validated findings {len(findings)}, environment limitations {len(environment_limitations)}, "
            f"insights {len(insights)}, citation analyses {len(citability_history)}, "
            f"crawler checks {len(ai_crawler_history)}, brand presence analyses {len(brand_presence_history)}"
        ),
        "window_days": window_days,
        "window_start": window_start,
        "window_end": window_end,
    }
    return facts, meta


def _failed_report_payload(meta: dict, model: str, *, used_pipeline: bool, llm_error: str, pipeline_error: str | None = None) -> dict:
    record_meta = {
        **meta,
        "used_fallback": False,
        "used_pipeline": used_pipeline,
        "model": model,
        "llm_error": llm_error,
    }
    if pipeline_error:
        record_meta["pipeline_error"] = pipeline_error
    return {
        "generation_status": "failed",
        "content": "",
        "content_html": "",
        "meta": record_meta,
    }


def _prompts(kind: str, audience: str, facts: dict, meta: dict, previous_exists: bool, locale: str = "en") -> tuple[str, str]:
    project = facts["project"]
    language = "English" if locale == "en" else "Chinese"
    if kind == "strategic" and audience == "human":
        system = _compose_report_system_prompt(
            language,
            "Your task is to generate an extremely in-depth strategic analysis report. Output in Markdown. "
            "The total report length should be between 2000-4000 words.\n\n"
            "Strictly follow the 6-module structure below. Each module must be discussed in detail; "
            "do not use short, perfunctory sentences:\n\n"
            "## 1. Executive Summary & Project Characterization\n"
            "  - Define the project's current growth stage in one sentence.\n"
            "  - Comprehensively evaluate the project's 'Digital Health' across metrics like SEO Score, GEO Score, Brand Footprint, AI Citability, etc.\n"
            "  - If historical reports exist, compare version differences and provide trend judgments.\n\n"
            "## 2. Core Competencies & Competitive Moat Analysis\n"
            "  - Interpret the business meaning behind each strength signal.\n"
            "  - Analyze the impact of AI Citability and AI Crawler status on 'being recommended by AI'.\n"
            "  - Synergy between positive community signals and brand digital footprint.\n"
            "  - What traffic opportunities do the keywords already captured in SERP rankings imply?\n\n"
            "## 3. Risk Scanning & Growth Bottleneck Warning\n"
            "  - Deeply interpret the root cause and potential impact of each risk signal.\n"
            "  - Cross-validate with warning/critical alerts in the Insights system.\n"
            "  - Evaluate which risks directly affect acquisition conversion and which are long-term hidden dangers.\n"
            "  - Provide a risk priority ranking.\n\n"
            "## 4. Competitive Landscape & Traffic Hijacking Analysis\n"
            "  - If competitor and knowledge graph data exist, perform detailed competitive analysis.\n"
            "  - Keyword overlap and differentiation opportunities.\n"
            "  - Direct competitive situation in SERP.\n"
            "  - Relative position in AI Search (GEO).\n"
            "  - If competitor data is incomplete, specify how to supplement it.\n\n"
            "## 5. Audience & Community Sentiment Insights\n"
            "  - Analyze themes and emotional tone of community discussions.\n"
            "  - Infer user personas from community traffic sources (Reddit, HN, etc.).\n"
            "  - Assess content output momentum in the approval queue.\n"
            "  - Differences in brand presence across various platforms.\n\n"
            "## 6. Next-Phase CMO Strategy & Execution Roadmap\n"
            "  - Provide 3-5 actionable strategic directions based on all the above analysis.\n"
            "  - Each direction must specify: Executing Agent, expected metric changes, implementation priority.\n"
            "  - Provide a clear '30-Day Action Roadmap'.\n"
            "  - Mark key nodes requiring human intervention.\n"
        )
        user = (
            f"Project: {project['brand_name']} ({project['category']})\n"
            f"Target URL: {project['url']}\n"
            f"Previous report exists: {previous_exists}\n"
            f"Data coverage: {meta.get('sample_count', 0)}/{meta.get('total_data_sources', 0)} data sources active\n"
            f"Summary Metadata: {_json_dump(meta)}\n\n"
            f"=== Full Fact Bundle (Collected from all agents) ===\n{_json_dump(facts)}"
        )
        return system, user

    if kind == "strategic" and audience == "agent":
        system = _compose_report_system_prompt(
            language,
            "Output in Markdown. This is an actionable brief for AI Agents and the execution team. "
            "Structure is fixed as:\n\n"
            "## 1. Must-Do This Week (P0)\n"
            "   - List 2-3 highest priority tasks.\n"
            "   - Each task must clearly state: Action, Owner (if applicable), Completion Criteria.\n"
            "   - Write tasks in natural language; do not use placeholder numbers, fictional commands, "
            "or non-existent system capabilities.\n\n"
            "## 2. Monthly Momentum (P1-P2)\n"
            "   - Provide momentum or milestones for Weeks 1-4.\n"
            "   - Each week should state Goal, Dependencies, Expected Output.\n\n"
            "## 3. Configuration & Dependencies\n"
            "   - List missing configurations, data sources, or human decisions.\n"
            "   - If there is no explicit command or automation entry in the system, describe the "
            "capability requirement; do not fabricate a CLI.\n\n"
            "## 4. Checkpoints & Risk Signals\n"
            "   - Provide checkpoints or observation signals for Day 1/7/14.\n"
            "   - Target values are allowed only if they already exist in the facts; otherwise, write as "
            "qualitative check items.\n\n"
            "## 5. Agent Automated vs. Human Intervention\n"
            "   - Clearly distinguish between actions that existing Agents can perform directly and "
            "those requiring human approval, external accounts, or additional tools.\n\n"
            "## 6. Key Data Snapshot\n"
            "   - Only reference core KPIs that already exist in the facts; do not fabricate new quantitative metrics."
        )
        user = (
            f"Project: {project['brand_name']} ({project['category']})\n"
            f"Data coverage: {meta.get('sample_count', 0)}/{meta.get('total_data_sources', 0)} data sources active\n"
            f"Summary Metadata: {_json_dump(meta)}\n\n"
            f"=== Full Fact Bundle (Collected from all agents) ===\n{_json_dump(facts)}"
        )
        return system, user

    if kind == "periodic" and audience == "human":
        system = _compose_report_system_prompt(
            language,
            "Your task is to generate an in-depth weekly report. Output in Markdown. "
            "Total report length should be between 1500-3000 words.\n\n"
            "Strictly follow the structure below. Perform deep business derivation for each module; "
            "do not stop at the data listing level:\n\n"
            "## 1. Most Important Changes This Week (Top Changes)\n"
            "  - List 3-5 most important changes. For each, explain not just 'what happened', "
            "but 'why it matters' and 'what it means for growth'.\n"
            "  - Coverage should include changes in AI Citability and Brand Footprint.\n\n"
            "## 2. Deep Multi-Dimensional Trend Analysis (SEO/GEO/SERP/Community/Citability/Footprint)\n"
            "  - Perform trend diagnosis (Up/Down/Flat) for each dimension with data and analyze the underlying reasons.\n"
            "  - Conduct cross-dimensional correlation analysis: e.g., did a drop in SEO score affect SERP rankings? "
            "Did an increase in community discussion drive GEO visibility?\n"
            "  - Any changes in AI Crawler status? What is the trend for AI Citability?\n\n"
            "## 3. New Risks & Wins This Week\n"
            "  - Deeply interpret alerts from the Insights system.\n"
            "  - For risks, provide specific impact assessments and mitigation suggestions.\n"
            "  - For wins, explain how to expand on the results.\n\n"
            "## 4. Competitive & Market Signal Changes\n"
            "  - Any new competitor-related movements in community discussions.\n"
            "  - Competitor rank changes in SERP.\n"
            "  - Status of content output in the approval queue.\n\n"
            "## 5. Next Week's Strategic Focus & Execution Plan (Next Week Strategy)\n"
            "  - Provide 3-5 specific action items for next week.\n"
            "  - Mark the responsible Agent and expected result for each item.\n"
            "  - Note items requiring human decision-making.\n\n"
            "Explicitly mark confidence at the beginning of the report when samples are sparse."
        )
        user = (
            f"Project: {project['brand_name']} ({project['category']})\n"
            f"Statistical window: {meta.get('window_start', 'Unknown')} to {meta.get('window_end', 'Unknown')}\n"
            f"Data coverage: {meta.get('sample_count', 0)}/{meta.get('total_data_sources', 0)} data sources active\n"
            f"Metadata: {_json_dump(meta)}\n\n"
            f"=== Full Fact Bundle (Collected from all agents) ===\n{_json_dump(facts)}"
        )
        return system, user

    # periodic / agent
    system = _compose_report_system_prompt(
        language,
        "Output in Markdown, maintaining a weekly action brief style for execution Agents. "
        "Structure is fixed as:\n"
        "1. Project & Confidence\n"
        "2. Key Metrics Snapshot This Week\n"
        "3. Top Objectives for Next Week\n"
        "4. Priority Directions & Agent Task Allocation\n"
        "5. Guardrails & Prohibited Items"
    )
    user = f"Periodic report fact bundle:\n{_json_dump({'meta': meta, 'facts': facts})}"
    return system, user


async def _generate_report_record(
    *,
    kind: str,
    audience: str,
    facts: dict,
    meta: dict,
    previous_exists: bool,
    locale: str = "en",
    on_progress=None,
) -> dict:
    used_pipeline = False
    used_fallback = False
    llm_error = None
    pipeline_error = None
    model = await _get_report_model()
    report_model = model
    content = ""

    # Human reports use the deep multi-agent pipeline;
    # Agent briefs stay single-call (they need to be concise).
    if audience == "human":
        try:
            from aicmo.report_pipeline import run_deep_report_pipeline

            content = await run_deep_report_pipeline(
                facts, meta, previous_exists, kind=kind,
                locale=locale,
                on_progress=on_progress,
            )
            used_pipeline = True
            if not content.strip():
                raise RuntimeError("Pipeline returned empty report.")
        except Exception as pipeline_exc:
            pipeline_error = str(pipeline_exc) or pipeline_exc.__class__.__name__
            logger.warning(
                "Deep pipeline failed for %s/%s, falling back to single-call: %s",
                kind, audience, pipeline_exc,
            )
            # Fallback to single-call LLM
            try:
                system_prompt, user_prompt = _prompts(kind, audience, facts, meta, previous_exists, locale=locale)
                content, fallback_model = await _generate_llm_markdown_with_empty_retry(
                    system_prompt,
                    user_prompt,
                    primary_model=model,
                )
                used_fallback = True
                if fallback_model:
                    report_model = fallback_model
            except Exception as exc:
                llm_error = str(exc) or exc.__class__.__name__
                logger.exception("Report generation failed for %s/%s", kind, audience)
                return _failed_report_payload(
                    meta,
                    model,
                    used_pipeline=False,
                    llm_error=llm_error,
                    pipeline_error=pipeline_error,
                )
    else:
        # Agent brief — single-call path
        system_prompt, user_prompt = _prompts(kind, audience, facts, meta, previous_exists, locale=locale)
        try:
            content, fallback_model = await _generate_llm_markdown_with_empty_retry(
                system_prompt,
                user_prompt,
                primary_model=model,
            )
            used_fallback = fallback_model is not None
            if fallback_model:
                report_model = fallback_model
        except Exception as exc:
            llm_error = str(exc) or exc.__class__.__name__
            logger.exception("Report generation failed for %s/%s", kind, audience)
            return _failed_report_payload(
                meta,
                model,
                used_pipeline=False,
                llm_error=llm_error,
            )

    record_meta = {
        **meta,
        "used_fallback": used_fallback,
        "used_pipeline": used_pipeline,
        "model": report_model,
    }
    if llm_error:
        record_meta["llm_error"] = llm_error
    if pipeline_error:
        record_meta["pipeline_error"] = pipeline_error

    return {
        "generation_status": "completed",
        "content": content,
        "content_html": _simple_markdown_to_html(content),
        "meta": record_meta,
    }


async def _persist_bundle(
    *,
    project_id: int,
    kind: str,
    source_run_id: int | None,
    window_start: str | None,
    window_end: str | None,
    facts: dict,
    meta: dict,
    locale: str = "en",
    on_progress=None,
) -> dict:
    previous_human = await storage.get_latest_report(project_id, kind, "human")
    records = {
        "human": await _generate_report_record(
            kind=kind,
            audience="human",
            facts=facts,
            meta=meta,
            previous_exists=bool(previous_human),
            locale=locale,
            on_progress=on_progress,
        ),
        "agent": await _generate_report_record(
            kind=kind,
            audience="agent",
            facts=facts,
            meta=meta,
            previous_exists=bool(previous_human),
            locale=locale,
        ),
    }
    created = await storage.create_report_bundle(
        project_id=project_id,
        kind=kind,
        source_run_id=source_run_id,
        window_start=window_start,
        window_end=window_end,
        records=records,
    )
    payload = {"kind": kind}
    payload.update({item["audience"]: item for item in created})
    return payload


async def generate_strategic_report_bundle(project_id: int, source_run_id: int | None = None, on_progress=None, **kwargs) -> dict:
    """Generate and persist the latest strategic report bundle."""
    facts, meta = await _build_strategic_facts(project_id)
    return await _persist_bundle(
        project_id=project_id,
        kind="strategic",
        source_run_id=source_run_id,
        window_start=None,
        window_end=None,
        facts=facts,
        meta=meta,
        locale=kwargs.get("locale", "en"),
        on_progress=on_progress,
    )


async def generate_periodic_report_bundle(
    project_id: int,
    *,
    source_run_id: int | None = None,
    now: datetime | None = None,
    window_days: int = _PERIODIC_WINDOW_DAYS,
    on_progress=None,
    **kwargs,
) -> dict:
    """Generate and persist the latest periodic report bundle."""
    facts, meta = await _build_periodic_facts(project_id, now=now, window_days=window_days)
    return await _persist_bundle(
        project_id=project_id,
        kind="periodic",
        source_run_id=source_run_id,
        window_start=meta["window_start"],
        window_end=meta["window_end"],
        facts=facts,
        meta=meta,
        locale=kwargs.get("locale", "en"),
        on_progress=on_progress,
    )
