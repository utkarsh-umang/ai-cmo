"""Executor for report generation tasks."""

from __future__ import annotations

import asyncio

from opencmo import service


def _is_usable_report(record: dict | None) -> bool:
    if not record:
        return False
    return record.get("generation_status") == "completed" and bool((record.get("content") or "").strip())


def _report_failure_message(record: dict | None) -> str:
    if not record:
        return "Human report was not generated."
    meta = record.get("meta") or {}
    for key in ("llm_error", "pipeline_error"):
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return "Human report generation failed."


async def run_report_executor(ctx) -> None:
    task = ctx.task
    payload = task["payload"]
    event_tasks: list[asyncio.Task] = []

    # Restore BYOK keys saved at enqueue time so the worker can call the LLM.
    from opencmo import llm
    user_keys: dict = payload.get("__user_keys") or {}
    llm_token = llm.set_request_keys(user_keys) if user_keys else None

    def on_progress(event: dict) -> None:
        event_tasks.append(
            asyncio.create_task(
                ctx.emit(
                    event_type="progress",
                    phase=event.get("phase", ""),
                    status=event.get("status", ""),
                    summary=event.get("summary", ""),
                    payload=event,
                )
            )
        )

    try:
        result = await service.regenerate_project_report(
            payload["project_id"],
            payload["kind"],
            source_run_id=payload.get("source_run_id"),
            on_progress=on_progress,
        )
        human_report = result.get("human")
        if not _is_usable_report(human_report):
            raise RuntimeError(_report_failure_message(human_report))
    finally:
        if event_tasks:
            await asyncio.gather(*event_tasks, return_exceptions=True)
        if llm_token is not None:
            llm.reset_request_keys(llm_token)

    await ctx.complete(
        {
            "kind": payload["kind"],
            "summary": f"{payload['kind'].title()} report completed",
            "human_report_id": result.get("human", {}).get("id"),
            "human_version": result.get("human", {}).get("version"),
            "agent_report_id": result.get("agent", {}).get("id"),
            "agent_version": result.get("agent", {}).get("version"),
        }
    )
