"""Tests for LiteLLM request metadata attribution."""

from types import SimpleNamespace

from agent.litellm_metadata import build_litellm_request_metadata


def _agent(**kwargs):
    values = {
        "base_url": "https://litellm.example.com/v1",
        "platform": "slack",
        "session_id": "sess-123",
        "provider": "custom",
        "_parent_session_id": None,
        "_gateway_session_key": "agent:main:slack:C123:T456",
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_litellm_metadata_tags_interactive_source(monkeypatch):
    monkeypatch.delenv("HERMES_CRON_SESSION", raising=False)

    metadata = build_litellm_request_metadata(_agent(), caller="main")

    assert metadata is not None
    assert metadata["hermes_app"] == "hermes-agent"
    assert metadata["hermes_source"] == "slack"
    assert metadata["hermes_source_tag"] == "interactive:slack"
    assert metadata["hermes_caller"] == "main"
    assert metadata["hermes_session_hash"]
    assert metadata["hermes_session_hash"] != "sess-123"
    assert metadata["hermes_provider"] == "custom"
    assert "hermes_gateway_session_key" not in metadata


def test_litellm_metadata_tags_cron_job(monkeypatch):
    monkeypatch.setenv("HERMES_CRON_SESSION", "1")
    monkeypatch.setenv("HERMES_CRON_JOB_ID", "abc123")
    monkeypatch.setenv("HERMES_CRON_JOB_NAME", "Daily report")

    metadata = build_litellm_request_metadata(_agent(platform=""), caller="main")

    assert metadata is not None
    assert metadata["hermes_source"] == "cron"
    assert metadata["hermes_source_tag"].startswith("cron:")
    assert metadata["hermes_source_tag"] != "cron:abc123"
    assert metadata["hermes_cron_job_hash"]
    assert "hermes_cron_job_id" not in metadata
    assert "hermes_cron_job_name" not in metadata


def test_litellm_metadata_marks_delegate(monkeypatch):
    monkeypatch.delenv("HERMES_CRON_SESSION", raising=False)

    metadata = build_litellm_request_metadata(
        _agent(platform="slack", _parent_session_id="parent-1"), caller="main"
    )

    assert metadata is not None
    assert metadata["hermes_source_tag"] == "delegate:slack"
    assert metadata["hermes_parent_session_hash"]
    assert metadata["hermes_parent_session_hash"] != "parent-1"


def test_litellm_metadata_skips_non_litellm_proxy(monkeypatch):
    monkeypatch.delenv("HERMES_LITELLM_METADATA", raising=False)

    metadata = build_litellm_request_metadata(
        _agent(base_url="https://api.openai.com/v1")
    )

    assert metadata is None


def test_litellm_metadata_does_not_emit_raw_context_identifiers(monkeypatch):
    monkeypatch.setenv("HERMES_CRON_SESSION", "1")
    monkeypatch.setenv("HERMES_CRON_JOB_ID", "private-job-id")
    monkeypatch.setenv("HERMES_CRON_JOB_NAME", "Customer revenue report")

    metadata = build_litellm_request_metadata(
        _agent(
            session_id="session-secret",
            _parent_session_id="parent-secret",
            _gateway_session_key="agent:main:slack:CSECRET:TSECRET",
        ),
        caller="main",
    )

    assert metadata is not None
    serialized_values = " ".join(metadata.values())
    assert "session-secret" not in serialized_values
    assert "parent-secret" not in serialized_values
    assert "CSECRET" not in serialized_values
    assert "TSECRET" not in serialized_values
    assert "private-job-id" not in serialized_values
    assert "Customer revenue report" not in serialized_values
