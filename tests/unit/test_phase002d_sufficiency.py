from copy import deepcopy

from jsonschema import Draft202012Validator

from cumcm_skill_lab.expansion.models import read_json
from cumcm_skill_lab.expansion.sufficiency import (
    build_sufficiency,
    validate_sufficiency,
)


def _current(repo_root):
    return build_sufficiency(repo_root)


def test_terminal_phase002d_evidence_is_insufficient(repo_root):
    assert _current(repo_root)["result"] == "INSUFFICIENT"


def test_only_phase002d_primary_eligible_records_count(repo_root):
    value = _current(repo_root)
    assert value["actual"]["eligible_primary_count"] == 18


def test_balanced_case_minimum_fails_closed(repo_root):
    value = _current(repo_root)
    assert value["actual"]["balanced_cases"] == ["CASE-001", "CASE-002", "CASE-004"]
    assert value["conditions"]["balanced_case_minimum_met"] is False


def test_retry_attempts_do_not_inflate_independent_repeats(repo_root):
    value = _current(repo_root)
    assert value["actual"]["independent_repeats"] == 1
    assert value["actual"]["cell_repeat_counts"]["CASE-004"]["ARM-A"] == 2


def test_incomplete_case_cannot_be_balanced(repo_root):
    value = _current(repo_root)
    assert value["actual"]["cell_repeat_counts"]["CASE-006"] == {
        "ARM-A": 0,
        "ARM-B": 1,
        "ARM-C": 0,
    }
    assert "CASE-006" not in value["actual"]["balanced_cases"]


def test_task_input_hashes_are_consistent_per_case(repo_root):
    value = _current(repo_root)
    assert value["task_hash_consistency"]["passed"] is True
    assert value["task_hash_consistency"]["mismatched_cases"] == []


def test_eligible_evidence_hard_gates_pass(repo_root):
    value = _current(repo_root)
    assert value["conditions"]["frozen_evidence_valid"] is True
    assert value["conditions"]["mandatory_hard_gates_passed"] is True


def test_insufficiency_locks_semantic_audits_and_ranking(repo_root):
    value = _current(repo_root)
    assert value["semantic_judges_required"] is False
    assert value["ranking_allowed"] is False


def test_sufficiency_record_reuses_existing_contract(repo_root):
    value = _current(repo_root)
    schema = read_json(repo_root / "contracts/evidence_sufficiency.schema.json")
    Draft202012Validator(schema).validate(value)
    assert validate_sufficiency(repo_root, value) == []


def test_sufficiency_hash_mutation_fails_closed(repo_root):
    value = deepcopy(_current(repo_root))
    value["record_hash"] = "0" * 64
    assert "SUFFICIENCY_RECORD_HASH_MISMATCH" in validate_sufficiency(repo_root, value)


def test_insufficient_record_cannot_unlock_semantic_review(repo_root):
    value = deepcopy(_current(repo_root))
    value["semantic_judges_required"] = True
    assert "INSUFFICIENT_EVIDENCE_UNLOCKED_SEMANTIC_OR_RANKING" in validate_sufficiency(
        repo_root, value
    )


def test_reason_codes_name_both_frozen_minima(repo_root):
    assert _current(repo_root)["reason_codes"] == [
        "BALANCED_CASE_MINIMUM_NOT_MET",
        "MINIMUM_REPEATS_NOT_MET",
    ]
