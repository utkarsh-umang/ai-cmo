"""Multi-agent deep report pipeline.

Replaces the single-LLM-call report generation with a 6-phase pipeline:
  Phase 1  Reflection Agent    — per-dimension quality auditors (parallel) + aggregator
  Phase 2  Insight Distiller   — per-dimension insight agents (parallel) + cross-cutter
  Phase 3  Outline Planner     — narrative structure with per-section briefs
  Phase 4  Section Writers     — parallel per-section authoring
  Phase 5  Section Grader      — review loop (max 2 retries)
  Phase 6  Report Synthesizer  — per-section summarizers (parallel) + intro/exec/strategy writers

KEY DESIGN: Phases 1, 2, and 6 use MULTIPLE sub-agents per dimension/section
instead of a single monolithic LLM call.  This prevents context overflow when
data is large (e.g. 1000+ keywords, 28 competitors).

Only used for ``audience="human"`` reports.  Agent briefs stay single-call.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Maximum retry count for the grader loop (Phase 5)
_MAX_GRADER_RETRIES = 1  # Phase 1 optimization: reduced from 2 to 1
# Minimum average score to pass the grader
_GRADER_PASS_THRESHOLD = 3.8  # Phase 1 optimization: raised from 3.5 to 3.8 to reduce low-quality retries
# Maximum concurrent LLM calls to prevent API rate limiting
_MAX_CONCURRENT_LLM_CALLS = 3  # conservative default for unstable local gateways


def _json_dump(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _extract_json(text: str) -> dict | list:
    """Best-effort JSON extraction from LLM output that may contain markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()
    return json.loads(cleaned)


def _truncate_list(data: list | None, max_items: int, sort_key: str | None = None) -> list:
    """Truncate a list to max_items, optionally sorting first."""
    if not data:
        return []
    items = list(data)
    if sort_key:
        try:
            items.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
        except Exception:
            pass
    return items[:max_items]


def _get_language(locale: str) -> str:
    """Map locale to human-readable language name."""
    mapping = {
        "en": "English",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
    }
    return mapping.get(locale[:2].lower(), "English")


# ---------------------------------------------------------------------------
# LLM call helpers (import the shared infra from reports.py at call time)
# ---------------------------------------------------------------------------

async def _llm_text_call(system: str, user: str) -> str:
    """Single LLM call returning plain text / markdown."""
    from aicmo.reports import _generate_llm_markdown
    return await _generate_llm_markdown(system, user)


async def _llm_json_call(system: str, user: str) -> dict | list:
    """Single LLM call expecting JSON output."""
    raw = await _llm_text_call(system, user)
    return _extract_json(raw)


# ---------------------------------------------------------------------------
# Data dimension slicing — split facts into per-dimension chunks
# ---------------------------------------------------------------------------

_DIMENSIONS = [
    {
        "id": "seo_tech",
        "name": "SEO & Technical Health",
        "keys": ["seo_latest", "ai_crawler_history"],
        "description": "Website SEO audit data and AI crawler accessibility data",
    },
    {
        "id": "search_visibility",
        "name": "Search Visibility & Rankings",
        "keys": ["serp_snapshots", "keywords"],
        "description": "SERP keyword rankings and search visibility data",
        "truncate": {"keywords": 30, "serp_snapshots": 25},
    },
    {
        "id": "ai_visibility",
        "name": "AI Visibility & Brand Citations",
        "keys": ["geo_latest", "citability_history", "brand_presence_history"],
        "description": "GEO score, AI platform citability, and brand presence",
    },
    {
        "id": "community_market",
        "name": "Community & Market Signals",
        "keys": ["community_latest", "discussions", "insights_history"],
        "description": "Community discussions, market trends, and AI insight alerts",
        "truncate": {"discussions": 15, "insights_history": 10},
    },
    {
        "id": "competitive",
        "name": "Competitive & Ecosystem Positioning",
        "keys": ["competitors", "graph_data", "approvals"],
        "description": "Competitor info, knowledge graph relationships, and content approval queue",
        "truncate": {"competitors": 20},
    },
]


def _slice_dimension(facts: dict, dimension: dict) -> dict:
    """Extract facts for one dimension, applying truncation rules."""
    sliced = {}
    truncate_rules = dimension.get("truncate", {})
    for key in dimension["keys"]:
        data = facts.get(key)
        if data is None:
            sliced[key] = None
            continue
        max_items = truncate_rules.get(key)
        if max_items and isinstance(data, list):
            sliced[key] = _truncate_list(data, max_items)
        else:
            sliced[key] = data
    return sliced


# ===================================================================
# Phase 1 — Reflection Agent (MULTI-AGENT: per-dimension auditors)
# ===================================================================

