"""Pull BWG SQLite DB locally, rerun with bounded concurrency + retries, then push back.

This is an operational helper for refreshing production project data locally
against a chosen LLM gateway before writing the updated SQLite database back to
the server.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")

REMOTE_HOST = "root@97.64.16.217"
REMOTE_PORT = "2222"
REMOTE_DB_PATH = "/root/.opencmo/data.db"
REMOTE_APP_PATH = "/opt/OpenCMO"


def _run(cmd: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def _ssh(command: str, *, capture_output: bool = False) -> subprocess.CompletedProcess:
    return _run(
        ["ssh", "-p", REMOTE_PORT, REMOTE_HOST, command],
        capture_output=capture_output,
    )


def _scp_from_remote(remote_path: str, local_path: Path) -> None:
    _run(["scp", "-P", REMOTE_PORT, f"{REMOTE_HOST}:{remote_path}", str(local_path)])


def _scp_to_remote(local_path: Path, remote_path: str) -> None:
    _run(["scp", "-P", REMOTE_PORT, str(local_path), f"{REMOTE_HOST}:{remote_path}"])


def create_remote_backup_copy(snapshot_name: str) -> str:
    backup_path = f"/root/.opencmo/{snapshot_name}.db"
    _ssh(f"sqlite3 {REMOTE_DB_PATH} '.backup {backup_path}'")
    return backup_path


@dataclass
class RetryPolicy:
    attempts: int = 4
    base_delay_seconds: float = 3.0
    max_delay_seconds: float = 1800.0
    jitter_seconds: float = 0.75


def _extract_provider_delay_seconds(exc: Exception) -> float | None:
    text = str(exc)
    patterns = [
        r"reset_seconds['\"]?\s*:\s*(\d+)",
        r"Retry-After['\"]?\s*:\s*(\d+)",
        r"retry after['\"]?\s*:\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


async def retry_async(
    label: str,
    fn: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, policy.attempts + 1):
        try:
            return await fn()
        except Exception as exc:  # noqa: BLE001 - operational retry wrapper
            last_error = exc
            if attempt >= policy.attempts:
                raise
            provider_delay = _extract_provider_delay_seconds(exc)
            if provider_delay is not None:
                delay = min(provider_delay, policy.max_delay_seconds)
            else:
                delay = min(policy.base_delay_seconds * (2 ** (attempt - 1)), policy.max_delay_seconds)
            delay += random.uniform(0, policy.jitter_seconds)
            print(f"[retry] {label} failed on attempt {attempt}/{policy.attempts}: {exc}; sleeping {delay:.1f}s", flush=True)
            await asyncio.sleep(delay)
    assert last_error is not None
    raise last_error


async def _set_local_defaults(api_key: str, base_url: str, model: str) -> None:
    from opencmo import storage

    await storage.ensure_db()
    await storage.set_setting("OPENAI_API_KEY", api_key)
    await storage.set_setting("OPENAI_BASE_URL", base_url)
    await storage.set_setting("OPENCMO_MODEL_DEFAULT", model)


async def _run_local_reprocess(*, scan_concurrency: int, report_concurrency: int, retry_policy: RetryPolicy) -> None:
    from opencmo import service, storage
    from opencmo.scheduler import run_scheduled_scan

    await storage.ensure_db()
    projects = await storage.list_projects()

    print(f"[info] local projects={len(projects)}", flush=True)

    scan_sem = asyncio.Semaphore(max(1, scan_concurrency))
    report_sem = asyncio.Semaphore(max(1, report_concurrency))

    async def rerun_project_scan(project: dict) -> None:
        async with scan_sem:
            label = f"scan:{project['id']}:{project['brand_name']}"

            async def _call():
                await run_scheduled_scan(project["id"], "full", triggered_by="manual")
                return {"ok": True}

            result = await retry_async(label, _call, policy=retry_policy)
            print(f"[scan] {label} -> {result.get('ok')}", flush=True)

    async def rerun_report(project: dict, kind: str) -> None:
        async with report_sem:
            label = f"report:{project['id']}:{project['brand_name']}:{kind}"

            async def _call():
                result = await service.regenerate_project_report(project["id"], kind)
                status = result.get("human", {}).get("generation_status")
                if status != "completed":
                    meta = result.get("human", {}).get("meta", {})
                    raise RuntimeError(
                        f"status={status}; llm_error={meta.get('llm_error')}; pipeline_error={meta.get('pipeline_error')}"
                    )
                return result

            result = await retry_async(label, _call, policy=retry_policy)
            status = result.get("human", {}).get("generation_status")
            print(f"[report] {label} -> {status}", flush=True)

    await asyncio.gather(*(rerun_project_scan(project) for project in projects))

    async def rerun_project_reports(project: dict) -> None:
        await rerun_report(project, "strategic")
        await rerun_report(project, "periodic")

    await asyncio.gather(*(rerun_project_reports(project) for project in projects))


def _replace_local_db(db_path: Path, temp_db: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(temp_db, db_path)


def _push_remote_db(local_db: Path, remote_backup_tag: str) -> None:
    _ssh(f"systemctl stop opencmo && sqlite3 {REMOTE_DB_PATH} '.backup /root/.opencmo/{remote_backup_tag}-preupload.db'")
    _scp_to_remote(local_db, REMOTE_DB_PATH)
    _ssh("systemctl start opencmo && systemctl is-active opencmo")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--scan-concurrency", type=int, default=1)
    parser.add_argument("--report-concurrency", type=int, default=1)
    parser.add_argument("--attempts", type=int, default=4)
    parser.add_argument("--base-delay", type=float, default=3.0)
    parser.add_argument("--max-delay", type=float, default=30.0)
    parser.add_argument("--dry-run-upload", action="store_true")
    return parser.parse_args(argv)


async def _async_main(args: argparse.Namespace) -> int:
    from opencmo.storage import _db as _db_module

    snapshot_tag = f"data-{os.getpid()}"
    remote_snapshot = create_remote_backup_copy(snapshot_tag)
    print(f"[info] remote snapshot created at {remote_snapshot}", flush=True)

    with tempfile.TemporaryDirectory(prefix="opencmo-bwg-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        local_snapshot = tmp_path / "remote.db"
        _scp_from_remote(remote_snapshot, local_snapshot)
        print(f"[info] remote snapshot copied to {local_snapshot}", flush=True)

        original_db_path = _db_module._DB_PATH
        _db_module._DB_PATH = tmp_path / "work.db"
        _db_module._SCHEMA_READY_FOR = None
        _replace_local_db(_db_module._DB_PATH, local_snapshot)
        try:
            await _set_local_defaults(args.api_key, args.base_url, args.model)
            await _run_local_reprocess(
                scan_concurrency=args.scan_concurrency,
                report_concurrency=args.report_concurrency,
                retry_policy=RetryPolicy(
                    attempts=args.attempts,
                    base_delay_seconds=args.base_delay,
                    max_delay_seconds=args.max_delay,
                ),
            )
            if args.dry_run_upload:
                print(f"[info] dry-run enabled; updated DB left at {_db_module._DB_PATH}", flush=True)
            else:
                _push_remote_db(_db_module._DB_PATH, snapshot_tag)
                print("[info] updated DB uploaded and remote service restarted", flush=True)
        finally:
            _db_module._DB_PATH = original_db_path
            _db_module._SCHEMA_READY_FOR = None
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    return asyncio.run(_async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
