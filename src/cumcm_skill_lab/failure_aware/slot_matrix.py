"""Resolve the frozen schedule into 24 failure-aware slot outcomes."""

from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .classification import TERMINAL_CLASSIFICATIONS, build_classifications
from .models import RESULT_ROOT, SOURCE_ROOT, check_or_write, hashed_body, read_json

SLOT_DIR = RESULT_ROOT / "slot_outcomes/records"
MATRIX_PATH = RESULT_ROOT / "slot_outcomes/slot_outcome_matrix.json"
CSV_PATH = RESULT_ROOT / "slot_outcomes/slot_outcome_matrix.csv"


def _schedule_slots(schedule: dict[str, Any]) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for block in schedule["blocks"]:
        for planned in block["planned_attempts"]:
            slots.append(
                {
                    "slot_id": planned["cell_id"],
                    "case_id": block["case_id"],
                    "anonymous_arm_id": planned["anonymous_arm_id"],
                    "repeat_id": block["repeat_id"],
                    "scheduled_order": planned["schedule_order"],
                    "block_number": block["block_number"],
                }
            )
    return slots


def _resolution(classifications: list[dict[str, Any]]) -> tuple[str, str, str | None]:
    kinds = [item["primary_classification"] for item in classifications]
    decisive = next(
        (kind for kind in kinds if kind == "ELIGIBLE_SUCCESS" or kind in TERMINAL_CLASSIFICATIONS),
        None,
    )
    if decisive == "ELIGIBLE_SUCCESS":
        return "RESOLVED_ELIGIBLE_SUCCESS", "ORACLE_PASS", None
    if decisive in TERMINAL_CLASSIFICATIONS:
        subtype = {
            "VALID_OUTPUT_ORACLE_FAIL": "ORACLE_FAIL",
            "TERMINAL_POLICY_FAILURE": "POLICY_FAILURE",
            "TERMINAL_MODEL_SCHEMA_FAILURE": "MODEL_SCHEMA_FAILURE",
            "TERMINAL_UNSUPPORTED_CLAIM_FAILURE": "UNSUPPORTED_CLAIM_FAILURE",
        }[decisive]
        return "RESOLVED_TERMINAL_NEGATIVE", subtype, None
    if "HARNESS_CENSORED" in kinds:
        return (
            "CENSORED_HARNESS",
            "HARNESS_FILE_BINDING_MISMATCH",
            "HARNESS_SEMANTIC_EQUIVALENCE_NOT_ESTABLISHED",
        )
    if "INFRASTRUCTURE_CENSORED" in kinds:
        return (
            "CENSORED_INFRASTRUCTURE",
            "INFRASTRUCTURE_ONLY",
            "TARGETED_SUPPLEMENTAL_AUTHORIZATION_REQUIRED",
        )
    return "UNRESOLVED_UNKNOWN", "UNKNOWN_ATTRIBUTION", "FAIL_CLOSED_UNKNOWN"


