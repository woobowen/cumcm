"""Completion and transition semantics for Phase 002B machine records."""

from __future__ import annotations

from typing import Any

from .bundles.role_views import ROLE_ORDER

COMPLETE = "AUTOMATED_ADJUDICATION_COMPLETE"
INCOMPLETE = "AUTOMATED_ADJUDICATION_INCOMPLETE"
DECISION_VALUES = {
    "AUTOMATED_ACCEPTED",
    "AUTOMATED_REJECTED",
    "RETEST_REQUIRED",
    "EVIDENCE_INSUFFICIENT",
    "AUTOMATED_ABSTAINED",
    "STALE",
}


def classify_completion(
    role_records: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    audit: dict[str, Any] | None,
    replay: dict[str, Any] | None,
) -> str:
    roles = {item.get("role_id"): item for item in role_records}
    roles_complete = all(
        roles.get(role, {}).get("status") == "COMPLETED"
        and roles.get(role, {}).get("schema_valid") is True
        for role in ROLE_ORDER
    )
    decisions_complete = (
        len(decisions) == 3
        and len({item.get("decision_id") for item in decisions}) == 3
        and all(item.get("decision") in DECISION_VALUES for item in decisions)
    )
    audit_complete = bool(audit and audit.get("result") in {"PASS", "FAIL", "RETEST_REQUIRED"})
    replay_complete = bool(replay and replay.get("stable") is True)
    return (
        COMPLETE
        if all((roles_complete, decisions_complete, audit_complete, replay_complete))
        else INCOMPLETE
    )


def phase003_allowed(
    decisions: list[dict[str, Any]], audit: dict[str, Any], replay: dict[str, Any]
) -> bool:
    by_type = {item.get("decision_type"): item for item in decisions}
    return bool(
        audit.get("result") == "PASS"
        and replay.get("stable") is True
        and by_type.get("ARCHITECTURE", {}).get("decision") == "AUTOMATED_ACCEPTED"
        and by_type.get("COMPONENTS", {}).get("decision") == "AUTOMATED_ACCEPTED"
        and by_type.get("COMPONENTS", {}).get("accepted_scope") == "SPECIFICATION_ONLY"
    )
