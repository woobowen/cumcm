import pytest
from jsonschema import Draft202012Validator

from cumcm_skill_lab.failure_aware.evidence_scopes import (
    build_evidence_scope_summary,
    check_or_write_evidence_scopes,
)
from cumcm_skill_lab.failure_aware.models import read_json
from cumcm_skill_lab.failure_aware.retry_bias import (
    build_retry_bias_audit,
    check_or_write_retry_bias,
)


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        ("attempt_count", 28),
        ("slot_count", 24),
        ("completion_rate", 0.714285714),
        ("primary_eligible_rate", 0.642857143),
        ("terminal_failure_rate", 0.571428571),
        ("policy_violation_rate", 0.25),
        ("infrastructure_rate", 0.035714286),
        ("retry_burden", 4),
    ],
)
def test_reliability_scope_uses_all_attempts(repo_root, metric, expected):
    summary = build_evidence_scope_summary(repo_root)
    assert summary["reliability_evidence"][metric] == expected


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        ("balanced_case_count", 2),
        ("minimum_repeat_depth", 1),
        ("required_balanced_cases", 4),
        ("required_repeat_depth", 2),
        ("result", "EVIDENCE_INSUFFICIENT"),
    ],
)
def test_quality_scope_preserves_original_gate(repo_root, metric, expected):
    summary = build_evidence_scope_summary(repo_root)
    assert summary["quality_evidence"][metric] == expected


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        ("resolved_slot_count", 23),
        ("resolved_success_slots", 9),
        ("resolved_terminal_negative_slots", 14),
        ("resolved_case_count", 3),
        ("minimum_repeat_depth", 2),
    ],
)
def test_outcome_completeness_is_not_quality_sufficiency(repo_root, metric, expected):
    summary = build_evidence_scope_summary(repo_root)
    assert summary["outcome_completeness"][metric] == expected


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        ("quality_balanced_case_count", 2),
        ("quality_minimum_repeat_depth", 1),
        ("outcome_resolved_case_count", 3),
        ("outcome_minimum_repeat_depth", 2),
        ("schedule_attempted_repeat_depth", 2),
        ("reliability_observed_repeat_depth", 2),
    ],
)
def test_repeat_depth_has_explicit_scope(repo_root, metric, expected):
    summary = build_evidence_scope_summary(repo_root)
    assert summary["repeat_semantics"][metric] == expected
    assert summary["repeat_semantics"]["repeat_depth_deprecated"] is True


def test_component_gaps_require_repetition(repo_root):
    summary = build_evidence_scope_summary(repo_root)
    groups = summary["component_gap_evidence"]["eligible_gap_groups"]
    assert {item["gap_id"] for item in groups} == {
        "REPEATED_ORACLE_CORRECTNESS_GAP",
        "REPEATED_POLICY_COMPLIANCE_GAP",
    }
    assert all(len(item["attempt_ids"]) >= 2 for item in groups)
    assert all(len(item["case_ids"]) >= 2 or len(item["repeat_ids"]) >= 2 for item in groups)


def test_component_gap_scope_excludes_invalid_inputs(repo_root):
    component = build_evidence_scope_summary(repo_root)["component_gap_evidence"]
    assert component["infrastructure_excluded"] is True
    assert component["recovery_excluded"] is True
    assert component["agent_votes_excluded"] is True


def test_failures_are_never_imputed_as_zero_scores(repo_root):
    summary = build_evidence_scope_summary(repo_root)
    audit = build_retry_bias_audit(repo_root)
    assert summary["failure_is_not_zero_score"] is True
    assert audit["failure_zero_imputation"] is False


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("retry_burden", 4),
        ("success_after_retry", []),
        ("terminal_failure_before_success", []),
        ("primary_eligible_after_retry", ["CASE-004-ARM-A-R2"]),
        ("earliest_eligible_enforced", True),
        ("best_of_n_prohibited", True),
        ("previous_failures_retained", True),
        ("later_success_erases_failure", False),
        ("posthoc_budget_expansion", False),
        ("per_cell_cap_respected", True),
        ("all_attempts_in_cost", True),
    ],
)
def test_retry_audit_preserves_failure_and_budget_semantics(repo_root, field, expected):
    audit = build_retry_bias_audit(repo_root)
    assert audit[field] == expected


def test_attempt_to_first_eligible_has_no_quality_claim(repo_root):
    audit = build_retry_bias_audit(repo_root)
    item = next(
        value
        for value in audit["attempt_to_first_eligible"]
        if value["slot_id"] == "CASE-004-ARM-A-R2"
    )
    assert item["attempt_number"] == 2
    assert item["attempt_id"] == "EXP-CASE-004-ARM-A-R2-A02"
    assert "CASE-004-ARM-A-R2" not in audit["success_after_retry"]


def test_scope_and_retry_artifacts_validate_against_contracts(repo_root):
    summary = build_evidence_scope_summary(repo_root)
    audit = build_retry_bias_audit(repo_root)
    summary_schema = read_json(repo_root / "contracts/evidence_scope_summary.schema.json")
    audit_schema = read_json(repo_root / "contracts/retry_bias_audit.schema.json")
    Draft202012Validator(summary_schema).validate(summary)
    Draft202012Validator(audit_schema).validate(audit)


def test_scope_and_retry_generated_files_match_replay(repo_root):
    scopes = check_or_write_evidence_scopes(repo_root, check=True)
    retry = check_or_write_retry_bias(repo_root, check=True)
    assert scopes["status"] == retry["status"] == "PASS"
    assert scopes["errors"] == retry["errors"] == []
