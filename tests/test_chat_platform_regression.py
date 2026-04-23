from __future__ import annotations

import json

from opencmo.ops.chat_platform_regression import DEFAULT_CASES, PlatformCase, _iter_sse_payloads, run_case, select_cases


def test_select_cases_returns_all_by_default():
    cases = select_cases(None)
    assert cases == list(DEFAULT_CASES)


def test_select_cases_filters_case_insensitively():
    cases = select_cases(["twitter", "InfoQ"])
    assert [case.platform for case in cases] == ["Twitter", "InfoQ"]


def test_iter_sse_payloads_parses_data_lines_and_stops_on_done():
    class FakeResponse:
        def iter_lines(self, decode_unicode=True):
            assert decode_unicode is True
            yield "data: " + json.dumps({"type": "agent", "name": "Twitter Expert"})
            yield ""
            yield "data: " + json.dumps({"type": "done", "final_output": "ok"})
            yield "data: " + json.dumps({"type": "delta", "content": "ignored"})

    events = list(_iter_sse_payloads(FakeResponse()))
    assert events == [
        {"type": "agent", "name": "Twitter Expert"},
        {"type": "done", "final_output": "ok"},
        {"type": "delta", "content": "ignored"},
    ]


def test_run_case_returns_error_when_session_creation_fails():
    class FailingSession:
        def post(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    result = run_case(
        FailingSession(),
        base_url="https://example.com/api/v1",
        project_id=36,
        locale="zh",
        case=PlatformCase("Twitter", "write", "Twitter Expert"),
        connect_timeout=5,
        read_timeout=5,
    )

    assert result["platform"] == "Twitter"
    assert result["done"] is False
    assert result["error"].startswith("session_create_failed:")
