"""Formal-state transition guards for audited automated decisions and team challenges."""

from __future__ import annotations

from copy import deepcopy

from jsonschema import Draft202012Validator


def apply_registered_technical_transition(
    state: dict, candidate: dict, workflow_rules: dict, project_state_schema: dict
) -> dict:
    """Validate one explicit technical-status edge and every target-state invariant."""
    source = state.get("technical_adjudication_status")
    target = candidate.get("technical_adjudication_status")
    contract = workflow_rules.get("technical_adjudication_status_contract", {})
    allowed = contract.get("registered_transitions", {}).get(source, [])
    if target not in allowed:
        raise ValueError(f"TECHNICAL_STATUS_TRANSITION_NOT_ALLOWED:{source}:{target}")
    errors = sorted(Draft202012Validator(project_state_schema).iter_errors(candidate), key=str)
    if errors:
        raise ValueError(f"PROJECT_STATE_INVARIANT_FAILED:{errors[0].message}")
    return deepcopy(candidate)


def apply_automated_decision(state: dict, decision: dict, audit: dict) -> dict:
    if audit.get("result") != "PASS" or audit.get("decision_id") != decision.get("decision_id"):
        raise ValueError("DECISION_AUDIT_REQUIRED")
    updated = deepcopy(state)
    updated["technical_adjudication_status"] = decision["decision"]
    ids = list(updated.get("automated_decision_ids", []))
    if decision["decision_id"] not in ids:
        ids.append(decision["decision_id"])
    updated["automated_decision_ids"] = ids
    updated["next_phase_allowed"] = decision.get("next_phase_allowed")
    return updated


def apply_team_record(state: dict, record: dict) -> dict:
    if record.get("technical_override_allowed") is not False:
        raise ValueError("TEAM_REVIEW_CANNOT_OVERRIDE_TECHNICAL_DECISION")
    updated = deepcopy(state)
    updated["team_compliance_review_status"] = record["status"]
    if record["record_type"] == "TEAM_CHALLENGE" and record["stale_triggered"]:
        updated["technical_adjudication_status"] = "STALE"
        updated["next_phase_allowed"] = None
    return updated
