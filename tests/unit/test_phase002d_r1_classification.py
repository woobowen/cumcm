from collections import Counter

import pytest
from jsonschema import Draft202012Validator

from cumcm_skill_lab.failure_aware.classification import (
    build_classifications,
    check_or_write_classifications,
)
from cumcm_skill_lab.failure_aware.models import read_json

EXPECTED_CLASSIFICATIONS = {
    "EXP-CASE-001-ARM-A-R1-A01": "ELIGIBLE_SUCCESS",
    "EXP-CASE-001-ARM-A-R2-A01": "HARNESS_CENSORED",
    "EXP-CASE-001-ARM-A-R2-A02": "INFRASTRUCTURE_CENSORED",
    "EXP-CASE-001-ARM-A-R2-A03": "HARNESS_CENSORED",
    "EXP-CASE-001-ARM-B-R1-A01": "VALID_OUTPUT_ORACLE_FAIL",
    "EXP-CASE-001-ARM-B-R2-A01": "ELIGIBLE_SUCCESS",
    "EXP-CASE-001-ARM-C-R1-A01": "VALID_OUTPUT_ORACLE_FAIL",
    "EXP-CASE-001-ARM-C-R2-A01": "ELIGIBLE_SUCCESS",
    "EXP-CASE-002-ARM-A-R1-A01": "ELIGIBLE_SUCCESS",
    "EXP-CASE-002-ARM-A-R2-A01": "ELIGIBLE_SUCCESS",
    "EXP-CASE-002-ARM-B-R1-A01": "ELIGIBLE_SUCCESS",
    "EXP-CASE-002-ARM-B-R2-A01": "ELIGIBLE_SUCCESS",
    "EXP-CASE-002-ARM-C-R1-A01": "ELIGIBLE_SUCCESS",
    "EXP-CASE-002-ARM-C-R2-A01": "ELIGIBLE_SUCCESS",
    "EXP-CASE-004-ARM-A-R1-A01": "VALID_OUTPUT_ORACLE_FAIL",
    "EXP-CASE-004-ARM-A-R2-A01": "TERMINAL_POLICY_FAILURE",
    "EXP-CASE-004-ARM-A-R2-A02": "VALID_OUTPUT_ORACLE_FAIL",
    "EXP-CASE-004-ARM-B-R1-A01": "VALID_OUTPUT_ORACLE_FAIL",
    "EXP-CASE-004-ARM-B-R2-A01": "VALID_OUTPUT_ORACLE_FAIL",
    "EXP-CASE-004-ARM-C-R1-A01": "VALID_OUTPUT_ORACLE_FAIL",
    "EXP-CASE-004-ARM-C-R2-A01": "VALID_OUTPUT_ORACLE_FAIL",
    "EXP-CASE-006-ARM-A-R1-A01": "TERMINAL_POLICY_FAILURE",
    "EXP-CASE-006-ARM-A-R1-A02": "TERMINAL_POLICY_FAILURE",
    "EXP-CASE-006-ARM-A-R2-A01": "TERMINAL_POLICY_FAILURE",
    "EXP-CASE-006-ARM-B-R1-A01": "VALID_OUTPUT_ORACLE_FAIL",
    "EXP-CASE-006-ARM-B-R2-A01": "TERMINAL_POLICY_FAILURE",
    "EXP-CASE-006-ARM-C-R1-A01": "TERMINAL_POLICY_FAILURE",
    "EXP-CASE-006-ARM-C-R2-A01": "TERMINAL_POLICY_FAILURE",
}


@pytest.mark.parametrize(
    ("attempt_id", "expected"),
    EXPECTED_CLASSIFICATIONS.items(),
)
def test_each_frozen_attempt_has_expected_primary_classification(repo_root, attempt_id, expected):
    records, _ = build_classifications(repo_root)
    by_id = {item["attempt_id"]: item for item in records}
    assert by_id[attempt_id]["primary_classification"] == expected


