"""Normalize and validate the independent C1 final authorization audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .candidate_freeze import FREEZE_PATH
from .compatibility_audits import normalize_audit, validate_audit
from .final_audit_bundle import BUNDLE_PATH, validate_final_audit_bundle
from .models import RESULT_ROOT, check_or_write_json

RAW_AUDIT_PATH = RESULT_ROOT / "subagent_outputs/raw/final_shadow_authorization_auditor.json"
OUTPUT_AUDIT_PATH = RESULT_ROOT / "subagent_outputs/final_shadow_authorization_auditor.json"
FINAL_AUDIT_PATH = RESULT_ROOT / "final_audit/audit-c1.json"
FINAL_ROLE = "final_shadow_authorization_auditor"
FINAL_VERDICTS = {"PASS", "FAIL", "RETEST_REQUIRED"}
TERMINAL_ACTIONS = {"SEAL", "REPLAY", "STATE_TRANSITION"}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_final_audit(root: Path, value: dict[str, Any]) -> list[str]:
    errors = validate_audit(root, value, FINAL_ROLE)
    bundle = _read_json(root / BUNDLE_PATH)
    freeze = _read_json(root / FREEZE_PATH)
    errors.extend(validate_final_audit_bundle(root, bundle))
    expected = {
        "candidate_id": freeze["candidate_id"],
        "candidate_file_sha256": freeze["candidate_file_sha256"],
        "canonical_candidate_hash": freeze["canonical_candidate_hash"],
        "candidate_freeze_hash": freeze["freeze_hash"],
        "bundle_hash": bundle["bundle_hash"],
        "parent_artifact_hash": bundle["bundle_hash"],
        "artifact_sequence_index": 10,
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            errors.append(f"C1_FINAL_AUDIT_{field.upper()}_MISMATCH")
    if value.get("verdict") not in FINAL_VERDICTS:
        errors.append("C1_FINAL_AUDIT_VERDICT_INVALID")
    serious_open = [
        item.get("finding_id")
        for item in value.get("findings", [])
        if item.get("severity") in {"BLOCKER", "ERROR"} and item.get("status") not in {"RESOLVED"}
    ]
    if value.get("verdict") == "PASS" and (value.get("unresolved_blockers") or serious_open):
        errors.append("C1_FINAL_AUDIT_PASS_WITH_UNRESOLVED_SERIOUS_FINDING")
    return sorted(set(errors))


def check_or_write_final_audit(root: Path, *, check: bool) -> dict[str, Any]:
    raw_path = root / RAW_AUDIT_PATH
    if not raw_path.is_file():
        return {
            "status": "FAIL",
            "errors": ["C1_FINAL_AUDIT_RAW_OUTPUT_MISSING"],
            "result": "NOT_RUN",
        }
    value = normalize_audit(_read_json(raw_path))
    errors = validate_final_audit(root, value)
    errors.extend(check_or_write_json(root / OUTPUT_AUDIT_PATH, value, check=check))
    errors.extend(check_or_write_json(root / FINAL_AUDIT_PATH, value, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "audit_id": value.get("audit_id"),
        "result": value.get("verdict"),
        "output_hash": value.get("output_hash"),
        "bundle_hash": value.get("bundle_hash"),
        "candidate_file_sha256": value.get("candidate_file_sha256"),
        "canonical_candidate_hash": value.get("canonical_candidate_hash"),
        "candidate_freeze_hash": value.get("candidate_freeze_hash"),
        "unresolved_blockers": value.get("unresolved_blockers", []),
    }


def evaluate_final_audit_gate(root: Path, action: str) -> dict[str, Any]:
    if action not in TERMINAL_ACTIONS:
        raise ValueError(f"C1_FINAL_AUDIT_UNKNOWN_TERMINAL_ACTION:{action}")
    audit = _read_json(root / FINAL_AUDIT_PATH)
    errors = validate_final_audit(root, audit)
    if audit.get("verdict") != "PASS":
        errors.append("C1_FINAL_AUTHORIZATION_AUDIT_NOT_PASS")
    if audit.get("unresolved_blockers"):
        errors.append("C1_FINAL_AUTHORIZATION_AUDIT_BLOCKERS_PRESENT")
    return {
        "action": action,
        "status": "PASS" if not errors else "BLOCKED",
        "errors": sorted(set(errors)),
        "audit_id": audit.get("audit_id"),
        "audit_result": audit.get("verdict"),
        "audit_output_hash": audit.get("output_hash"),
        "unresolved_blockers": audit.get("unresolved_blockers", []),
    }


__all__ = [
    "FINAL_AUDIT_PATH",
    "OUTPUT_AUDIT_PATH",
    "RAW_AUDIT_PATH",
    "check_or_write_final_audit",
    "evaluate_final_audit_gate",
    "validate_final_audit",
]
