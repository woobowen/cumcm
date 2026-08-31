"""Independent mechanical audit for automated decisions and their procedure."""

from __future__ import annotations

from typing import Any

FORBIDDEN_FIELDS = {"human_gate", "human_approved", "human_selected", "majority_vote_result"}
NETWORK_CLAIM = "NETWORK_POLICY_PROHIBITED_TRACE_AUDITED"


def _walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_walk_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_walk_keys(item) for item in value), set())
    return set()


def audit_payload(
    payload: dict,
    *,
    policy_hash: str,
    expected_policy_hash: str,
    recovery_ranked: bool = False,
    identity_leaked: bool = False,
    replay_hash_verified: bool = True,
    raw_trace_tracked: bool = False,
) -> dict:
    checks = {
        "rules_frozen": policy_hash == expected_policy_hash,
        "candidate_anonymous": not identity_leaked,
        "no_forbidden_human_fields": not bool(_walk_keys(payload) & FORBIDDEN_FIELDS),
        "recovery_not_ranked": not recovery_ranked,
        "no_majority_vote": payload.get("majority_vote_used") is not True,
        "replay_hash_verified": replay_hash_verified,
        "raw_trace_not_tracked": not raw_trace_tracked,
        "network_claim_bounded": payload.get("network_isolation_level", NETWORK_CLAIM)
        == NETWORK_CLAIM,
    }
    failures = sorted(name for name, passed in checks.items() if not passed)
    return {"checks": checks, "result": "PASS" if not failures else "FAIL", "failures": failures}


def audit_decision_record(record: dict, **kwargs: Any) -> dict:
    result = audit_payload(record, **kwargs)
    return {
        "audit_id": f"AUDIT-{record.get('decision_id', 'UNKNOWN')}",
        "decision_id": record.get("decision_id", "UNKNOWN"),
        "independent": True,
        **result,
        "replay_hash_verified": result["checks"]["replay_hash_verified"],
        "created_at": record.get("created_at", "1970-01-01T00:00:00Z"),
    }