@pytest.mark.parametrize(
    ("classification", "expected_count"),
    [
        ("ELIGIBLE_SUCCESS", 9),
        ("VALID_OUTPUT_ORACLE_FAIL", 9),
        ("TERMINAL_POLICY_FAILURE", 7),
        ("TERMINAL_MODEL_SCHEMA_FAILURE", 0),
        ("TERMINAL_UNSUPPORTED_CLAIM_FAILURE", 0),
        ("INFRASTRUCTURE_CENSORED", 1),
        ("HARNESS_CENSORED", 2),
        ("UNKNOWN_CENSORED", 0),
        ("SUPERSEDED", 0),
    ],
)
def test_classification_cardinality(repo_root, classification, expected_count):
    records, summary = build_classifications(repo_root)
    counts = Counter(item["primary_classification"] for item in records)
    assert counts[classification] == expected_count
    assert summary["classification_counts"][classification] == expected_count


def test_all_28_attempts_are_classified_once(repo_root):
    records, summary = build_classifications(repo_root)
    assert len(records) == len({item["attempt_id"] for item in records}) == 28
    assert set(EXPECTED_CLASSIFICATIONS) == {item["attempt_id"] for item in records}
    assert summary["all_attempts_accounted"] is True


def test_failure_attribution_is_identity_and_recovery_blind(repo_root):
    records, summary = build_classifications(repo_root)
    assert all(item["identity_used"] is False for item in records)
    assert all(item["recovery_used"] is False for item in records)
    assert summary["identity_used"] is False


def test_hard_fail_003_definition_and_attempts_are_preserved(repo_root):
    records, summary = build_classifications(repo_root)
    flagged = {
        item["attempt_id"]
        for item in records
        if "HARD_FAIL_003_RECORDED" in item["secondary_flags"]
    }
    assert flagged == set(summary["hard_fail_003_attempt_ids"])
    assert summary["hard_fail_003_definition"] == (
        "fabricated_run_source_file_metric_test_or_status"
    )
    assert flagged == {
        "EXP-CASE-001-ARM-A-R2-A01",
        "EXP-CASE-001-ARM-A-R2-A02",
        "EXP-CASE-001-ARM-A-R2-A03",
        "EXP-CASE-004-ARM-A-R2-A01",
        "EXP-CASE-006-ARM-A-R2-A01",
        "EXP-CASE-006-ARM-C-R1-A01",
    }


def test_infrastructure_is_primary_for_mixed_transport_attempt(repo_root):
    records, _ = build_classifications(repo_root)
    record = next(item for item in records if item["attempt_id"] == "EXP-CASE-001-ARM-A-R2-A02")
    assert record["primary_classification"] == "INFRASTRUCTURE_CENSORED"
    assert "TRANSPORT_FAILURE_RECORDED" in record["secondary_flags"]
    assert "HARD_FAIL_003_RECORDED" in record["secondary_flags"]
    assert record["confidence"] == "MEDIUM"


def test_completed_harness_mismatches_are_not_quality_eligible(repo_root):
    records, _ = build_classifications(repo_root)
    harness = [item for item in records if item["primary_classification"] == "HARNESS_CENSORED"]
    assert len(harness) == 2
    assert all(item["observed"]["completion_status"] == "COMPLETED" for item in harness)
    assert all(item["observed"]["primary_eligible"] is False for item in harness)
    assert all("HARNESS_PATH_CLAIM_MISMATCH" in item["secondary_flags"] for item in harness)


def test_every_classification_validates_against_contract(repo_root):
    records, _ = build_classifications(repo_root)
    schema = read_json(repo_root / "contracts/failure_classification.schema.json")
    validator = Draft202012Validator(schema)
    assert all(not list(validator.iter_errors(item)) for item in records)


def test_generated_classifications_match_replay(repo_root):
    result = check_or_write_classifications(repo_root, check=True)
    assert result["status"] == "PASS"
    assert result["errors"] == []
    assert result["attempt_count"] == 28
