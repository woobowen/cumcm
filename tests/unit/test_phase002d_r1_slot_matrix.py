import csv
import io

import pytest
from jsonschema import Draft202012Validator

from cumcm_skill_lab.failure_aware.models import read_json
from cumcm_skill_lab.failure_aware.slot_matrix import (
    _resolution,
    build_slot_matrix,
    check_or_write_slot_matrix,
)

EXPECTED_SLOTS = {
    "CASE-001-ARM-A-R1": ("RESOLVED_ELIGIBLE_SUCCESS", 1),
    "CASE-001-ARM-A-R2": ("CENSORED_HARNESS", 3),
    "CASE-001-ARM-B-R1": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-001-ARM-B-R2": ("RESOLVED_ELIGIBLE_SUCCESS", 1),
    "CASE-001-ARM-C-R1": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-001-ARM-C-R2": ("RESOLVED_ELIGIBLE_SUCCESS", 1),
    "CASE-002-ARM-A-R1": ("RESOLVED_ELIGIBLE_SUCCESS", 1),
    "CASE-002-ARM-A-R2": ("RESOLVED_ELIGIBLE_SUCCESS", 1),
    "CASE-002-ARM-B-R1": ("RESOLVED_ELIGIBLE_SUCCESS", 1),
    "CASE-002-ARM-B-R2": ("RESOLVED_ELIGIBLE_SUCCESS", 1),
    "CASE-002-ARM-C-R1": ("RESOLVED_ELIGIBLE_SUCCESS", 1),
    "CASE-002-ARM-C-R2": ("RESOLVED_ELIGIBLE_SUCCESS", 1),
    "CASE-004-ARM-A-R1": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-004-ARM-A-R2": ("RESOLVED_TERMINAL_NEGATIVE", 2),
    "CASE-004-ARM-B-R1": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-004-ARM-B-R2": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-004-ARM-C-R1": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-004-ARM-C-R2": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-006-ARM-A-R1": ("RESOLVED_TERMINAL_NEGATIVE", 2),
    "CASE-006-ARM-A-R2": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-006-ARM-B-R1": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-006-ARM-B-R2": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-006-ARM-C-R1": ("RESOLVED_TERMINAL_NEGATIVE", 1),
    "CASE-006-ARM-C-R2": ("RESOLVED_TERMINAL_NEGATIVE", 1),
}


@pytest.mark.parametrize(("slot_id", "expected"), EXPECTED_SLOTS.items())
def test_each_scheduled_slot_has_expected_resolution_and_attempt_count(
    repo_root, slot_id, expected
):
    records, _, _ = build_slot_matrix(repo_root)
    by_id = {item["slot_id"]: item for item in records}
    assert (by_id[slot_id]["outcome_resolution"], by_id[slot_id]["attempt_count"]) == expected


@pytest.mark.parametrize(
    ("resolution", "expected_count"),
    [
        ("RESOLVED_ELIGIBLE_SUCCESS", 9),
        ("RESOLVED_TERMINAL_NEGATIVE", 14),
        ("CENSORED_INFRASTRUCTURE", 0),
        ("CENSORED_HARNESS", 1),
        ("UNRESOLVED_UNKNOWN", 0),
        ("STALE", 0),
    ],
)
def test_matrix_resolution_cardinality(repo_root, resolution, expected_count):
    _, matrix, _ = build_slot_matrix(repo_root)
    assert matrix["resolution_counts"][resolution] == expected_count


@pytest.mark.parametrize(
    ("kinds", "expected"),
    [
        (["ELIGIBLE_SUCCESS"], "RESOLVED_ELIGIBLE_SUCCESS"),
        (["VALID_OUTPUT_ORACLE_FAIL"], "RESOLVED_TERMINAL_NEGATIVE"),
        (["TERMINAL_POLICY_FAILURE"], "RESOLVED_TERMINAL_NEGATIVE"),
        (["HARNESS_CENSORED"], "CENSORED_HARNESS"),
        (["INFRASTRUCTURE_CENSORED"], "CENSORED_INFRASTRUCTURE"),
        (["UNKNOWN_CENSORED"], "UNRESOLVED_UNKNOWN"),
    ],
)
def test_resolution_precedence_is_fail_closed(kinds, expected):
    records = [{"primary_classification": value} for value in kinds]
    assert _resolution(records)[0] == expected


def test_slot_matrix_accounts_for_all_attempts_exactly_once(repo_root):
    records, matrix, _ = build_slot_matrix(repo_root)
    attempts = [attempt_id for item in records for attempt_id in item["all_attempt_ids"]]
    assert len(attempts) == len(set(attempts)) == 28
    assert len(records) == len({item["slot_id"] for item in records}) == 24
    assert matrix["all_attempts_accounted"] is True


def test_earliest_eligible_is_the_only_quality_selection(repo_root):
    records, matrix, _ = build_slot_matrix(repo_root)
    assert all(
        item["selected_quality_record_id"] == item["first_eligible_success_id"] for item in records
    )
    assert matrix["earliest_eligible_selection"] is True
    assert matrix["best_of_n_prohibited"] is True


def test_first_completion_is_distinct_from_first_eligible(repo_root):
    records, _, _ = build_slot_matrix(repo_root)
    item = next(value for value in records if value["slot_id"] == "CASE-001-ARM-A-R2")
    assert item["first_completion_id"] == "EXP-CASE-001-ARM-A-R2-A01"
    assert item["first_eligible_success_id"] is None
    assert item["selected_quality_record_id"] is None


@pytest.mark.parametrize(
    ("slot_id", "retry_count"),
    [
        ("CASE-001-ARM-A-R2", 2),
        ("CASE-004-ARM-A-R2", 1),
        ("CASE-006-ARM-A-R1", 1),
    ],
)
def test_retry_burden_is_bound_to_slot(repo_root, slot_id, retry_count):
    records, _, _ = build_slot_matrix(repo_root)
    item = next(value for value in records if value["slot_id"] == slot_id)
    assert item["retry_count"] == retry_count
    assert item["attempt_count"] == retry_count + 1


def test_harness_censored_slot_retains_mixed_infrastructure_evidence(repo_root):
    records, _, _ = build_slot_matrix(repo_root)
    item = next(value for value in records if value["slot_id"] == "CASE-001-ARM-A-R2")
    assert item["outcome_resolution"] == "CENSORED_HARNESS"
    assert len(item["harness_failure_ids"]) == 2
    assert len(item["infrastructure_failure_ids"]) == 1
    assert item["unresolved_reason"] == "HARNESS_SEMANTIC_EQUIVALENCE_NOT_ESTABLISHED"


def test_all_slot_records_validate_against_contract(repo_root):
    records, matrix, _ = build_slot_matrix(repo_root)
    slot_schema = read_json(repo_root / "contracts/slot_outcome.schema.json")
    matrix_schema = read_json(repo_root / "contracts/slot_outcome_matrix.schema.json")
    assert all(not list(Draft202012Validator(slot_schema).iter_errors(item)) for item in records)
    Draft202012Validator(matrix_schema).validate(matrix)


def test_csv_projection_has_one_row_per_slot(repo_root):
    records, _, csv_text = build_slot_matrix(repo_root)
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(rows) == len(records) == 24
    assert {item["slot_id"] for item in rows} == set(EXPECTED_SLOTS)


def test_generated_matrix_matches_replay(repo_root):
    result = check_or_write_slot_matrix(repo_root, check=True)
    assert result["status"] == "PASS"
    assert result["errors"] == []
    assert result["slot_count"] == 24
