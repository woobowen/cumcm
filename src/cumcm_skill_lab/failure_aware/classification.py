"""Deterministically classify every frozen Phase 002D attempt."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import RESULT_ROOT, SOURCE_ROOT, check_or_write, hashed_body, read_json

CLASSIFICATION_DIR = RESULT_ROOT / "attempt_classification"
SUMMARY_PATH = RESULT_ROOT / "failure_attribution_summary.json"
INFRASTRUCTURE_FAILURES = {
    "TLS_HANDSHAKE_TIMEOUT",
    "RESPONSES_CONNECT_RESET",
    "WEBSOCKET_RESET",
    "HTTPS_FALLBACK_DISCONNECT",
    "PROCESS_TIMEOUT",
    "UNKNOWN_TRANSPORT_FAILURE",
}
TERMINAL_CLASSIFICATIONS = {
    "VALID_OUTPUT_ORACLE_FAIL",
    "TERMINAL_POLICY_FAILURE",
    "TERMINAL_MODEL_SCHEMA_FAILURE",
    "TERMINAL_UNSUPPORTED_CLAIM_FAILURE",
}


def _paths(attempt_id: str) -> dict[str, Path]:
    return {
        "attempt": SOURCE_ROOT / f"attempts/{attempt_id}.json",
        "eligibility": SOURCE_ROOT / f"eligibility/{attempt_id}.json",
        "oracle": SOURCE_ROOT / f"oracle/{attempt_id}.json",
        "process": SOURCE_ROOT / f"process_evidence/{attempt_id}.json",
        "observation": SOURCE_ROOT / f"runs/{attempt_id}/observation.json",
    }


def _harness_path_mismatch(attempt: dict[str, Any], observation: dict | None) -> bool:
    if "HARD-FAIL-003" not in attempt["hard_failures"] or observation is None:
        return False
    claimed = observation.get("files_created", [])
    return (
        bool(claimed)
        and all(item.startswith(".harness/") for item in claimed)
        and not attempt["files_written"]
    )


def classify_attempt(root: Path, attempt_id: str) -> dict[str, Any]:
    paths = _paths(attempt_id)
    attempt = read_json(root / paths["attempt"])
    eligibility = read_json(root / paths["eligibility"])
    oracle = read_json(root / paths["oracle"])
    process = read_json(root / paths["process"])
    observation_path = root / paths["observation"]
    observation = read_json(observation_path) if observation_path.is_file() else None
    harness_mismatch = _harness_path_mismatch(attempt, observation)

    flags: set[str] = {f"ORACLE_{attempt['oracle_status']}"}
    if attempt["failure_class"] == "POLICY_VIOLATION":
        flags.add("POLICY_VIOLATION_RECORDED")
    if "HARD-FAIL-003" in attempt["hard_failures"]:
        flags.add("HARD_FAIL_003_RECORDED")
    if not attempt["schema_valid"]:
        flags.add("SCHEMA_INVALID_RECORDED")
    if attempt["process_evidence_status"] != "PASS":
        flags.add("PROCESS_EVIDENCE_FAIL")
    if attempt["failure_class"] in INFRASTRUCTURE_FAILURES:
        flags.add("TRANSPORT_FAILURE_RECORDED")
    if attempt["completion_status"] == "COMPLETED":
        flags.add("COMPLETED_OUTPUT_RETAINED")
    if attempt["retry_of"] is not None:
        flags.add("RETRY_ATTEMPT")
    if harness_mismatch:
        flags.add("HARNESS_PATH_CLAIM_MISMATCH")
    if observation is None:
        flags.add("OBSERVATION_UNAVAILABLE")

    if attempt["primary_eligible"]:
        primary = (
            "ELIGIBLE_SUCCESS" if attempt["oracle_status"] == "PASS" else "VALID_OUTPUT_ORACLE_FAIL"
        )
        basis = "PRIMARY_ELIGIBILITY_AND_ORACLE"
        confidence = "HIGH"
    elif attempt["failure_class"] in INFRASTRUCTURE_FAILURES:
        primary = "INFRASTRUCTURE_CENSORED"
        basis = "TRANSPORT_OBSERVATION_WITH_HARNESS_SECONDARY"
        confidence = "MEDIUM" if attempt["hard_failures"] else "HIGH"
    elif attempt["failure_class"] == "POLICY_VIOLATION":
        primary = "TERMINAL_POLICY_FAILURE"
        basis = "RUNNER_POLICY_TERMINAL"
        confidence = "HIGH"
    elif attempt["failure_class"] == "SCHEMA_INVALID":
        primary = "TERMINAL_MODEL_SCHEMA_FAILURE"
        basis = "RUNNER_SCHEMA_TERMINAL"
        confidence = "HIGH"
    elif harness_mismatch:
        primary = "HARNESS_CENSORED"
        basis = "HARNESS_FILE_BINDING_MISMATCH"
        confidence = "MEDIUM"
    elif attempt["hard_failures"]:
        primary = "TERMINAL_UNSUPPORTED_CLAIM_FAILURE"
        basis = "AUTHORITATIVE_UNSUPPORTED_CLAIM"
        confidence = "HIGH"
    else:
        primary = "UNKNOWN_CENSORED"
        basis = "UNKNOWN_FAIL_CLOSED"
        confidence = "LOW"

    evidence_refs = [
        paths["attempt"].as_posix(),
        paths["eligibility"].as_posix(),
        paths["oracle"].as_posix(),
        paths["process"].as_posix(),
        "rules/dynamic_eval_rules.yaml#hard_failures.HARD-FAIL-003",
    ]
    if observation is not None:
        evidence_refs.append(paths["observation"].as_posix())
    body = {
        "schema_version": "1.0.0",
        "classification_id": f"CLASSIFICATION:{attempt_id}",
        "attempt_id": attempt_id,
        "slot_id": attempt["cell_id"],
        "case_id": attempt["case_id"],
        "anonymous_arm_id": attempt["anonymous_arm_id"],
        "repeat_id": attempt["repeat_id"],
        "primary_classification": primary,
        "secondary_flags": sorted(flags),
        "observed": {
            "completion_status": attempt["completion_status"],
            "failure_class": attempt["failure_class"],
            "schema_valid": attempt["schema_valid"],
            "oracle_status": oracle["status"],
            "process_evidence_status": "PASS" if process["passed"] else "FAIL",
            "primary_eligible": eligibility["primary_eligible"],
            "hard_failures": attempt["hard_failures"],
            "retry_of": attempt["retry_of"],
        },
        "evidence_refs": evidence_refs,
        "attribution_basis": basis,
        "confidence": confidence,
        "identity_used": False,
        "recovery_used": False,
    }
    return hashed_body(body, "classification_hash")


def build_classifications(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ledger = read_json(root / SOURCE_ROOT / "attempt_ledger.json")
    attempt_ids = ledger["attempt_ids"]
    if len(attempt_ids) != 28 or len(set(attempt_ids)) != 28:
        raise ValueError("SOURCE_ATTEMPT_SET_NOT_28_UNIQUE")
    records = [classify_attempt(root, attempt_id) for attempt_id in attempt_ids]
    counts = Counter(item["primary_classification"] for item in records)
    hard_failure_ids = [
        item["attempt_id"]
        for item in records
        if "HARD_FAIL_003_RECORDED" in item["secondary_flags"]
    ]
    body = {
        "schema_version": "1.0.0",
        "summary_id": "PHASE-002D-R1-FAILURE-ATTRIBUTION-001",
        "source_attempt_count": 28,
        "classified_attempt_count": len(records),
        "classification_counts": {
            name: counts.get(name, 0)
            for name in (
                "ELIGIBLE_SUCCESS",
                "VALID_OUTPUT_ORACLE_FAIL",
                "TERMINAL_POLICY_FAILURE",
                "TERMINAL_MODEL_SCHEMA_FAILURE",
                "TERMINAL_UNSUPPORTED_CLAIM_FAILURE",
                "INFRASTRUCTURE_CENSORED",
                "HARNESS_CENSORED",
                "UNKNOWN_CENSORED",
                "SUPERSEDED",
            )
        },
        "policy_violation_attempt_ids": [
            item["attempt_id"]
            for item in records
            if "POLICY_VIOLATION_RECORDED" in item["secondary_flags"]
        ],
        "hard_fail_003_attempt_ids": hard_failure_ids,
        "infrastructure_attempt_ids": [
            item["attempt_id"]
            for item in records
            if item["primary_classification"] == "INFRASTRUCTURE_CENSORED"
        ],
        "completed_but_excluded_attempt_ids": [
            item["attempt_id"]
            for item in records
            if item["observed"]["completion_status"] == "COMPLETED"
            and not item["observed"]["primary_eligible"]
        ],
        "retry_attempt_ids": [
            item["attempt_id"] for item in records if "RETRY_ATTEMPT" in item["secondary_flags"]
        ],
        "hard_fail_003_definition": "fabricated_run_source_file_metric_test_or_status",
        "identity_used": False,
        "all_attempts_accounted": len(records) == 28,
    }
    return records, hashed_body(body, "summary_hash")


def check_or_write_classifications(root: Path, *, check: bool) -> dict[str, Any]:
    records, summary = build_classifications(root)
    schema = read_json(root / "contracts/failure_classification.schema.json")
    errors: list[str] = []
    validator = Draft202012Validator(schema)
    expected_paths: set[Path] = set()
    for record in records:
        validation = sorted(validator.iter_errors(record), key=str)
        errors.extend(f"CLASSIFICATION_SCHEMA:{item.message}" for item in validation)
        path = root / CLASSIFICATION_DIR / f"{record['attempt_id']}.json"
        expected_paths.add(path)
        errors.extend(check_or_write(path, record, check=check))
    errors.extend(check_or_write(root / SUMMARY_PATH, summary, check=check))
    if check and (root / CLASSIFICATION_DIR).is_dir():
        actual_paths = set((root / CLASSIFICATION_DIR).glob("*.json"))
        if actual_paths != expected_paths:
            errors.append("CLASSIFICATION_FILE_SET_MISMATCH")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "attempt_count": len(records),
        "classification_counts": summary["classification_counts"],
        "summary_hash": summary["summary_hash"],
    }
