"""Lexicographic evidence decision engine; it never counts Judge votes."""

from __future__ import annotations

from typing import Any


def decide(facts: dict[str, Any]) -> dict:
    reasons: list[str] = []
    if facts.get("stale"):
        return {"decision": "STALE", "reason_codes": ["DEPENDENCY_STALE"]}
    failed_gates = sorted(
        name for name, passed in facts.get("hard_gates", {}).items() if passed is not True
    )
    if failed_gates:
        return {
            "decision": "AUTOMATED_REJECTED",
            "reason_codes": [f"HARD_GATE_FAILED:{name}" for name in failed_gates],
        }
    failed_counterexamples = list(facts.get("failed_counterexample_tests", []))
    if failed_counterexamples:
        return {
            "decision": "AUTOMATED_REJECTED",
            "reason_codes": [f"COUNTEREXAMPLE_CONFIRMED:{item}" for item in failed_counterexamples],
        }
    unresolved = list(facts.get("unresolved_blockers", []))
    if unresolved:
        status = "RETEST_REQUIRED" if facts.get("retriable", False) else "AUTOMATED_ABSTAINED"
        return {
            "decision": status,
            "reason_codes": [f"UNRESOLVED_BLOCKER:{item}" for item in unresolved],
        }
    if facts.get("evidence_sufficiency") != "SUFFICIENT":
        return {
            "decision": "EVIDENCE_INSUFFICIENT",
            "reason_codes": list(facts.get("sufficiency_reasons", []))
            or ["EVIDENCE_BELOW_FROZEN_MINIMUM"],
        }
    if facts.get("oracle_pass") is not True:
        return {"decision": "AUTOMATED_REJECTED", "reason_codes": ["ORACLE_FAILED"]}
    if facts.get("process_pass") is not True:
        status = "RETEST_REQUIRED" if facts.get("retriable", True) else "AUTOMATED_REJECTED"
        return {"decision": status, "reason_codes": ["PROCESS_EVIDENCE_FAILED"]}
    if facts.get("stable") is not True:
        return {"decision": "AUTOMATED_ABSTAINED", "reason_codes": ["REPLAY_UNSTABLE"]}
    if facts.get("decision_audit") != "PASS":
        return {"decision": "AUTOMATED_ABSTAINED", "reason_codes": ["AUDIT_NOT_PASS"]}
    reasons.append("ALL_LEXICOGRAPHIC_GATES_PASSED")
    return {"decision": "AUTOMATED_ACCEPTED", "reason_codes": reasons}


def phase_transition_allowed(architecture: dict, components: dict, all_tests_pass: bool) -> bool:
    component_rows = components.get("component_results", [])
    return bool(
        architecture.get("decision") == "AUTOMATED_ACCEPTED"
        and architecture.get("decision_audit_result") == "PASS"
        and any(
            row.get("decision") == "AUTOMATED_ACCEPTED"
            and row.get("accepted_scope") == "SPECIFICATION_ONLY"
            for row in component_rows
        )
        and not architecture.get("unresolved_blockers")
        and architecture.get("replay_stable") is True
        and all_tests_pass
    )