_REFLECT_DIM_SYSTEM = """\
You are a data quality audit expert focused on the {{dim_name}} dimension.
You MUST respond in {language}. All your analysis and output should be in {language}.

Please audit the following {{dim_name}} dimension data:

1. **Data Completeness**: Is the data complete? Are there missing fields or null values? Is the sample size sufficient?
2. **Data Quality**: Are there outliers? Is the data consistent?
3. **Usability**: Can this data support high-quality analysis? What are the limitations?

Return JSON:
{{
  "dimension": "{dim_id}",
  "quality_score": Integer from 0 to 100,
  "issues": ["Issue description"],
  "anomalies": ["Anomaly description"],
  "summary": "One-sentence summary of the data quality for this dimension",
  "data_available": true/false
}}

You must return valid JSON. Do not wrap it in markdown code blocks."""


_REFLECT_AGG_SYSTEM = """\
You are the head of data quality audit. Below are the audit results from 5 dimension quality experts.
You MUST respond in {language}. All your analysis and output should be in {language}.

Please summarize the audit conclusions for each dimension and complete cross-validation:

1. **Cross-Validation**:
   - Is the SEO audit result consistent with SERP ranking data?
   - Is the GEO score trend contradictory to Brand Presence data?
   - Is there a signal conflict between Community sentiment and Insights alerts?
   - Is the AI Crawler accessibility status coordinated with the Citability score?

2. **Overall Judgment**: Is the overall data sufficient to generate a high-quality report?

Return JSON:
{{
  "data_quality_score": Weighted average integer from 0 to 100,
  "issues": ["Summarized key issues"],
  "anomalies": ["Cross-dimensional anomalies"],
  "cross_validation_notes": ["Cross-validation findings"],
  "validated_summary": "One paragraph summarizing the overall data quality",
  "confidence_level": "high/medium/low",
  "dimension_scores": {{"seo_tech": 80, "search_visibility": 60, ...}}
}}

You must return valid JSON. Do not wrap it in markdown code blocks."""


async def _reflect_one_dimension(facts: dict, dim: dict, meta: dict, locale: str = "en") -> dict:
    """Run one dimension-specific quality auditor."""
    dim_data = _slice_dimension(facts, dim)
    project = facts.get("project", {})
    language = _get_language(locale)
    system = _REFLECT_DIM_SYSTEM.format(language=language).format(dim_name=dim["name"], dim_id=dim["id"])
    user = (
        f"Project: {project.get('brand_name', '?')} ({project.get('category', '?')})\n"
        f"Dimension: {dim['name']} — {dim['description']}\n\n"
        f"=== {dim['name']} Dimension Data ===\n{_json_dump(dim_data)}"
    )
    try:
        result = await _llm_json_call(system, user)
        if not isinstance(result, dict):
            raise ValueError("dimension auditor did not return a JSON object")
        result["dimension"] = dim["id"]
        raw_score = result.get("quality_score")
        result["quality_score"] = int(raw_score) if raw_score is not None else None
        result["data_available"] = bool(result.get("data_available", bool(dim_data)))
        result.setdefault("issues", [])
        result.setdefault("anomalies", [])
        result.setdefault("summary", "")
        return result
    except Exception as exc:
        logger.warning("[Phase 1] Dimension %s audit failed: %s", dim["id"], exc)
        return {
            "dimension": dim["id"],
            "quality_score": None,
            "issues": [str(exc)],
            "anomalies": [],
            "summary": "Audit failed",
            "data_available": False,
            "error": str(exc),
        }


async def _phase_reflect(facts: dict, meta: dict, locale: str = "en") -> dict:
    """Phase 1: Run per-dimension auditors in parallel, then aggregate."""
    logger.info("[Pipeline Phase 1] Reflection — %d dimension auditors in parallel", len(_DIMENSIONS))
    language = _get_language(locale)

    # Run all dimension auditors in parallel with concurrency limit
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_LLM_CALLS)

    async def _bounded_reflect(dim):
        async with semaphore:
            return await _reflect_one_dimension(facts, dim, meta, locale=locale)

    dim_results = await asyncio.gather(
        *[_bounded_reflect(dim) for dim in _DIMENSIONS],
        return_exceptions=True,
    )

    # Collect results
    dim_reports = []
    for i, result in enumerate(dim_results):
        if isinstance(result, Exception):
            logger.warning("[Phase 1] Dimension %s failed: %s", _DIMENSIONS[i]["id"], result)
            dim_reports.append({
                "dimension": _DIMENSIONS[i]["id"],
                "quality_score": None,
                "issues": [str(result)],
                "anomalies": [],
                "summary": "Audit anomaly",
                "data_available": False,
            })
        else:
            dim_reports.append(result)
            logger.info("[Phase 1] Dimension %s — score: %s", result.get("dimension", "?"), result.get("quality_score", "?"))

    # Aggregate with a separate agent
    logger.info("[Pipeline Phase 1] Aggregating %d dimension audits", len(dim_reports))
    project = facts.get("project", {})
    user = (
        f"Project: {project.get('brand_name', '?')} ({project.get('category', '?')})\n"
        f"Data Coverage: {meta.get('sample_count', 0)}/{meta.get('total_data_sources', 0)} sources have data\n\n"
        f"=== Per-Dimension Audit Results ===\n{_json_dump(dim_reports)}"
    )
    try:
        aggregated = await _llm_json_call(_REFLECT_AGG_SYSTEM.format(language=language), user)
        if not isinstance(aggregated, dict):
            raise ValueError("aggregator did not return a JSON object")
        numeric_scores = {
            report["dimension"]: int(report["quality_score"])
            for report in dim_reports
            if report.get("quality_score") is not None
        }
        aggregated.setdefault("dimension_scores", numeric_scores)
        logger.info(
            "[Pipeline Phase 1] Aggregated quality: %s, confidence: %s",
            aggregated.get("data_quality_score", "?"), aggregated.get("confidence_level", "?"),
        )
        return aggregated
    except Exception as exc:
        logger.warning("[Pipeline Phase 1] Aggregation failed: %s — using available dimension scores only", exc)
        numeric_scores = {
            report["dimension"]: int(report["quality_score"])
            for report in dim_reports
            if report.get("quality_score") is not None
        }
        if not numeric_scores:
            raise RuntimeError("No valid dimension quality scores available for aggregation") from exc
        avg = sum(numeric_scores.values()) // len(numeric_scores)
        return {
            "data_quality_score": avg,
            "issues": [iss for r in dim_reports for iss in r.get("issues", [])],
            "anomalies": [iss for r in dim_reports for iss in r.get("anomalies", [])],
            "validated_summary": f"Average quality across dimensions {avg}/100 (aggregation failed, using simple average)",
            "confidence_level": "low",
            "dimension_scores": numeric_scores,
        }


