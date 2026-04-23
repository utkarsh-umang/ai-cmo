from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from opencmo.ops.reprocess_remote_db import RetryPolicy, _extract_provider_delay_seconds, retry_async


def test_extract_provider_delay_seconds_reads_reset_seconds():
    exc = RuntimeError("Error code: 429 - {'error': {'reset_seconds': 14945}}")
    assert _extract_provider_delay_seconds(exc) == 14945


@pytest.mark.asyncio
async def test_retry_async_uses_exponential_backoff_without_provider_hint():
    attempts = {"count": 0}

    async def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("plain failure")
        return "ok"

    sleep_mock = AsyncMock()
    with patch("asyncio.sleep", sleep_mock):
        result = await retry_async(
            "plain",
            flaky,
            policy=RetryPolicy(attempts=3, base_delay_seconds=2, max_delay_seconds=30, jitter_seconds=0),
        )

    assert result == "ok"
    sleep_mock.assert_any_await(2)
    sleep_mock.assert_any_await(4)
