"""Validate a frozen architecture candidate set without selecting a candidate."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import read_json, read_yaml, sha256_json

CANDIDATE_CONTRACT = Path("contracts/architecture_candidate.schema.json")
SET_CONTRACT = Path("contracts/architecture_candidate_set.schema.json")
SPECIFICATION = Path("specifications/architectures/architecture_candidate_set.yaml")
BASELINE_ID = "ARCH-S0-RETAIN-SCAFFOLD-ONLY"


def validate_candidate_set_value(
    set_schema: dict[str, Any], candidate_schema: dict[str, Any], value: dict[str, Any]
) -> list[str]:
    errors = [
        f"ARCHITECTURE_SET_SCHEMA:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(set_schema).iter_errors(value)
    ]
    candidates = value.get("candidates", [])
    for candidate in candidates:
        errors.extend(
            f"ARCHITECTURE_CANDIDATE_SCHEMA:{candidate.get('architecture_id')}:{item.message}"
            for item in Draft202012Validator(candidate_schema).iter_errors(candidate)
        )
    ids = [item.get("architecture_id") for item in candidates]
    if len(ids) != len(set(ids)):
        errors.append("ARCHITECTURE_ID_DUPLICATE")
    if BASELINE_ID not in ids or value.get("baseline_id") != BASELINE_ID:
        errors.append("ARCHITECTURE_BASELINE_MISSING")
    if value.get("selected_architecture") is not None:
        errors.append("ARCHITECTURE_PRESELECTED")
    if any(item.get("formal_skill_count") != 1 for item in candidates):
        errors.append("ARCHITECTURE_SECOND_FORMAL_SKILL")
    if any(item.get("state_truth_sources") != ["state/project_state.json"] for item in candidates):
        errors.append("ARCHITECTURE_SECOND_STATE_SOURCE")
    prohibited_text = " ".join(
        value for item in candidates for value in item.get("prohibited_behavior", [])
    ).lower()
    if "third-party" not in prohibited_text and "upstream" not in prohibited_text:
        errors.append("ARCHITECTURE_UPSTREAM_PACKAGE_PROHIBITION_MISSING")
    body = dict(value)
    recorded = body.pop("candidate_set_hash", None)
    if sha256_json(body) != recorded:
        errors.append("ARCHITECTURE_SET_HASH_MISMATCH")
    return sorted(set(errors))


def validate_architecture_candidates(root: Path) -> dict[str, Any]:
    value = read_yaml(root / SPECIFICATION)
    errors = validate_candidate_set_value(
        read_json(root / SET_CONTRACT), read_json(root / CANDIDATE_CONTRACT), value
    )
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "candidate_set_id": value.get("candidate_set_id"),
        "candidate_ids": [item.get("architecture_id") for item in value.get("candidates", [])],
        "selected_architecture": value.get("selected_architecture"),
        "decision": value.get("decision"),
    }


__all__ = [
    "BASELINE_ID",
    "CANDIDATE_CONTRACT",
    "SET_CONTRACT",
    "SPECIFICATION",
    "validate_architecture_candidates",
    "validate_candidate_set_value",
]
