from __future__ import annotations

import pytest

from opencmo.background import service as bg_service


@pytest.mark.asyncio
async def test_enqueue_returns_existing_active_task_for_same_dedupe_key(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    await storage.ensure_db()
    project_id = await storage.ensure_project("Planner", "https://planner.test", "saas")

    first = await bg_service.enqueue_task(
        kind="report",
        project_id=project_id,
        payload={"report_kind": "periodic"},
        dedupe_key=f"report:project:{project_id}:periodic",
    )
    second = await bg_service.enqueue_task(
        kind="report",
        project_id=project_id,
        payload={"report_kind": "periodic"},
        dedupe_key=f"report:project:{project_id}:periodic",
    )

    assert second["task_id"] == first["task_id"]
    assert second["status"] == "queued"


@pytest.mark.asyncio
async def test_request_cancel_marks_active_task(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    await storage.ensure_db()
    project_id = await storage.ensure_project("Graphy", "https://graphy.test", "saas")

    task = await bg_service.enqueue_task(
        kind="graph_expansion",
        project_id=project_id,
        payload={"project_id": project_id, "resume": True},
        dedupe_key=f"graph:project:{project_id}",
    )
    ok = await bg_service.request_cancel(task["task_id"])
    updated = await bg_service.get_task(task["task_id"])

    assert ok is True
    assert updated["status"] == "cancel_requested"