# ===================================================================
# Phase 2 — Insight Distiller (MULTI-AGENT: per-dimension analysts)
# ===================================================================

_DISTILL_DIM_SYSTEM = """\
You are a digital marketing analyst focused on {{dim_name}}.
You MUST respond in {language}. All your analysis and output should be in {language}.

Based on the following {{dim_name}} dimension data, distill analytical findings (insights).

Rules:
1. **Interpret Data**: Do not just list data; answer "so what?"
2. **Trend Judgment**: If historical data is available, judge whether it's up/down/stable and the magnitude of change.
3. **Quantitative Expression**: Use specific numbers; avoid vague expressions.
4. **Prioritization**: Sort by business impact.

Output JSON:
{{
  "dimension": "{dim_id}",
  "insights": [
    {{
      "id": "{dim_id}-INS-001",
      "title": "Short Title",
      "finding": "Detailed finding description, including specific numbers...",
      "evidence": ["{{dim_name}}"],
      "impact_level": "critical/high/medium/low",
      "recommended_section": "Suggested report section theme"
    }}
  ]
}}

Requirement: Produce 2-4 high-quality insights.
You must return valid JSON. Do not wrap it in markdown code blocks."""


_DISTILL_CROSS_SYSTEM = """\
You are a senior cross-dimensional business analyst. Below are the insights distilled by 5 dimension analysts.
You MUST respond in {language}. All your analysis and output should be in {language}.

Your task:

1. **Find Cross-Dimensional Correlations**:
   - E.g., High SEO score but low SERP ranking → Content quality issue.
   - E.g., GEO score rising but Brand Presence unchanged → AI citation is one-off.
   - E.g., High community heat but SERP unchanged → Social signals not converted to search weight.

2. **Distill Overarching Themes**: Identify 2-3 strategic themes that cut across multiple dimensions.

3. **Generate Executive Summary Points**: Distill 3-5 one-sentence core findings based on all insights.

4. **Re-number**: Uniformly number all insights as INS-001, INS-002, ...

Output JSON:
{{
  "insights": [All merged insights, uniformly numbered INS-001...],
  "cross_cutting_themes": ["Theme 1", "Theme 2"],
  "executive_summary_points": ["Core Finding 1", "Core Finding 2"]
}}

You must return valid JSON. Do not wrap it in markdown code blocks."""


async def _distill_one_dimension(facts: dict, dim: dict, reflection: dict, locale: str = "en") -> dict:
    """Run one dimension-specific insight analyst."""
    dim_data = _slice_dimension(facts, dim)
    project = facts.get("project", {})
    dim_score = reflection.get("dimension_scores", {}).get(dim["id"], "?")
    language = _get_language(locale)

    system = _DISTILL_DIM_SYSTEM.format(language=language).format(dim_name=dim["name"], dim_id=dim["id"])
    user = (
        f"Project: {project.get('brand_name', '?')} ({project.get('category', '?')})\n"
        f"Dimension Quality Score: {dim_score}/100\n\n"
        f"=== {dim['name']} Dimension Data ===\n{_json_dump(dim_data)}"
    )
    try:
        result = await _llm_json_call(system, user)
        if not isinstance(result, dict):
            result = {"dimension": dim["id"], "insights": []}
        result["dimension"] = dim["id"]
        logger.info("[Phase 2] Dimension %s — %d insights", dim["id"], len(result.get("insights", [])))
        return result
    except Exception as exc:
        logger.warning("[Phase 2] Dimension %s distill failed: %s", dim["id"], exc)
        return {"dimension": dim["id"], "insights": []}


