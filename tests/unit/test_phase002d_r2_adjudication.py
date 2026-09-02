from copy import deepcopy

import pytest

from cumcm_skill_lab.specification.adjudication import (
    DECISION_FILES,
    SHADOW_DECISION_ID,
    build_decisions,
    validate_decisions,
)


def _by_id(root):
    return {item["automated_decision"]["decision_id"]: item for item in build_decisions(root)}


def test_decision_set_is_complete(repo_root):
    assert set(_by_id(repo_root)) == set(DECISION_FILES)


@pytest.mark.parametrize(
    ("decision_id", "phase_scope"),
    (
        ("DECISION-COMPONENT-SPECIFICATION-FREEZE-002D-R2", "SPECIFICATION_FROZEN"),
        ("DECISION-INTERACTION-CONTRACT-002D-R2", "SPECIFICATION_FROZEN"),
        ("DECISION-ARCHITECTURE-CANDIDATE-SET-002D-R2", "CANDIDATE_SET_FROZEN"),
        ("DECISION-PROSPECTIVE-BENCHMARK-FREEZE-002D-R2", "BENCHMARK_FROZEN"),
        ("DECISION-THRESHOLD-POLICY-FREEZE-002D-R2", "POLICY_FROZEN"),
    ),
)
def test_base_decision_scope_is_exact(repo_root, decision_id, phase_scope):
    value = _by_id(repo_root)[decision_id]
    assert value["automated_decision"]["decision"] == "AUTOMATED_ACCEPTED"
    assert value["phase_scope"] == phase_scope


def test_candidate_set_decision_does_not_select_architecture(repo_root):
    value = _by_id(repo_root)["DECISION-ARCHITECTURE-CANDIDATE-SET-002D-R2"]
    assert value["architecture_selected"] is False
    assert "ARCHITECTURE_SELECTION" in value["automated_decision"]["rejected_scope"]


def test_shadow_decision_fails_closed_before_audit_and_replay(repo_root):
    value = _by_id(repo_root)[SHADOW_DECISION_ID]
    assert value["automated_decision"]["decision"] == "RETEST_REQUIRED"
    assert value["phase_scope"] is None
    assert value["authorization"]["accepted_scope"] is None
    assert value["authorization"]["prerequisites"]["decision_auditor"] is False
    assert value["authorization"]["prerequisites"]["replay"] is False


def test_shadow_decision_never_routes_to_phase003(repo_root):
    value = _by_id(repo_root)[SHADOW_DECISION_ID]
    assert value["authorization"]["phase003_prohibited"] is True
    assert value["authorization"]["next_phase_allowed"] != "PHASE-SKILL-INTEGRATION-003"


@pytest.mark.parametrize("field", ("majority_vote_used", "human_technical_gate_used"))
def test_decisions_never_use_votes_or_human_technical_gate(repo_root, field):
    assert all(item[field] is False for item in build_decisions(repo_root))


def test_decision_hash_mutation_is_detected(repo_root):
    decisions = build_decisions(repo_root)
    mutated = deepcopy(decisions)
    mutated[0]["phase_scope"] = None
    assert any("HASH_MISMATCH" in item for item in validate_decisions(repo_root, mutated))


def test_all_current_decisions_validate(repo_root):
    assert validate_decisions(repo_root, build_decisions(repo_root)) == []
