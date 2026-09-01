"""Map deterministic prerequisites to the legal pre-adjudication action."""

from __future__ import annotations

from typing import Any


def evaluate_short_circuit(sufficiency: dict[str, Any]) -> dict[str, Any]:
    conditions = sufficiency["conditions"]
    if sufficiency["result"] == "STALE":
        return {
            "short_circuit": True,
            "decision": "STALE",
            "semantic_judges_status": "BLOCKED",
            "ranking_status": "PROHIBITED",
            "next_phase_candidate": None,
        }
    if not conditions["mandatory_hard_gates_passed"]:
        return {
            "short_circuit": True,
            "decision": "AUTOMATED_REJECTED",
            "semantic_judges_status": "SKIPPED",
            "ranking_status": "PROHIBITED",
            "next_phase_candidate": "PHASE-EVIDENCE-EXPANSION-002D",
        }
    if sufficiency["result"] == "INSUFFICIENT":
        return {
            "short_circuit": True,
            "decision": "EVIDENCE_INSUFFICIENT",
            "semantic_judges_status": "SKIPPED",
            "ranking_status": "PROHIBITED",
            "next_phase_candidate": "PHASE-EVIDENCE-EXPANSION-002D",
        }
    return {
        "short_circuit": False,
        "decision": "CONTINUE_SEMANTIC_ADJUDICATION",
        "semantic_judges_status": "REQUIRED",
        "ranking_status": "ALLOWED",
        "next_phase_candidate": None,
    }
