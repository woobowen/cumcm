"""Specific, observable failure classes for formal Codex transports."""

from __future__ import annotations

from dataclasses import dataclass

FAILURE_CLASSES = (
    "AUTH_BLOCKED",
    "QUOTA_BLOCKED",
    "RESPONSES_CONNECT_RESET",
    "RESPONSES_STREAM_TIMEOUT",
    "APP_SERVER_DISCONNECTED",
    "SESSION_ID_MISSING",
    "SESSION_RESUME_FAILED",
    "MODEL_UNAVAILABLE",
    "MODEL_COMPARABILITY_BROKEN",
    "SCHEMA_INVALID",
    "OUTPUT_MISSING",
    "EVIDENCE_HASH_MISMATCH",
    "POLICY_HASH_MISMATCH",
    "IDENTITY_LEAK",
    "SANDBOX_POLICY_VIOLATION",
    "NETWORK_POLICY_VIOLATION",
    "MCP_POLICY_VIOLATION",
    "UNKNOWN_TRANSPORT_FAILURE",
)


@dataclass(frozen=True)
class FailureInfo:
    failure_class: str
    observable_code: str
    resumable: bool
    terminal: bool
    user_action_required: bool
    next_adapter: str | None


def classify_failure(
    observable: str,
    *,
    session_id: str | None = None,
    adapter: str = "EXEC_RESUMABLE",
    resume: bool = False,
) -> FailureInfo:
    text = observable.lower()
    if any(term in text for term in ("not logged in", "authentication", "unauthorized", "login")):
        return _info("AUTH_BLOCKED", "AUTH_REQUIRED", False, True, True, None)
    if any(
        term in text
        for term in ("quota", "usage limit", "insufficient_quota", "rate limit exceeded")
    ):
        return _info("QUOTA_BLOCKED", "QUOTA_OR_USAGE_LIMIT", False, True, True, None)
    if "model" in text and any(
        term in text for term in ("not available", "unavailable", "not found", "unsupported")
    ):
        return _info("MODEL_UNAVAILABLE", "MODEL_NOT_AVAILABLE", False, True, False, None)
    if "model_comparability_broken" in text or "model mismatch" in text:
        return _info("MODEL_COMPARABILITY_BROKEN", "MODEL_MISMATCH", False, True, False, None)
    if "evidence_hash_mismatch" in text:
        return _info("EVIDENCE_HASH_MISMATCH", "EVIDENCE_HASH_MISMATCH", False, True, False, None)
    if "policy_hash_mismatch" in text:
        return _info("POLICY_HASH_MISMATCH", "POLICY_HASH_MISMATCH", False, True, False, None)
    if "identity_leak" in text or "identity_leaked" in text:
        return _info("IDENTITY_LEAK", "IDENTITY_LEAK", False, True, False, None)
    if "sandbox_policy_violation" in text:
        return _info(
            "SANDBOX_POLICY_VIOLATION", "SANDBOX_POLICY_VIOLATION", False, True, False, None
        )
    if "network_policy_violation" in text:
        return _info(
            "NETWORK_POLICY_VIOLATION", "NETWORK_POLICY_VIOLATION", False, True, False, None
        )
    if "mcp_policy_violation" in text:
        return _info("MCP_POLICY_VIOLATION", "MCP_POLICY_VIOLATION", False, True, False, None)
    if "schema" in text and any(term in text for term in ("invalid", "failed", "validation")):
        return _info("SCHEMA_INVALID", "SCHEMA_VALIDATION_FAILED", False, True, False, None)
    if "output_missing" in text or "last message" in text and "missing" in text:
        return _info("OUTPUT_MISSING", "OUTPUT_FILE_MISSING", False, True, False, None)
    if resume and any(term in text for term in ("resume failed", "session not found")):
        return _info(
            "SESSION_RESUME_FAILED", "EXACT_SESSION_RESUME_FAILED", False, True, False, None
        )
    if adapter == "APP_SERVER_RESUMABLE" and any(
        term in text
        for term in ("broken pipe", "app server", "app_server", "process exited", "eof")
    ):
        return _info(
            "APP_SERVER_DISCONNECTED", "APP_SERVER_PROCESS_DISCONNECTED", True, False, False, None
        )
    if any(
        term in text
        for term in (
            "connection reset",
            "connection closed",
            "stream disconnected",
            "websocket",
            "responses transport",
        )
    ):
        return _transport_info("RESPONSES_CONNECT_RESET", "RESPONSES_CONNECTION_RESET", session_id)
    if any(term in text for term in ("timed out", "timeout", "deadline exceeded")):
        return _transport_info("RESPONSES_STREAM_TIMEOUT", "RESPONSES_STREAM_TIMEOUT", session_id)
    if session_id is None:
        return _info(
            "SESSION_ID_MISSING",
            "NO_EXACT_SESSION_BEFORE_FAILURE",
            False,
            False,
            False,
            "APP_SERVER_RESUMABLE" if adapter == "EXEC_RESUMABLE" else None,
        )
    return _info(
        "UNKNOWN_TRANSPORT_FAILURE",
        "UNCLASSIFIED_TRANSPORT_ERROR",
        True,
        False,
        False,
        None,
    )


def _transport_info(failure_class: str, code: str, session_id: str | None) -> FailureInfo:
    if session_id:
        return _info(failure_class, code, True, False, False, None)
    return _info(
        "SESSION_ID_MISSING",
        f"{code}_WITHOUT_SESSION",
        False,
        False,
        False,
        "APP_SERVER_RESUMABLE",
    )


def _info(
    failure_class: str,
    observable_code: str,
    resumable: bool,
    terminal: bool,
    user_action_required: bool,
    next_adapter: str | None,
) -> FailureInfo:
    if failure_class not in FAILURE_CLASSES:
        raise ValueError(f"UNKNOWN_FAILURE_CLASS:{failure_class}")
    return FailureInfo(
        failure_class=failure_class,
        observable_code=observable_code,
        resumable=resumable,
        terminal=terminal,
        user_action_required=user_action_required,
        next_adapter=next_adapter,
    )
