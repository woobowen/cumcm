from copy import deepcopy

from cumcm_skill_lab.expansion.models import read_json
from cumcm_skill_lab.expansion.score_audit import (
    build_score_audit,
    validate_score_audit,
)


def _batch_one(repo_root):
    return read_json(repo_root / "evals/results/phase-002d/score_audit/batches/batch-001.json")


def test_batch_one_score_audit_preserves_authoritative_attempt_binding(repo_root):
    audit = _batch_one(repo_root)
    assert validate_score_audit(audit) == []
    assert audit["authoritative_attempt_binding_pass"] is True
    assert audit["coverage_binding_mismatch_count"] == 1
    assert audit["status"] == "PASS_WITH_COVERAGE_LIMITATION"


def test_coverage_binding_mismatch_is_isolated_to_arm_a(repo_root):
    audit = _batch_one(repo_root)
    mismatches = [record for record in audit["records"] if record["coverage_binding_mismatch"]]
    assert [record["anonymous_arm_id"] for record in mismatches] == ["ARM-A"]
    assert mismatches[0]["coverage_hard_failures"] == ["HARD-FAIL-003"]
    assert mismatches[0]["attempt_hard_failures"] == []
    assert mismatches[0]["recomputed_hard_failures"] == []


def test_coverage_is_never_promoted_to_hard_gate(repo_root):
    audit = _batch_one(repo_root)
    assert audit["coverage_excluded_from_hard_gates"] is True
    assert all(record["coverage_is_hard_gate_source"] is False for record in audit["records"])
    assert all(record["coverage_proves_correctness"] is False for record in audit["records"])


def test_original_scores_are_retained(repo_root):
    audit = _batch_one(repo_root)
    assert audit["original_scores_modified"] is False
    assert all(len(record["coverage_hash"]) == 64 for record in audit["records"])


def test_score_audit_hash_mutation_fails_closed(repo_root):
    audit = _batch_one(repo_root)
    mutated = deepcopy(audit)
    mutated["audit_hash"] = "0" * 64
    assert "SCORE_AUDIT_HASH_MISMATCH" in validate_score_audit(mutated)


def test_authoritative_binding_failure_is_blocking(repo_root):
    audit = _batch_one(repo_root)
    mutated = deepcopy(audit)
    mutated["authoritative_attempt_binding_pass"] = False
    assert "AUTHORITATIVE_ATTEMPT_BINDING_FAILED" in validate_score_audit(mutated)


def test_current_score_audit_rebuilds_from_all_append_only_attempts(repo_root):
    current = read_json(repo_root / "evals/results/phase-002d/score_audit/audit.json")
    rebuilt = build_score_audit(
        repo_root,
        batch_id=current["batch_id"],
        audited_at=current["audited_at"],
    )
    assert rebuilt == current


def test_failed_attempts_without_observations_are_explicitly_noncomparable(repo_root):
    current = read_json(repo_root / "evals/results/phase-002d/score_audit/audit.json")
    records = [
        record
        for record in current["records"]
        if record["classification"] == "NOT_APPLICABLE_NO_OBSERVATION"
    ]
    assert current["noncomparable_no_observation_count"] == 3
    assert len(records) == 3
    assert all(record["observation_available"] is False for record in records)
    assert all(record["authoritative_match"] is None for record in records)
    assert all(record["coverage_binding_mismatch"] is None for record in records)
    assert all(record["coverage_is_hard_gate_source"] is False for record in records)
