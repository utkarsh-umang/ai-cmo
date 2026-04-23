from __future__ import annotations

from unittest.mock import patch

from opencmo.config import configure_agent_tracing


def test_configure_agent_tracing_disables_for_custom_provider():
    with patch("opencmo.config.is_custom_provider", return_value=True), patch(
        "agents.set_tracing_disabled"
    ) as mock_disable:
        assert configure_agent_tracing() is True
        mock_disable.assert_called_once_with(True)


def test_configure_agent_tracing_keeps_openai_tracing_enabled():
    with patch("opencmo.config.is_custom_provider", return_value=False), patch(
        "agents.set_tracing_disabled"
    ) as mock_disable:
        assert configure_agent_tracing() is False
        mock_disable.assert_called_once_with(False)
