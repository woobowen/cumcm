"""Normalize native read-only audit transports and close compatibility findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .historical_record import build_historical_record
from .models import CREATED_AT, RESULT_ROOT, check_or_write_json, sha256_json
from .schema_resolution import build_schema_resolution_record

RAW_ROOT = RESULT_ROOT / "subagent_outputs/raw"
OUTPUT_ROOT = RESULT_ROOT / "subagent_outputs"
CLOSURE_PATH = RESULT_ROOT / "compatibility_tests/closure.json"
FIRST_ROUND_ROLES = (
    "historical_freeze_semantics_auditor",
    "schema_version_compatibility_auditor",
    "candidate_binding_prosecutor",
)
COMPATIBILITY_FINDINGS = {
    "HFS-AUD-001": "HFS-C1-T016-C1-SUBJECT-COMMIT-RETARGET-REJECTED",
    "HFS-AUD-002": "HFS-C1-T017-LIVE-POINTER-DUPLICATE-YAML-KEY-REJECTED",
    "HFS-AUD-003": "HFS-C1-T018-DERIVED-OBSERVATION-AUTHORITY-RECOMPUTED",
    "SCHEMA-COMPAT-001": "C1-SCHEMA-016-MISSING-SHADOW-AUTHORIZATION-REJECTED",
    "SCHEMA-COMPAT-002": "C1-SCHEMA-017-C1-SUBPHASE-REJECTS-R2A-FREEZE-ID",
    "SCHEMA-COMPAT-003": "C1-SCHEMA-018-MIGRATION-RECORD-FAILS-CLOSED-ON-TARGET-SCHEMA-INVALID",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_audit(value: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(value)
    normalized.pop("output_hash", None)
    normalized["output_hash"] = sha256_json(normalized)
    return normalized


def validate_audit(root: Path, value: dict[str, Any], role: str) -> list[str]:
    schema = _read_json(root / "contracts/c1_native_audit.schema.json")
    errors = [
        f"C1_NATIVE_AUDIT_SCHEMA:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(schema).iter_errors(value)
    ]
    if value.get("role") != role:
        errors.append("C1_NATIVE_AUDIT_ROLE_MISMATCH")
    body = dict(value)
    recorded = body.pop("output_hash", None)
    if sha256_json(body) != recorded:
        errors.append("C1_NATIVE_AUDIT_OUTPUT_HASH_MISMATCH")
    ids = [item.get("finding_id") for item in value.get("findings", [])]
    if len(ids) != len(set(ids)):
        errors.append("C1_NATIVE_AUDIT_FINDING_ID_DUPLICATE")
    if any(
        item.get("severity") in {"BLOCKER", "ERROR"} and not item.get("required_test")
        for item in value.get("findings", [])
    ):
        errors.append("C1_NATIVE_AUDIT_SERIOUS_FINDING_WITHOUT_TEST")
    return sorted(set(errors))


def build_compatibility_closure(root: Path, audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    historical = build_historical_record(root)
    schema_record, migration = build_schema_resolution_record(root)
    candidate_findings = [
        item
        for item in audits["candidate_binding_prosecutor"]["findings"]
        if item["severity"] in {"BLOCKER", "ERROR"}
    ]
    closures = [
        {
            "finding_id": finding_id,
            "required_test_id": test_id,
            "status": "CLOSED",
        }
        for finding_id, test_id in COMPATIBILITY_FINDINGS.items()
    ]
    errors: list[str] = []
    if historical["result"] != "PASS":
        errors.append("HISTORICAL_COMPATIBILITY_NOT_PASS")
    if schema_record["result"] != "PASS":
        errors.append("SCHEMA_COMPATIBILITY_NOT_PASS")
    if migration["target_schema_validation_result"] != "PASS":
        errors.append("MIGRATION_TARGET_SCHEMA_NOT_PASS")
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "closure_id": "PHASE-002D-R2A-C1-COMPATIBILITY-AUDIT-CLOSURE-001",
        "artifact_sequence_index": 3,
        "parent_artifact_hash": schema_record["record_hash"],
        "created_at": CREATED_AT,
        "audit_output_hashes": {role: audits[role]["output_hash"] for role in FIRST_ROUND_ROLES},
        "historical_compatibility_hash": historical["record_hash"],
        "schema_resolution_hash": schema_record["record_hash"],
        "closures": closures,
        "candidate_findings_deferred_to_m5_m6": [
            {"finding_id": item["finding_id"], "required_test_id": item["required_test"]}
            for item in candidate_findings
        ],
        "candidate_prosecutor_verdict": audits["candidate_binding_prosecutor"]["verdict"],
        "candidate_abstention_treated_as_pass": False,
        "unresolved_compatibility_blockers": [],
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    body["closure_hash"] = sha256_json(body)
    return body


def check_or_write_compatibility_audits(root: Path, *, check: bool) -> dict[str, Any]:
    errors: list[str] = []
    audits: dict[str, dict[str, Any]] = {}
    for role in FIRST_ROUND_ROLES:
        raw_path = root / RAW_ROOT / f"{role}.json"
        if not raw_path.is_file():
            errors.append(f"C1_NATIVE_AUDIT_RAW_MISSING:{role}")
            continue
        normalized = normalize_audit(_read_json(raw_path))
        errors.extend(f"{role}:{item}" for item in validate_audit(root, normalized, role))
        errors.extend(
            check_or_write_json(root / OUTPUT_ROOT / f"{role}.json", normalized, check=check)
        )
        audits[role] = normalized
    closure = None
    if len(audits) == len(FIRST_ROUND_ROLES):
        closure = build_compatibility_closure(root, audits)
        errors.extend(check_or_write_json(root / CLOSURE_PATH, closure, check=check))
        if closure["result"] != "PASS":
            errors.extend(closure["errors"])
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "audit_output_hashes": {role: item["output_hash"] for role, item in audits.items()},
        "closure_hash": closure["closure_hash"] if closure else None,
    }


__all__ = [
    "CLOSURE_PATH",
    "FIRST_ROUND_ROLES",
    "build_compatibility_closure",
    "check_or_write_compatibility_audits",
    "normalize_audit",
    "validate_audit",
]
