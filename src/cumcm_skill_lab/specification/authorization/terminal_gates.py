"""Fail-closed validators for R2A seal, replay, and state-transition gates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import read_json

from .native_audits import FINAL_AUDIT_PATH, FINAL_ROLE, validate_subagent_output

TERMINAL_ACTIONS = ("SEAL", "REPLAY", "STATE_TRANSITION")


def evaluate_terminal_gate(root: Path, action: str) -> dict[str, Any]:
    """Return a machine-readable rejection until the independent audit passes."""
    if action not in TERMINAL_ACTIONS:
        raise ValueError(f"UNKNOWN_R2A_TERMINAL_ACTION:{action}")
    audit = read_json(root / FINAL_AUDIT_PATH)
    errors = validate_subagent_output(root, audit, FINAL_ROLE)
    if audit.get("verdict") != "PASS":
        errors.append("R2A_FINAL_AUTHORIZATION_AUDIT_NOT_PASS")
    if audit.get("blockers"):
        errors.append("R2A_FINAL_AUTHORIZATION_AUDIT_BLOCKERS_PRESENT")
    errors = sorted(set(errors))
    return {
        "action": action,
        "status": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        "audit_id": audit.get("audit_id"),
        "audit_result": audit.get("verdict"),
        "audit_checkpoint_hash": audit.get("output_hash"),
        "blockers": audit.get("blockers", []),
        "artifact_created": False,
        "formal_state_transition_performed": False,
        "next_phase_allowed": None,
    }


__all__ = ["TERMINAL_ACTIONS", "evaluate_terminal_gate"]