async def _phase_distill(facts: dict, meta: dict, reflection: dict, locale: str = "en") -> dict:
    """Phase 2: Run per-dimension insight analysts in parallel, then cross-cut."""
    logger.info("[Pipeline Phase 2] Insight Distiller — %d dimension analysts in parallel", len(_DIMENSIONS))
    language = _get_language(locale)

    # Run all dimension analysts in parallel with concurrency limit
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_LLM_CALLS)

    async def _bounded_distill(dim):
        async with semaphore:
            return await _distill_one_dimension(facts, dim, reflection, locale=locale)

    dim_results = await asyncio.gather(
        *[_bounded_distill(dim) for dim in _DIMENSIONS],
        return_exceptions=True,
    )

    # Collect all dimension insights
    all_dim_insights = []
    for i, result in enumerate(dim_results):
        if isinstance(result, Exception):
            logger.warning("[Phase 2] Dimension %s failed: %s", _DIMENSIONS[i]["id"], result)
            continue
        all_dim_insights.append(result)

    total_insights = sum(len(r.get("insights", [])) for r in all_dim_insights)
    logger.info("[Pipeline Phase 2] Collected %d insights from %d dimensions", total_insights, len(all_dim_insights))

    if total_insights == 0:
        raise RuntimeError("All dimension distillers produced 0 insights")

    # Cross-cutting synthesis
    logger.info("[Pipeline Phase 2] Cross-cutting synthesis")
    project = facts.get("project", {})
    user = (
        f"Project: {project.get('brand_name', '?')} ({project.get('category', '?')})\n"
        f"Overall Data Quality: {reflection.get('data_quality_score', '?')}/100\n\n"
        f"=== Per-Dimension Analyst Insights ===\n{_json_dump(all_dim_insights)}"
    )
    try:
        result = await _llm_json_call(_DISTILL_CROSS_SYSTEM.format(language=language), user)
        if not isinstance(result, dict):
            raise ValueError("Cross-cutter did not return a dict")
        insights = result.get("insights", [])
        logger.info("[Pipeline Phase 2] Final: %d insights, %d themes",
                     len(insights), len(result.get("cross_cutting_themes", [])))
        return result
    except Exception as exc:
        logger.warning("[Pipeline Phase 2] Cross-cutting failed: %s — using raw dimension insights", exc)
        # Fallback: merge all dimension insights with sequential numbering
        merged = []
        idx = 1
        for dim_result in all_dim_insights:
            for ins in dim_result.get("insights", []):
                ins["id"] = f"INS-{idx:03d}"
                merged.append(ins)
                idx += 1
        return {
            "insights": merged,
            "cross_cutting_themes": [],
            "executive_summary_points": [ins["title"] for ins in merged[:5]],
        }


# ===================================================================
# Phase 3 — Outline Planner (narrative structure)
# ===================================================================

_PLAN_SYSTEM = """\
You are a senior business report editor-in-chief. Based on the following analysis findings, please plan the outline for a deep business analysis report.
You MUST respond in {language}. All your analysis and output should be in {language}.

Requirements:
1. Total report word count target: 3000-5000 words.
2. Each section must have a clear **Core Thesis** (not a descriptive title).
3. Each section must specify which insights (reference by ID) are used as evidence.
4. Number of sections: 4-6 main sections.
5. Introduction and Strategic Recommendations sections marked as is_final_section: true (they are written last).

Output JSON format:
{{
  "report_title": "Report Title",
  "executive_summary_thesis": "One-sentence summary of the report's core finding",
  "sections": [
    {{
      "id": "sec-1",
      "title": "Thesis-driven section title",
      "thesis": "Core thesis of this section: ...",
      "insight_ids": ["INS-001", "INS-003"],
      "word_budget": 600,
      "is_final_section": false,
      "writing_guidance": "Start with data trends, support with competitor comparisons..."
    }}
  ],
  "narrative_arc": "Report narrative arc: From problem diagnosis → Root cause analysis → Opportunity identification → Action roadmap"
}}

Note: Set is_final_section to false for main sections and true for introduction and strategic recommendations.
You must return valid JSON. Do not wrap it in markdown code blocks."""


async def _phase_plan_outline(
    facts: dict, distilled: dict, reflection: dict, locale: str = "en"
) -> dict:
    """Phase 3: Plan the report outline with per-section briefs."""
    logger.info("[Pipeline Phase 3] Outline Planner — designing narrative")
    project = facts["project"]
    language = _get_language(locale)
    user = (
        f"Brand/Business Context:\n"
        f"  Brand Name: {project['brand_name']}\n"
        f"  Category: {project['category']}\n"
        f"  URL: {project['url']}\n"
        f"  Data Quality: {reflection.get('data_quality_score', '?')}/100\n\n"
        f"Analysis Findings ({len(distilled.get('insights', []))} total):\n"
        f"{_json_dump(distilled)}"
    )
    try:
        result = await _llm_json_call(_PLAN_SYSTEM.format(language=language), user)
        if not isinstance(result, dict):
            raise ValueError("Planner did not return a dict")
        sections = result.get("sections", [])
        logger.info(
            "[Pipeline Phase 3] Planned %d sections, arc: %s",
            len(sections),
            result.get("narrative_arc", "?")[:80],
        )
        return result
    except Exception as exc:
        logger.warning("[Pipeline Phase 3] Plan failed: %s", exc)
        raise


