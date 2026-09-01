import pytest
from jsonschema import Draft202012Validator

from cumcm_skill_lab.failure_aware.decisions import (
    ARCHITECTURE_CANDIDATES,
    DECISION_FILES,
    apply_team_compliance_review,
    build_decisions,
    build_sufficiency_records,
    evaluate_architecture_gate,
    validate_decisions,
)
from cumcm_skill_lab.failure_aware.models import read_json


def _by_id(repo_root):
    return {item["automated_decision"]["decision_id"]: item for item in build_decisions(repo_root)}


def test_all_seven_required_decisions_are_generated(repo_root):
    decisions = build_decisions(repo_root)
    assert len(decisions) == 7
    assert {item["automated_decision"]["decision_id"] for item in decisions} == set(DECISION_FILES)


@pytest.mark.parametrize(
    ("decision_id", "decision", "accepted_scope"),
    [
        ("DECISION-FAILURE-SEMANTICS-002D-R1", "AUTOMATED_ACCEPTED", "POLICY_ONLY"),
        ("DECISION-SLOT-RESOLUTION-002D-R1", "AUTOMATED_ACCEPTED", "POLICY_ONLY"),
        (
            "DECISION-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1",
            "AUTOMATED_REJECTED",
            "NONE",
        ),
        (
            "DECISION-QUALITY-EVIDENCE-SUFFICIENCY-002D-R1",
            "EVIDENCE_INSUFFICIENT",
            "NONE",
        ),
        (
            "DECISION-RELIABILITY-EVIDENCE-SUFFICIENCY-002D-R1",
            "AUTOMATED_ACCEPTED",
            "RELIABILITY_ONLY",
        ),
        ("DECISION-ARCHITECTURE-002D-R1", "EVIDENCE_INSUFFICIENT", "NONE"),
        (
            "DECISION-COMPONENT-READINESS-002D-R1",
            "AUTOMATED_ACCEPTED",
            "SPECIFICATION_ONLY",
        ),
    ],
)
def test_decision_and_scope_are_separated(repo_root, decision_id, decision, accepted_scope):
    item = _by_id(repo_root)[decision_id]
    assert item["automated_decision"]["decision"] == decision
    assert item["accepted_scope"] == accepted_scope


def test_quality_insufficient_but_reliability_sufficient(repo_root):
    quality, reliability = build_sufficiency_records(repo_root)
    assert quality["result"] == "EVIDENCE_INSUFFICIENT"
    assert reliability["result"] == "SUFFICIENT_RELIABILITY_ONLY"
    assert reliability["quality_claim_allowed"] is False
    assert reliability["performance_superiority_claim_allowed"] is False


def test_architecture_is_not_selected_from_posthoc_policy(repo_root):
    architecture = _by_id(repo_root)["DECISION-ARCHITECTURE-002D-R1"]
    core = architecture["automated_decision"]
    assert core["target_ids"] == ["RETAIN_SCAFFOLD_ONLY"]
    assert core["decision"] == "EVIDENCE_INSUFFICIENT"
    assert "NATIVE_SINGLE_SKILL_CLEAN_ROOM" in core["rejected_scope"]
    assert architecture["positive_performance_superiority_claim_allowed"] is False


def test_components_are_specification_only(repo_root):
    components = _by_id(repo_root)["DECISION-COMPONENT-READINESS-002D-R1"]
    core = components["automated_decision"]
    assert len(core["component_results"]) == 4
    assert all(item["accepted_scope"] == "SPECIFICATION_ONLY" for item in core["component_results"])
    assert {"DIRECT_REUSE", "IMPLEMENTATION_READY", "PRODUCTION_READY", "INTEGRATED"}.issubset(
        core["rejected_scope"]
    )


def test_decisions_use_canonical_automated_contract_and_validate(repo_root):
    decisions = build_decisions(repo_root)
    assert validate_decisions(repo_root, decisions) == []
    core_schema = read_json(repo_root / "contracts/automated_decision.schema.json")
    envelope_schema = read_json(repo_root / "contracts/failure_aware_decision.schema.json")
    for item in decisions:
        Draft202012Validator(core_schema).validate(item["automated_decision"])
        Draft202012Validator(envelope_schema).validate(item)
        assert item["automated_decision_contract"] == "contracts/automated_decision.schema.json"


def test_no_vote_human_gate_recovery_or_identity_enters_decisions(repo_root):
    for item in build_decisions(repo_root):
        assert item["majority_vote_used"] is False
        assert item["human_technical_gate_used"] is False
        assert item["recovery_ranked"] is False
        assert item["identity_used"] is False
        assert item["terminal_negative_zero_imputed"] is False
        assert item["automated_decision"]["judge_decisions"] == []


def test_all_decisions_route_only_back_to_evidence_expansion(repo_root):
    assert {
        item["automated_decision"]["next_phase_allowed"] for item in build_decisions(repo_root)
    } == {"PHASE-EVIDENCE-EXPANSION-002D"}


def test_system_can_reject_all_architecture_candidates():
    result = evaluate_architecture_gate(
        freeze_valid=False, quality_sufficient=True, posthoc_policy=False
    )
    assert result["decision"] == "AUTOMATED_REJECTED"
    assert result["rejected_candidates"] == list(ARCHITECTURE_CANDIDATES)


def test_system_can_abstain_from_posthoc_architecture_selection():
    result = evaluate_architecture_gate(
        freeze_valid=True, quality_sufficient=True, posthoc_policy=True
    )
    assert result["decision"] == "AUTOMATED_ABSTAINED"
    assert result["reason"] == "POSTHOC_POLICY_CANNOT_SELECT_ARCHITECTURE"


def test_team_compliance_review_cannot_override_technical_rejection():
    with pytest.raises(ValueError, match="TEAM_COMPLIANCE_CANNOT_OVERRIDE"):
        apply_team_compliance_review("AUTOMATED_REJECTED", "AUTOMATED_ACCEPTED")
    assert apply_team_compliance_review("AUTOMATED_REJECTED", None) == "AUTOMATED_REJECTED"
