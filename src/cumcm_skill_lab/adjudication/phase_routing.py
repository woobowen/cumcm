"""Derive the next phase from an audited architecture/evidence decision."""

from __future__ import annotations

from typing import Any

from .models import sha256_json

PHASE_002C = "PHASE-AUTOMATED-EVIDENCE-SUFFICIENCY-002C"
PHASE_002D = "PHASE-EVIDENCE-EXPANSION-002D"
PHASE_003 = "PHASE-SKILL-INTEGRATION-003"


def build_phase_route(
    decision: dict[str, Any],
    *,
    audit_result: str,
    phase003_prerequisites_met: bool = False,
) -> dict[str, Any]:
    next_phase: str | None = None
    phase003_allowed = False
    evidence_expansion_allowed = False
    reasons: list[str] = []
    if audit_result != "PASS":
        reasons.append("DECISION_AUDIT_NOT_PASS")
    elif decision["decision"] in {"EVIDENCE_INSUFFICIENT", "AUTOMATED_REJECTED"}:
        next_phase = PHASE_002D
        evidence_expansion_allowed = True
        reasons.append("NON_ACCEPTING_DECISION_ROUTES_TO_EVIDENCE_EXPANSION")
    elif decision["decision"] == "AUTOMATED_ACCEPTED" and phase003_prerequisites_met:
        next_phase = PHASE_003
        phase003_allowed = True
        reasons.append("ALL_PHASE003_PREREQUISITES_MET")
    else:
        reasons.append("NO_NEXT_PHASE_AUTHORIZED")
    route = {
        "route_id": "PHASE-ROUTE-002C",
        "decision_id": decision["decision_id"],
        "decision": decision["decision"],
        "audit_result": audit_result,
        "current_phase": PHASE_002C,
        "next_phase_allowed": next_phase,
        "phase003_allowed": phase003_allowed,
        "evidence_expansion_allowed": evidence_expansion_allowed,
        "phase002d_started": False,
        "reason_codes": reasons,
    }
    route["route_hash"] = sha256_json(route)
    return route