# ===================================================================
# Phase 4 — Section Writer (per-section authoring)
# ===================================================================

_WRITE_SECTION_SYSTEM = """\
You are a senior business analysis writer. Please write deep content for one section of the report.
You MUST respond in {language}. All your analysis and output should be in {language}.

Writing Requirements:
1. Use the core thesis as the framework, supported by data and insights.
2. Do not just list data; **interpret** it—answer "so what?"
3. Every key claim must have data support, using [Source: Agent Name] for attribution.
4. Use specific numbers; avoid vague terms (don't use "large", "good", etc.).
5. Maintain logical progression between paragraphs, not just flat listing.
6. 3-5 sentences per paragraph.
7. Naturally transition to the theme of the next section at the end.
8. Tone: Professional but not obscure, like a McKinsey industry report.
9. Must include at least one "counter-intuitive finding" or "deep insight".

**Additional Requirements (Optimized version):**
10. If competitor data is involved, you must add comparison tables or clear numerical comparisons.
11. For problem diagnosis, perform root cause analysis (answer "why it's like this"), listing 2-3 possible causes.
12. If historical trend data is available, specify the trend direction and rate of change (e.g., "30% decrease over the past 3 months").
13. Every problem must be linked to business impact (traffic, revenue, market share, etc.).

Output pure Markdown text (no JSON, no code block wrapping).
Start with ## for the section title, followed by body paragraphs."""


async def _phase_write_section(
    outline: dict,
    section: dict,
    insights_map: dict[str, dict],
    completed_summaries: list[str] | None = None,
    locale: str = "en",
) -> str:
    """Phase 4: Write one report section."""
    section_id = section.get("id", "?")
    logger.info("[Pipeline Phase 4] Writing section: %s", section.get("title", section_id))
    language = _get_language(locale)

    relevant_insights = [
        insights_map[iid]
        for iid in section.get("insight_ids", [])
        if iid in insights_map
    ]

    user = (
        f"Report Title: {outline.get('report_title', 'Deep Strategic Analysis Report')}\n"
        f"Report Narrative Arc: {outline.get('narrative_arc', 'None')}\n\n"
        f"== Current Task ==\n"
        f"Title: {section['title']}\n"
        f"Core Thesis: {section.get('thesis', 'None')}\n"
        f"Word Budget: {section.get('word_budget', 600)} words\n"
        f"Writing Guidance: {section.get('writing_guidance', 'Expand on the thesis with arguments')}\n\n"
        f"== Available Insights (Total {len(relevant_insights)}) ==\n"
        f"{_json_dump(relevant_insights)}\n"
    )
    if completed_summaries:
        user += (
            "\n== Summaries of Other Completed Sections ==\n"
            + "\n".join(f"- {s}" for s in completed_summaries)
        )

    return await _llm_text_call(_WRITE_SECTION_SYSTEM.format(language=language), user)


# ===================================================================
# Phase 5 — Section Grader (review loop)
# ===================================================================

_GRADE_SECTION_SYSTEM = """\
You are a strict business report reviewer. Please review the following report section.
You MUST respond in {language}. All your analysis and output should be in {language}.

Grade based on the following dimensions (1-5 points):
1. **Thesis Clarity**: Is the core thesis clear? Is the argument centered around the thesis?
2. **Data Depth**: Is the available data fully utilized? Is there "so what" analysis rather than just listing?
3. **Insight Uniqueness**: Is there deep analysis beyond the surface? Are there counter-intuitive findings?
4. **Logical Coherence**: Is there logical progression between paragraphs? Is the argument chain complete?
5. **Actionability**: Does the analysis point to specific action recommendations?

Return JSON:
{{
  "scores": {{"clarity": 4, "depth": 3, "originality": 3, "coherence": 4, "actionability": 4}},
  "average_score": 3.6,
  "pass": false,
  "revision_instructions": "Specific instructions for improvement...",
  "specific_fixes": ["Specific fix suggestion 1", "Specific fix suggestion 2"]
}}

Set pass to true if average_score >= 3.8.
You must return valid JSON. Do not wrap it in markdown code blocks."""


