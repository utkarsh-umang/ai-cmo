"""Campaigns API router."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/projects/{project_id}/campaigns")
async def api_v1_campaigns(project_id: int):
    """List campaign runs for a project."""
    return JSONResponse(await storage.list_campaign_runs(project_id))


@router.get("/campaigns/{run_id}")
async def api_v1_campaign_detail(run_id: int):
    """Get a campaign run with all its artifacts."""
    run = await storage.get_campaign_run(run_id)
    if not run:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(run)
