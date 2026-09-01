from copy import deepcopy

import pytest

from cumcm_skill_lab.failure_aware.decision_audit import build_decision_audit
from cumcm_skill_lab.failure_aware.decisions import (
    DECISION_FILES,
    apply_team_compliance_review,
    evaluate_architecture_gate,
    validate_decisions,
)
from cumcm_skill_lab.failure_aware.models import read_json


def test_decision_audit_passes_all_mechanical_checks(repo_root):
    audit = build_decision_audit(repo_root)
    assert audit["result"] == "PASS"
    assert len(audit["checks"]) >= 18
    assert all(audit["checks"].values())
    assert audit["blockers"] == []


def test_decision_audit_is_independent_and_nonvoting(repo_root):
    audit = build_decision_audit(repo_root)
    assert audit["independent"] is True
    assert audit["majority_vote_used"] is False
    assert audit["human_technical_gate_used"] is False
    assert audit["recovery_ranked"] is False


def test_decision_audit_covers_exact_seven_decisions(repo_root):
    audit = build_decision_audit(repo_root)
    assert set(audit["decision_ids"]) == set(DECISION_FILES)


def test_architecture_gate_can_reject_all_or_abstain():
    assert (
        evaluate_architecture_gate(
            freeze_valid=False, quality_sufficient=False, posthoc_policy=True
        )["decision"]
        == "AUTOMATED_REJECTED"
    )
    assert (
        evaluate_architecture_gate(freeze_valid=True, quality_sufficient=True, posthoc_policy=True)[
            "decision"
        ]
        == "AUTOMATED_ABSTAINED"
    )


def test_team_compliance_cannot_override_technical_decision():
    with pytest.raises(ValueError, match="TEAM_COMPLIANCE_CANNOT_OVERRIDE"):
        apply_team_compliance_review("AUTOMATED_REJECTED", "AUTOMATED_ACCEPTED")


def test_decision_set_rejects_duplicate_identity(repo_root):
    decisions = [
        read_json(repo_root / "evals/results/phase-002d-r1/automated_decisions" / filename)
        for filename in DECISION_FILES.values()
    ]
    decisions[-1] = deepcopy(decisions[0])
    assert "FAILURE_AWARE_DECISION_SET_MISMATCH" in validate_decisions(repo_root, decisions)


def test_architecture_is_not_selected_by_reliability(repo_root):
    audit = build_decision_audit(repo_root)
    assert audit["checks"]["quality_insufficient_and_unaccepted"] is True
    assert audit["checks"]["reliability_accepted_only"] is True
    assert audit["checks"]["architecture_not_selected"] is True


def test_component_acceptance_is_specification_only(repo_root):
    audit = build_decision_audit(repo_root)
    assert audit["checks"]["component_scope_specification_only"] is True


def test_decision_audit_requires_stable_replay(repo_root):
    audit = build_decision_audit(repo_root)
    assert audit["checks"]["offline_replay_stable"] is True
    assert audit["replayable"] is True


def test_decision_audit_routes_only_to_phase002d(repo_root):
    audit = build_decision_audit(repo_root)
    assert audit["checks"]["next_phase_route_is_phase002d"] is True