async def _phase_grade_section(section: dict, content: str, locale: str = "en") -> dict:
    """Phase 5: Grade a written section. Returns scores + pass/fail."""
    section_id = section.get("id", "?")
    logger.info("[Pipeline Phase 5] Grading section: %s", section.get("title", section_id))
    language = _get_language(locale)
    user = (
        f"== Section Requirements ==\n"
        f"Core Thesis: {section.get('thesis', 'None')}\n"
        f"Word Budget: {section.get('word_budget', 600)}\n"
        f"Available Insight IDs: {section.get('insight_ids', [])}\n\n"
        f"== Section Content ==\n{content}"
    )
    try:
        result = await _llm_json_call(_GRADE_SECTION_SYSTEM.format(language=language), user)
        if not isinstance(result, dict):
            raise ValueError("grader did not return a JSON object")
        avg = result.get("average_score")
        if avg is None:
            raise ValueError("grader response missing average_score")
        result["pass"] = avg >= _GRADER_PASS_THRESHOLD
        result["grading_unavailable"] = False
        logger.info(
            "[Pipeline Phase 5] Section %s score: %.1f — %s",
            section_id, avg, "PASS" if result["pass"] else "NEEDS REVISION",
        )
        return result
    except Exception as exc:
        logger.warning("[Pipeline Phase 5] Grading failed for %s: %s", section_id, exc)
        return {
            "average_score": None,
            "pass": False,
            "grading_unavailable": True,
            "revision_instructions": f"Section grading unavailable: {exc}",
            "specific_fixes": [],
        }


_REVISE_SECTION_SYSTEM = """\
You are a senior business analysis writer. The reviewer has provided feedback on your section; please revise the content accordingly.
You MUST respond in {language}. All your analysis and output should be in {language}.

Revision Requirements:
1. Keep the original thesis and structure unchanged.
2. Improve point-by-point based on the reviewer's specific fix suggestions.
3. Strengthen data depth and insight uniqueness.
4. Ensure every claim has data support.

Output the revised pure Markdown text (no JSON, no code block wrapping)."""


async def _phase_revise_section(
    section: dict, original_content: str, grade: dict, locale: str = "en"
) -> str:
    """Revise a section based on grader feedback."""
    logger.info("[Pipeline Phase 5] Revising section: %s", section.get("title", "?"))
    language = _get_language(locale)
    user = (
        f"== Original Section ==\n{original_content}\n\n"
        f"== Reviewer Scores ==\n{_json_dump(grade.get('scores', {}))}\n"
        f"Total Score: {grade.get('average_score', '?')}\n\n"
        f"== Revision Instructions ==\n{grade.get('revision_instructions', 'Improve depth')}\n\n"
        f"== Specific Fix Suggestions ==\n"
        + "\n".join(f"- {fix}" for fix in grade.get("specific_fixes", []))
    )
    return await _llm_text_call(_REVISE_SECTION_SYSTEM.format(language=language), user)


# ===================================================================
# Phase 6 — Report Synthesizer (MULTI-AGENT: summarizers + writers)
# ===================================================================

_SUMMARIZE_SECTION_SYSTEM = """\
You are a report editing assistant. Please generate a concise summary for the following report section.
You MUST respond in {language}. All your analysis and output should be in {language}.

Requirements:
1. Summarize the core content in 3-5 sentences.
2. Retain the most critical data points.
3. Distill the main conclusions.

Output pure text summary (no JSON, no Markdown titles)."""

_WRITE_EXEC_SUMMARY_SYSTEM = """\
You are a report editor for executives. Based on the following section summaries and core findings, write an executive summary.
You MUST respond in {language}. All your analysis and output should be in {language}.

Requirements:
1. 250-350 words.
2. The first sentence must point out the most critical business impact (e.g., acquisition efficiency, brand visibility, market competitive pressure).
3. Quantification is allowed only if explicit numbers have already appeared in the input; if reliable numbers are missing, use qualitative judgment and explain the data gap.
4. Clearly point out 1-3 highest priority actions and suggested time windows, but do not fabricate ROI, traffic loss, or competitor growth rates.
5. Add urgency prompts, but only based on facts and trends already given in the input.
6. Oriented toward CMO decision-makers, making them understand "why action must be taken now" within 30 seconds.

Output pure Markdown (starting with ## Executive Summary)."""

_WRITE_INTRO_SYSTEM = """\
You are a strategic report editor. Based on the following context information, write the report introduction.
You MUST respond in {language}. All your analysis and output should be in {language}.

Requirements:
1. 200-300 words.
2. Do not use nonsense like "This report aims to...".
3. Quickly establish context: brand positioning, market environment, why attention is needed now.
4. Tone should be professional and urgent.

Output pure Markdown (starting with ## Introduction)."""

_WRITE_STRATEGY_SYSTEM = """\
You are a CMO-level strategic consultant. Based on the following section analysis summaries, propose strategic recommendations and an action roadmap.
You MUST respond in {language}. All your analysis and output should be in {language}.

Requirements:
1. 500-800 words, divided into three parts.

**Part 1: Prioritization**
- List 3-5 key action items.
- Sort by P0/P1/P2 and explain the basis for sorting.
- Explain dependencies (e.g., fix foundation issues first, then evaluate expansion actions).

**Part 2: 30-Day Action Roadmap**
- Task breakdown for Weeks 1-4.
- For each week, specify: responsible role, preconditions, acceptance criteria.
- Mark which can be automatically executed by Agents vs. requiring human decision-making.

**Part 3: Risks & Opportunities**
- Point out what risks will be faced if no action is taken.
- Point out the most worthwhile opportunity window to seize currently.
- Quantification is allowed only if explicit numbers already exist in the input; do not fabricate ICE scores, ROI, or future metric changes.

Output pure Markdown (starting with ## Strategic Recommendations & Action Roadmap)."""