def build_slot_matrix(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    schedule = read_json(root / SOURCE_ROOT / "schedule/schedule.json")
    ledger = read_json(root / SOURCE_ROOT / "attempt_ledger.json")
    attempts = {
        attempt_id: read_json(root / SOURCE_ROOT / f"attempts/{attempt_id}.json")
        for attempt_id in ledger["attempt_ids"]
    }
    classifications, _ = build_classifications(root)
    classified = {item["attempt_id"]: item for item in classifications}
    order = {attempt_id: index for index, attempt_id in enumerate(ledger["attempt_ids"])}
    by_slot: dict[str, list[str]] = defaultdict(list)
    for attempt_id in ledger["attempt_ids"]:
        by_slot[attempts[attempt_id]["cell_id"]].append(attempt_id)

    records: list[dict[str, Any]] = []
    for planned in _schedule_slots(schedule):
        attempt_ids = sorted(by_slot[planned["slot_id"]], key=order.__getitem__)
        if not attempt_ids:
            raise ValueError(f"SCHEDULED_SLOT_UNATTEMPTED:{planned['slot_id']}")
        attempt_values = [attempts[item] for item in attempt_ids]
        class_values = [classified[item] for item in attempt_ids]
        observed_success_ids = [
            item["attempt_id"]
            for item in class_values
            if item["primary_classification"] == "ELIGIBLE_SUCCESS"
        ]
        terminal_ids = [
            item["attempt_id"]
            for item in class_values
            if item["primary_classification"] in TERMINAL_CLASSIFICATIONS
        ]
        infrastructure_ids = [
            item["attempt_id"]
            for item in class_values
            if item["primary_classification"] == "INFRASTRUCTURE_CENSORED"
        ]
        harness_ids = [
            item["attempt_id"]
            for item in class_values
            if item["primary_classification"] == "HARNESS_CENSORED"
        ]
        resolution, subtype, unresolved = _resolution(class_values)
        selected_success_id = (
            observed_success_ids[0]
            if resolution == "RESOLVED_ELIGIBLE_SUCCESS" and observed_success_ids
            else None
        )
        first_completion = next(
            (
                item["attempt_id"]
                for item in attempt_values
                if item["completion_status"] == "COMPLETED"
            ),
            None,
        )
        body = {
            "schema_version": "1.0.0",
            "slot_id": planned["slot_id"],
            "case_id": planned["case_id"],
            "anonymous_arm_id": planned["anonymous_arm_id"],
            "repeat_id": planned["repeat_id"],
            "scheduled_order": planned["scheduled_order"],
            "all_attempt_ids": attempt_ids,
            "attempt_count": len(attempt_ids),
            "first_attempt_id": attempt_ids[0],
            "first_completion_id": first_completion,
            "first_eligible_success_id": observed_success_ids[0] if observed_success_ids else None,
            "selected_quality_record_id": selected_success_id,
            "terminal_failure_ids": terminal_ids,
            "infrastructure_failure_ids": infrastructure_ids,
            "harness_failure_ids": harness_ids,
            "outcome_resolution": resolution,
            "outcome_subtype": subtype,
            "quality_eligible": selected_success_id is not None,
            "reliability_eligible": True,
            "censored": resolution.startswith("CENSORED_") or resolution == "UNRESOLVED_UNKNOWN",
            "retry_count": len(attempt_ids) - 1,
            "policy_violation_count": sum(
                item["failure_class"] == "POLICY_VIOLATION" for item in attempt_values
            ),
            "hard_failure_count": sum(bool(item["hard_failures"]) for item in attempt_values),
            "oracle_pass_count": sum(item["oracle_status"] == "PASS" for item in attempt_values),
            "oracle_fail_count": sum(item["oracle_status"] == "FAIL" for item in attempt_values),
            "input_tokens": sum(item["input_tokens"] or 0 for item in attempt_values),
            "output_tokens": sum(item["output_tokens"] or 0 for item in attempt_values),
            "elapsed_seconds": round(sum(item["duration_seconds"] for item in attempt_values), 6),
            "evidence_ids": [item["classification_id"] for item in class_values],
            "confidence": "LOW" if resolution.startswith("CENSORED_") else "HIGH",
            "unresolved_reason": unresolved,
        }
        records.append((planned["block_number"], hashed_body(body, "slot_hash")))
    slot_records = [
        record
        for _, record in sorted(records, key=lambda item: (item[0], item[1]["scheduled_order"]))
    ]
    counts = Counter(item["outcome_resolution"] for item in slot_records)
    resolution_names = (
        "RESOLVED_ELIGIBLE_SUCCESS",
        "RESOLVED_TERMINAL_NEGATIVE",
        "CENSORED_INFRASTRUCTURE",
        "CENSORED_HARNESS",
        "UNRESOLVED_UNKNOWN",
        "STALE",
    )
    accounted = sorted(item for record in slot_records for item in record["all_attempt_ids"])
    body = {
        "schema_version": "1.0.0",
        "matrix_id": "PHASE-002D-R1-SLOT-OUTCOME-MATRIX-001",
        "input_freeze_id": "PHASE-002D-R1-INPUT-FREEZE-001",
        "schedule_hash": schedule["schedule_hash"],
        "source_attempt_count": len(ledger["attempt_ids"]),
        "expected_slot_count": 24,
        "slots": slot_records,
        "resolution_counts": {name: counts.get(name, 0) for name in resolution_names},
        "all_attempts_accounted": accounted == sorted(ledger["attempt_ids"]),
        "earliest_eligible_selection": all(
            item["selected_quality_record_id"] in (None, item["first_eligible_success_id"])
            for item in slot_records
        ),
        "best_of_n_prohibited": all(
            item["selected_quality_record_id"] in (None, item["first_eligible_success_id"])
            for item in slot_records
        ),
    }
    matrix = hashed_body(body, "matrix_hash")
    return slot_records, matrix, render_slot_csv(slot_records)


def render_slot_csv(records: list[dict[str, Any]]) -> str:
    output = io.StringIO(newline="")
    fields = [key for key in records[0] if key != "schema_version"]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for record in records:
        row = {}
        for key in fields:
            value = record[key]
            if isinstance(value, list):
                value = "|".join(str(item) for item in value)
            elif value is None:
                value = ""
            elif isinstance(value, bool):
                value = str(value).lower()
            row[key] = value
        writer.writerow(row)
    return output.getvalue()


def check_or_write_slot_matrix(root: Path, *, check: bool) -> dict[str, Any]:
    records, matrix, csv_text = build_slot_matrix(root)
    slot_validator = Draft202012Validator(read_json(root / "contracts/slot_outcome.schema.json"))
    matrix_validator = Draft202012Validator(
        read_json(root / "contracts/slot_outcome_matrix.schema.json")
    )
    errors = [
        f"SLOT_SCHEMA:{error.message}"
        for record in records
        for error in slot_validator.iter_errors(record)
    ]
    errors.extend(
        f"MATRIX_SCHEMA:{error.message}" for error in matrix_validator.iter_errors(matrix)
    )
    for record in records:
        errors.extend(
            check_or_write(root / SLOT_DIR / f"{record['slot_id']}.json", record, check=check)
        )
    errors.extend(check_or_write(root / MATRIX_PATH, matrix, check=check))
    csv_path = root / CSV_PATH
    if check:
        if not csv_path.is_file() or csv_path.read_text(encoding="utf-8") != csv_text:
            errors.append(f"MISMATCH:{CSV_PATH}")
    else:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text(csv_text, encoding="utf-8")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "slot_count": len(records),
        "resolution_counts": matrix["resolution_counts"],
        "matrix_hash": matrix["matrix_hash"],
    }
