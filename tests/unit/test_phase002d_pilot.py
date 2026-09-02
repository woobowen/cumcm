import pytest

from cumcm_skill_lab.expansion.pilot import (
    _classify_failure,
    transport_fallback_allowed,
)


@pytest.mark.parametrize(
    ("stderr", "expected"),
    [
        ("TLS handshake timed out", "TLS_HANDSHAKE_TIMEOUT"),
        ("Responses connection reset", "RESPONSES_CONNECT_RESET"),
        ("WebSocket closed unexpectedly", "WEBSOCKET_RESET"),
        ("HTTPS fallback disconnected", "HTTPS_FALLBACK_DISCONNECT"),
        ("invalid_json_schema for response_format", "RUNNER_SCHEMA_REJECTED"),
        ("authentication required", "AUTH_BLOCKED"),
        ("usage limit reached", "QUOTA_BLOCKED"),
        ("model unavailable", "MODEL_UNAVAILABLE"),
    ],
)
def test_pilot_failure_classification(stderr: str, expected: str):
    assert _classify_failure(exit_code=1, stderr=stderr, stdout="", timed_out=False) == expected


@pytest.mark.parametrize(
    "failure",
    [
        "TLS_HANDSHAKE_TIMEOUT",
        "RESPONSES_CONNECT_RESET",
        "WEBSOCKET_RESET",
        "HTTPS_FALLBACK_DISCONNECT",
    ],
)
def test_only_explicit_transport_failures_allow_process_local_fallback(failure: str):
    assert transport_fallback_allowed(failure)


@pytest.mark.parametrize(
    "failure",
    ["AUTH_BLOCKED", "QUOTA_BLOCKED", "MODEL_UNAVAILABLE", "SCHEMA_INVALID", None],
)
def test_non_transport_failures_do_not_allow_profile_switch(failure: str | None):
    assert not transport_fallback_allowed(failure)


def test_every_pilot_output_property_has_explicit_type():
    from cumcm_skill_lab.expansion.pilot import OUTPUT_SCHEMA

    assert all("type" in value for value in OUTPUT_SCHEMA["properties"].values())
