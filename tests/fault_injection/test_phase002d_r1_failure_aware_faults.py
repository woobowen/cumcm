from copy import deepcopy

from jsonschema import Draft202012Validator

from cumcm_skill_lab.failure_aware import classification as classification_module
from cumcm_skill_lab.failure_aware.classification import classify_attempt
from cumcm_skill_lab.failure_aware.models import read_json
from cumcm_skill_lab.failure_aware.retry_bias import (
    _cost_reconciliation,
    build_retry_bias_audit,
)
from cumcm_skill_lab.failure_aware.slot_matrix import _resolution
from cumcm_skill_lab.failure_aware.supplemental import harness_semantic_equivalence


def _classified(primary: str) -> dict[str, str]:
    return {"primary_classification": primary}


def test_terminal_before_success_cannot_be_quality_selected():
    sequence = [
        _classified("TERMINAL_POLICY_FAILURE"),
        _classified("ELIGIBLE_SUCCESS"),
    ]
    assert _resolution(sequence) == (
        "RESOLVED_TERMINAL_NEGATIVE",
        "POLICY_FAILURE",
        None,
    )


def test_first_terminal_subtype_cannot_be_erased_by_later_oracle_failure():
    sequence = [
        _classified("TERMINAL_POLICY_FAILURE"),
        _classified("VALID_OUTPUT_ORACLE_FAIL"),
    ]
    assert _resolution(sequence)[1] == "POLICY_FAILURE"


def test_exact_cost_reconciliation_rejects_count_preserving_mutation(repo_root):
    ledger = classification_module.read_json(
        repo_root / "evals/results/phase-002d/attempt_ledger.json"
    )
    attempts = [
        classification_module.read_json(
            repo_root / f"evals/results/phase-002d/attempts/{attempt_id}.json"
        )
        for attempt_id in ledger["attempt_ids"]
    ]
    cost = classification_module.read_json(repo_root / "evals/results/phase-002d/cost/cost.json")
    mutated = deepcopy(attempts)
    mutated[0]["input_tokens"] += 1
    mutated[1]["input_tokens"] -= 1
    mutated[0]["duration_seconds"] += 0.001
    result = _cost_reconciliation(mutated, cost)
    assert result["recomputed"]["attempts"] == result["recorded"]["attempts"]
    assert result["recomputed"]["input_tokens"] == result["recorded"]["input_tokens"]
    assert result["exact_match"] is False


def test_policy_attribution_requires_authoritative_runner_label(repo_root, monkeypatch):
    attempt_id = "EXP-CASE-006-ARM-B-R2-A01"
    original_read_json = classification_module.read_json

    def mutated_read_json(path):
        value = original_read_json(path)
        if path.as_posix().endswith(f"attempts/{attempt_id}.json"):
            value = deepcopy(value)
            value["failure_class"] = "NONE"
        return value

    monkeypatch.setattr(classification_module, "read_json", mutated_read_json)
    record = classify_attempt(repo_root, attempt_id)
    assert record["primary_classification"] != "TERMINAL_POLICY_FAILURE"
    assert record["attribution_basis"] != "RUNNER_POLICY_TERMINAL"


def test_mixed_transport_attribution_retains_secondary_uncertainty(repo_root):
    attempt_id = "EXP-CASE-001-ARM-A-R2-A02"
    record = classify_attempt(repo_root, attempt_id)
    assert record["primary_classification"] == "INFRASTRUCTURE_CENSORED"
    assert record["confidence"] == "MEDIUM"
    assert {
        "TRANSPORT_FAILURE_RECORDED",
        "HARD_FAIL_003_RECORDED",
        "PROCESS_EVIDENCE_FAIL",
    }.issubset(record["secondary_flags"])


def test_transport_primary_requires_authoritative_failure_label(repo_root, monkeypatch):
    attempt_id = "EXP-CASE-001-ARM-A-R2-A02"
    original_read_json = classification_module.read_json

    def mutated_read_json(path):
        value = original_read_json(path)
        if path.as_posix().endswith(f"attempts/{attempt_id}.json"):
            value = deepcopy(value)
            value["failure_class"] = "NONE"
        return value

    monkeypatch.setattr(classification_module, "read_json", mutated_read_json)
    record = classify_attempt(repo_root, attempt_id)
    assert record["primary_classification"] != "INFRASTRUCTURE_CENSORED"
    assert "HARD_FAIL_003_RECORDED" in record["secondary_flags"]


def test_harness_semantic_equivalence_fails_closed_without_bound_files(repo_root):
    result = harness_semantic_equivalence(repo_root)
    assert result["status"] == "NOT_ESTABLISHED"
    assert result["bound_file_hashes"] == []
    assert result["semantic_equivalence_pass"] is False
    assert result["supplemental_eligible"] is False


def test_retry_control_mutations_fail_closed(repo_root):
    audit = build_retry_bias_audit(repo_root)
    schema = read_json(repo_root / "contracts/retry_bias_audit.schema.json")
    validator = Draft202012Validator(schema)
    mutations = (
        ("earliest_eligible_enforced", False),
        ("best_of_n_prohibited", False),
        ("previous_failures_retained", False),
        ("later_success_erases_failure", True),
        ("failure_zero_imputation", True),
    )
    for field, value in mutations:
        mutated = deepcopy(audit)
        mutated[field] = value
        assert list(validator.iter_errors(mutated)), field

    deleted = deepcopy(audit)
    del deleted["previous_failures_retained"]
    assert list(validator.iter_errors(deleted))
