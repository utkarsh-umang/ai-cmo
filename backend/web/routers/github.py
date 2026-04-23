"""GitHub leads API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/projects/{project_id}/github-leads")
async def api_v1_github_leads(
    project_id: int,
    status: str | None = None,
    min_score: float | None = None,
    has_email: bool | None = None,
    has_twitter: bool | None = None,
    language: str | None = None,
    location: str | None = None,
    enriched: bool | None = None,
    limit: int = 100,
    offset: int = 0,
):
    leads = await storage.list_github_leads(
        project_id,
        status=status,
        min_score=min_score,
        has_email=has_email,
        has_twitter=has_twitter,
        language=language,
        location=location,
        enriched=enriched,
        limit=limit,
        offset=offset,
    )
    total = await storage.count_github_leads(project_id)
    return JSONResponse({"leads": leads, "total": total})


@router.get("/projects/{project_id}/github-leads/stats")
async def api_v1_github_lead_stats(project_id: int):
    stats = await storage.get_github_lead_stats(project_id)
    return JSONResponse(stats)


@router.post("/projects/{project_id}/github-discover")
async def api_v1_github_discover(project_id: int, request: Request):
    body = await request.json()
    seed_username = body.get("seed_username", "").strip()
    source = body.get("source", "both")
    max_hops = body.get("max_hops", 1)

    if not seed_username:
        return JSONResponse({"error": "seed_username is required"}, status_code=400)

    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)

    from opencmo.background import service as bg_service

    task = await bg_service.enqueue_task(
        kind="github_enrich",
        project_id=project_id,
        payload={
            "project_id": project_id,
            "seed_username": seed_username,
            "source": source,
            "max_hops": max_hops,
        },
        dedupe_key=f"github_enrich:{project_id}:{seed_username}",
        priority=40,
    )
    run = await storage.create_discovery_run(
        project_id, task["task_id"], seed_username, source, max_hops,
    )
    return JSONResponse({"task_id": task["task_id"], "run": run}, status_code=202)


@router.get("/projects/{project_id}/github-discovery-runs")
async def api_v1_github_runs(project_id: int):
    runs = await storage.list_discovery_runs(project_id)
    return JSONResponse(runs)


@router.patch("/projects/{project_id}/github-leads/{login}/status")
async def api_v1_update_lead_status(project_id: int, login: str, request: Request):
    body = await request.json()
    ok = await storage.update_lead_outreach(
        project_id,
        login,
        status=body.get("status", "not_contacted"),
        channel=body.get("channel", ""),
        note=body.get("note", ""),
    )
    if not ok:
        return JSONResponse({"error": "Lead not found"}, status_code=404)
    return JSONResponse({"ok": True})


@router.post("/projects/{project_id}/github-leads/generate-outreach")
async def api_v1_generate_outreach(project_id: int, request: Request):
    body = await request.json()
    logins = body.get("logins", [])
    channel = body.get("channel", "email")

    if not logins:
        return JSONResponse({"error": "No logins provided"}, status_code=400)

    from opencmo.services.github_service import generate_outreach_batch

    result = await generate_outreach_batch(project_id, logins, channel)
    status_code = 200 if result.get("ok") else 400
    return JSONResponse(result, status_code=status_code)


@router.post("/projects/{project_id}/github-leads/score")
async def api_v1_score_leads(project_id: int):
    from opencmo.services.github_service import compute_outreach_score, has_contact_info

    project = await storage.get_project(project_id)
    category = project.get("category", "") if project else ""

    from opencmo.storage.serp import list_tracked_keywords
    kw_rows = await list_tracked_keywords(project_id)
    keywords = [r["keyword"] for r in kw_rows] if kw_rows else []

    leads = await storage.list_github_leads(project_id, enriched=True, limit=2000)
    for lead in leads:
        if not has_contact_info(lead):
            await storage.update_lead_score(project_id, lead["login"], 0)
            continue
        score = compute_outreach_score(lead, category=category, keywords=keywords)
        await storage.update_lead_score(project_id, lead["login"], score)
    stats = await storage.get_github_lead_stats(project_id)
    return JSONResponse({"scored": len(leads), "stats": stats})


@router.delete("/projects/{project_id}/github-leads")
async def api_v1_delete_leads(project_id: int):
    deleted = await storage.delete_github_leads(project_id)
    return JSONResponse({"ok": True, "deleted": deleted})
