"""Apply frozen policy and executed evidence without aggregating agent preferences."""

from __future__ import annotations

from .decision_engine import decide
from .models import sha256_json


def adjudicate(
    *,
    bundle_id: str,
    policy: dict,
    freeze_hash: str,
    facts: dict,
    test_evidence: list[dict],
) -> dict:
    policy_body = {key: value for key, value in policy.items() if key != "policy_hash"}
    if sha256_json(policy_body) != policy["policy_hash"]:
        raise ValueError("POLICY_HASH_MISMATCH")
    confirmed = [
        item["test_id"]
        for item in test_evidence
        if item["status"] == "FAILED" or not item["oracle_result"]
    ]
    engine_facts = {**facts, "failed_counterexample_tests": confirmed}
    result = decide(engine_facts)
    return {
        "meta_id": f"META-{bundle_id}",
        "bundle_id": bundle_id,
        "policy_hash": policy["policy_hash"],
        "freeze_hash": freeze_hash,
        "thresholds_unchanged": True,
        "majority_vote_used": False,
        "hard_gate_status": ("PASS" if all(facts.get("hard_gates", {}).values()) else "FAIL"),
        "evidence_sufficiency": facts.get("evidence_sufficiency", "INSUFFICIENT"),
        "test_evidence": [item["test_id"] for item in test_evidence],
        **result,
    }