async def _summarize_one_section(section: dict, content: str, locale: str = "en") -> str:
    """Summarize one section into 3-5 sentences."""
    language = _get_language(locale)
    user = (
        f"Section Title: {section.get('title', '?')}\n"
        f"Core Thesis: {section.get('thesis', '?')}\n\n"
        f"== Section Content ==\n{content}"
    )
    return await _llm_text_call(_SUMMARIZE_SECTION_SYSTEM.format(language=language), user)


async def _phase_synthesize(
    outline: dict,
    section_contents: list[tuple[dict, str]],
    distilled: dict,
    facts: dict,
    locale: str = "en",
) -> str:
    """Phase 6: Multi-agent synthesis — parallel summarizers, then 3 specialist writers."""
    logger.info("[Pipeline Phase 6] Report Synthesizer — %d sub-agents", len(section_contents) + 3)

    project = facts["project"]
    language = _get_language(locale)

    # Step 1: Parallel per-section summarizers with concurrency limit
    logger.info("[Pipeline Phase 6.1] Summarizing %d sections in parallel", len(section_contents))
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_LLM_CALLS)

    async def _bounded_summarize(sec, content):
        async with semaphore:
            return await _summarize_one_section(sec, content, locale=locale)

    summary_tasks = [_bounded_summarize(sec, content) for sec, content in section_contents]
    summaries = await asyncio.gather(*summary_tasks, return_exceptions=True)

    section_summaries = []
    for i, (sec, _) in enumerate(section_contents):
        if isinstance(summaries[i], Exception):
            raise RuntimeError(f"Section summary failed for {sec.get('title', '?')}: {summaries[i]}") from summaries[i]
        summary = summaries[i]
        section_summaries.append({"title": sec.get("title", "?"), "summary": summary})

    summaries_text = "\n\n".join(
        f"### {s['title']}\n{s['summary']}" for s in section_summaries
    )

    # Context for all synthesis writers (small — just summaries, not full content)
    synthesis_context = (
        f"Brand: {project['brand_name']} ({project['category']})\n"
        f"URL: {project['url']}\n"
        f"Report Title: {outline.get('report_title', 'Deep Analysis Report')}\n"
        f"Narrative Arc: {outline.get('narrative_arc', 'None')}\n\n"
        f"Key Finding Points:\n"
        + "\n".join(f"- {p}" for p in distilled.get("executive_summary_points", []))
        + f"\n\nCross-Cutting Themes: {', '.join(distilled.get('cross_cutting_themes', []))}\n\n"
        f"=== Section Summaries ===\n{summaries_text}"
    )

    # Step 2: Run exec summary + intro + strategy writers in parallel with concurrency limit
    logger.info("[Pipeline Phase 6.2] Running 3 synthesis writers in parallel")

    async def _bounded_synthesis(coro):
        async with semaphore:
            return await coro

    exec_task = _bounded_synthesis(_llm_text_call(_WRITE_EXEC_SUMMARY_SYSTEM.format(language=language), synthesis_context))
    intro_task = _bounded_synthesis(_llm_text_call(_WRITE_INTRO_SYSTEM.format(language=language), synthesis_context))
    strategy_task = _bounded_synthesis(_llm_text_call(_WRITE_STRATEGY_SYSTEM.format(language=language), synthesis_context))

    exec_summary, intro, strategy = await asyncio.gather(
        exec_task, intro_task, strategy_task,
        return_exceptions=True,
    )

    if isinstance(exec_summary, Exception):
        raise RuntimeError(f"Executive summary generation failed: {exec_summary}") from exec_summary
    if isinstance(intro, Exception):
        raise RuntimeError(f"Intro generation failed: {intro}") from intro
    if isinstance(strategy, Exception):
        raise RuntimeError(f"Strategy generation failed: {strategy}") from strategy

    # Step 3: Assemble final report (no LLM needed — just concatenation)
    logger.info("[Pipeline Phase 6.3] Assembling final report")
    report_title = outline.get("report_title", f"{project['brand_name']} Deep Strategic Analysis")
    sections_md = "\n\n".join(content for _, content in section_contents)

    final_report = (
        f"# {report_title}\n\n"
        f"{exec_summary}\n\n"
        f"{intro}\n\n"
        f"{sections_md}\n\n"
        f"{strategy}"
    )

    return final_report


# ===================================================================
# Pipeline orchestrator
# ===================================================================

