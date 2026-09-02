"""Fail-closed Phase 002D adjudication absence and route record."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import RESULT_ROOT, check_or_write, hashed_body, read_json, sha256_json

CLOSURE_PATH = RESULT_ROOT / "closure/adjudication_gate.json"
CLOSURE_SCHEMA_PATH = Path("contracts/phase002d_decision.schema.json")


def build_closure(root: Path) -> dict[str, Any]:
    sufficiency = read_json(root / RESULT_ROOT / "sufficiency/evidence_sufficiency.json")
    checkpoint = read_json(root / RESULT_ROOT / "checkpoint.json")
    if sufficiency["result"] == "SUFFICIENT":
        raise RuntimeError("PHASE002D_M8_REQUIRED_AFTER_SUFFICIENT_EVIDENCE")
    body = {
        "schema_version": "1.0.0",
        "gate_id": "PHASE-002D-ADJUDICATION-PRECONDITION-GATE",
        "phase": "PHASE-EVIDENCE-EXPANSION-002D",
        "status": "LOCKED_EVIDENCE_INSUFFICIENT",
        "evidence_sufficiency": sufficiency["result"],
        "sufficiency_record_hash": sufficiency["record_hash"],
        "runner_status": checkpoint["status"],
        "runner_hard_stop_reasons": checkpoint["hard_stop_reasons"],
        "native_subagents_started": False,
        "automated_decisions_generated": False,
        "automated_decision_ids": [],
        "decision_auditor": "NOT_RUN_PRECONDITION_FAILED",
        "decision_replay": "NOT_RUN_PRECONDITION_FAILED",
        "route_replay": "PASS",
        "technical_adjudication_status": "EVIDENCE_EXPANSION_INCOMPLETE",
        "next_phase_allowed": "PHASE-EVIDENCE-EXPANSION-002D",
        "phase_003_allowed": False,
        "phase_003_started": False,
        "automated_decision_contract": "contracts/automated_decision.schema.json",
    }
    return hashed_body(body, "record_hash")


def validate_closure(root: Path, value: dict[str, Any]) -> list[str]:
    schema = read_json(root / CLOSURE_SCHEMA_PATH)
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(value)]
    body = dict(value)
    recorded = body.pop("record_hash", None)
    if sha256_json(body) != recorded:
        errors.append("PHASE002D_CLOSURE_HASH_MISMATCH")
    if value.get("evidence_sufficiency") != "SUFFICIENT" and (
        value.get("native_subagents_started")
        or value.get("automated_decisions_generated")
        or value.get("automated_decision_ids")
    ):
        errors.append("PHASE002D_ADJUDICATION_UNLOCKED_WITHOUT_SUFFICIENCY")
    if value.get("phase_003_allowed") or value.get("phase_003_started"):
        errors.append("PHASE003_ILLEGALLY_UNLOCKED")
    return errors


def check_or_write_closure(root: Path, *, check: bool) -> dict[str, Any]:
    expected = build_closure(root)
    errors = validate_closure(root, expected)
    errors.extend(check_or_write(root / CLOSURE_PATH, expected, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "gate_status": expected["status"],
        "native_subagents_started": expected["native_subagents_started"],
        "automated_decisions_generated": expected["automated_decisions_generated"],
        "decision_auditor": expected["decision_auditor"],
        "decision_replay": expected["decision_replay"],
        "route_replay": expected["route_replay"],
        "next_phase_allowed": expected["next_phase_allowed"],
        "record_hash": expected["record_hash"],
    }
