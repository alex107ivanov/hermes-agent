"""Regression tests for the actionable gateway inactivity warning."""

from gateway.run import format_inactivity_warning


def test_inactivity_warning_identifies_the_stalled_run_and_last_work():
    warning = format_inactivity_warning(
        warning_seconds=900,
        timeout_seconds=1800,
        session_key="discord:channel:thread",
        activity={
            "last_activity_ts": 1_700_000_000.0,
            "last_activity_desc": "waiting for provider response",
            "current_tool": None,
            "api_call_count": 7,
            "max_iterations": 90,
        },
        model="custom/_escalation",
        context_tokens=86_432,
    )

    assert "No activity for 15 min" in warning
    assert "Session: discord:channel:thread" in warning
    assert "Waiting on model/API" in warning
    assert "custom/_escalation" in warning
    assert "~86,432 tokens" in warning
    assert "waiting for provider response" in warning
    assert "iteration 7/90" in warning


def test_inactivity_warning_marks_a_tool_wait_without_context_estimate():
    warning = format_inactivity_warning(
        warning_seconds=60,
        timeout_seconds=120,
        session_key="telegram:chat",
        activity={
            "last_activity_ts": 1_700_000_000.0,
            "last_activity_desc": "tool call started",
            "current_tool": "terminal",
            "api_call_count": 3,
            "max_iterations": 20,
        },
        model="test/model",
        context_tokens=None,
    )

    assert "Waiting on tool: terminal" in warning
    assert "context estimate unavailable" in warning
    assert "tool call started" in warning
