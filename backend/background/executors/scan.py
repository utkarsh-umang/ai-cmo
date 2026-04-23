"""Executor for monitor scan tasks."""

from __future__ import annotations

import asyncio

from opencmo.monitoring import run_monitoring_workflow


async def run_scan_executor(ctx) -> None:
    task = ctx.task
    payload = task["payload"]
    event_tasks: list[asyncio.Task] = []

    def on_progress(event: dict) -> None:
        event_tasks.append(
            asyncio.create_task(
                ctx.emit(
                    event_type="progress",
                    phase=event.get("stage", ""),
                    status=event.get("status", ""),
                    summary=event.get("summary") or event.get("detail") or event.get("content", ""),
                    payload=event,
                )
            )
        )

    try:
        result = await run_monitoring_workflow(
            task["task_id"],
            payload["project_id"],
            payload["monitor_id"],
            payload["job_type"],
            payload["job_id"],
            analyze_url=payload.get("analyze_url"),
            locale=payload.get("locale", "en"),
            on_progress=on_progress,
        )
    finally:
        if event_tasks:
            await asyncio.gather(*event_tasks, return_exceptions=True)

    await ctx.complete(
        {
            "run_id": result["run_id"],
            "summary": result["summary"],
            "findings_count": len(result.get("findings", [])),
            "recommendations_count": len(result.get("recommendations", [])),
        }
    )