async def run_deep_report_pipeline(
    facts: dict, meta: dict, previous_exists: bool, *, kind: str, locale: str = "en", on_progress=None
) -> str:
    """Run the 6-phase multi-agent deep report pipeline.

    Args:
        on_progress: Optional callable(dict) for sending progress events.

    Returns the final Markdown report content.
    Raises on unrecoverable errors (caller should fallback).
    """
    logger.info("[Deep Report Pipeline] Starting for kind: %s, locale: %s", kind, locale)
    def _emit(phase: str, status: str, summary: str, detail: str = ""):
        if on_progress:
            on_progress({
                "phase": phase,
                "status": status,
                "summary": summary,
                "detail": detail or summary,
            })

    logger.info(
        "=== Deep Report Pipeline START (%s) for %s ===",
        kind, facts["project"]["brand_name"],
    )

    # ── Phase 1: Reflection (parallel per-dimension) ──
    _emit("reflection", "running", "Phase 1: Running data quality auditors...")
    reflection = await _phase_reflect(facts, meta, locale=locale)
    _emit("reflection", "completed", f"Phase 1 complete: {len(reflection.get('dimensions', {}))} dimensions audited")

    # ── Phase 2: Distill insights (parallel per-dimension) ──
    _emit("distillation", "running", "Phase 2: Distilling strategic insights...")
    distilled = await _phase_distill(facts, meta, reflection, locale=locale)
    insight_count = len(distilled.get("insights", []))
    _emit("distillation", "completed", f"Phase 2 complete: {insight_count} insights extracted")

    # ── Phase 3: Plan outline ──
    _emit("planning", "running", "Phase 3: Planning report structure...")
    outline = await _phase_plan_outline(facts, distilled, reflection, locale=locale)
    sections = outline.get("sections", [])
    _emit("planning", "completed", f"Phase 3 complete: {len(sections)} sections planned")

    # Build insight lookup map
    insights_list = distilled.get("insights", [])
    insights_map: dict[str, dict] = {ins["id"]: ins for ins in insights_list if "id" in ins}

    # Separate main sections from final sections (intro/conclusion)
    main_sections = [s for s in sections if not s.get("is_final_section", False)]

    if not main_sections:
        raise RuntimeError("Outline planner returned no main sections")

    # ── Phase 4 + 5: Write & Grade (with retry loop) ──
    _emit("writing", "running", f"Phase 4-5: Writing {len(main_sections)} sections in parallel...")

    async def _write_and_grade(section: dict) -> tuple[dict, str]:
        """Write a section, grade it, revise if needed."""
        section_title = section.get("title", section.get("id", "?"))
        _emit("writing", "running", f"Writing section: {section_title}")
        content = await _phase_write_section(outline, section, insights_map, locale=locale)

        for attempt in range(_MAX_GRADER_RETRIES + 1):
            grade = await _phase_grade_section(section, content, locale=locale)
            if grade.get("grading_unavailable", False):
                raise RuntimeError(
                    grade.get("revision_instructions", f"Section grading unavailable for {section_title}")
                )
            if grade.get("pass", False):
                _emit("grading", "completed", f"Section passed: {section_title}")
                return section, content
            if attempt < _MAX_GRADER_RETRIES:
                logger.info(
                    "[Pipeline] Section %s failed grading (attempt %d/%d), revising...",
                    section.get("id", "?"), attempt + 1, _MAX_GRADER_RETRIES,
                )
                _emit("grading", "running", f"Revising section: {section_title} (attempt {attempt + 1})")
                content = await _phase_revise_section(section, content, grade, locale=locale)
            else:
                logger.warning(
                    "[Pipeline] Section %s exhausted retries, using last version",
                    section.get("id", "?"),
                )

        return section, content

    # Run all main sections in parallel with concurrency limit
    logger.info("[Pipeline] Writing %d main sections in parallel...", len(main_sections))
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_LLM_CALLS)

    async def _bounded_write_and_grade(section: dict) -> tuple[dict, str]:
        async with semaphore:
            return await _write_and_grade(section)

    section_results = await asyncio.gather(
        *[_bounded_write_and_grade(sec) for sec in main_sections],
        return_exceptions=True,
    )

    # Collect successful sections, skip failures
    completed_sections: list[tuple[dict, str]] = []
    for i, result in enumerate(section_results):
        if isinstance(result, Exception):
            logger.error("[Pipeline] Section %d failed: %s — skipping", i, result)
            _emit("writing", "failed", f"Section {i} failed: {result}")
            continue
        completed_sections.append(result)

    if not completed_sections:
        raise RuntimeError("All section writers failed")

    _emit("writing", "completed", f"Phase 4-5 complete: {len(completed_sections)} sections written and graded")

    # ── Phase 6: Synthesize (parallel summarizers + parallel writers) ──
    _emit("synthesis", "running", "Phase 6: Synthesizing final report...")
    final_report = await _phase_synthesize(outline, completed_sections, distilled, facts, locale=locale)
    _emit("synthesis", "completed", f"Phase 6 complete: {len(final_report)} chars")

    logger.info(
        "=== Deep Report Pipeline COMPLETE — %d chars, %d sections ===",
        len(final_report), len(completed_sections),
    )
    return final_report
