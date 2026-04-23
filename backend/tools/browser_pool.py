"""Shared browser concurrency gate for Crawl4AI-backed work."""

from __future__ import annotations

import asyncio
import os
import weakref
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

_DEFAULT_BROWSER_CONCURRENCY = 1
_SEMAPHORES: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, dict[int, asyncio.Semaphore]]" = (
    weakref.WeakKeyDictionary()
)


def _get_positive_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, value)


def get_browser_concurrency() -> int:
    """Return the global browser concurrency cap for Crawl4AI usage."""
    return _get_positive_int_env("OPENCMO_BROWSER_CONCURRENCY", _DEFAULT_BROWSER_CONCURRENCY)


def _get_browser_semaphore() -> asyncio.Semaphore:
    loop = asyncio.get_running_loop()
    limit = get_browser_concurrency()
    semaphores = _SEMAPHORES.setdefault(loop, {})
    semaphore = semaphores.get(limit)
    if semaphore is None:
        semaphore = asyncio.Semaphore(limit)
        semaphores[limit] = semaphore
    return semaphore


@asynccontextmanager
async def browser_slot() -> AsyncIterator[None]:
    """Serialize or bound Crawl4AI browser launches across the process."""
    async with _get_browser_semaphore():
        yield
