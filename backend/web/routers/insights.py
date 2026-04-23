"""Insights API router."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import llm, storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

_LANG_NAMES: dict[str, str] = {
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
}


async def _translate_insights(items: list[dict], lang: str) -> list[dict]:
    """Translate insight title and summary to the requested language via LLM.

    Falls back silently to the original English content on any error.
    """
    if not items or lang not in _LANG_NAMES:
        return items
    lang_name = _LANG_NAMES[lang]
    payload = [{"id": r["id"], "title": r["title"], "summary": r["summary"]} for r in items]
    system = "You are a precise translator. Output only valid JSON array, no markdown, no explanation."
    user = (
        f"Translate these marketing insight titles and summaries to {lang_name}.\n"
        f"Return the exact same JSON array structure with translated 'title' and 'summary' fields.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        raw = await llm.chat_completion(system, user, temperature=0.3)
        translated: list = json.loads(raw)
        mapping = {str(r["id"]): r for r in translated if isinstance(r, dict) and "id" in r}
        return [
            {
                **row,
                "title": mapping.get(str(row["id"]), {}).get("title", row["title"]),
                "summary": mapping.get(str(row["id"]), {}).get("summary", row["summary"]),
            }
            for row in items
        ]
    except Exception:
        logger.debug("Insight translation failed for lang=%s, returning original", lang)
        return items


@router.get("/insights")
async def api_v1_insights(request: Request):
    project_id = request.query_params.get("project_id")
    unread = request.query_params.get("unread", "").lower() in ("true", "1")
    lang = request.query_params.get("lang", "en")
    pid = int(project_id) if project_id else None
    insights = await storage.list_insights(project_id=pid, unread_only=unread)
    insights = await _translate_insights(insights, lang)
    return JSONResponse(insights)


@router.get("/insights/summary")
async def api_v1_insights_summary(request: Request):
    project_id = request.query_params.get("project_id")
    lang = request.query_params.get("lang", "en")
    pid = int(project_id) if project_id else None
    summary = await storage.get_insights_summary(project_id=pid)
    summary["recent"] = await _translate_insights(summary["recent"], lang)
    return JSONResponse(summary)


@router.post("/insights/{insight_id}/read")
async def api_v1_insight_read(insight_id: int):
    ok = await storage.mark_insight_read(insight_id)
    if not ok:
        return JSONResponse({"error": "Not found or already read"}, status_code=404)
    return JSONResponse({"ok": True})
