from __future__ import annotations

import asyncio

import pytest


def test_get_browser_concurrency_defaults_to_one(monkeypatch):
    from opencmo.tools.browser_pool import get_browser_concurrency

    monkeypatch.delenv("OPENCMO_BROWSER_CONCURRENCY", raising=False)
    assert get_browser_concurrency() == 1


@pytest.mark.asyncio
async def test_browser_slot_respects_configured_limit(monkeypatch):
    from opencmo.tools.browser_pool import browser_slot

    monkeypatch.setenv("OPENCMO_BROWSER_CONCURRENCY", "1")

    current = 0
    peak = 0
    lock = asyncio.Lock()

    async def _job():
        nonlocal current, peak
        async with browser_slot():
            async with lock:
                current += 1
                peak = max(peak, current)
            await asyncio.sleep(0.05)
            async with lock:
                current -= 1

    await asyncio.gather(*(_job() for _ in range(3)))

    assert peak == 1
