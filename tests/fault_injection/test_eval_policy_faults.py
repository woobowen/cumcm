"""Cross-layer fail-closed cases not tied to a real network or third-party runtime."""

import copy
import json

import pytest
from jsonschema import Draft202012Validator

from cumcm_skill_lab.eval.anonymization import assert_identity_free
from cumcm_skill_lab.eval.safety import inspect_source_entry
from cumcm_skill_lab.eval.scoring import score_observation


def _observation(repo_root):
    return json.loads(
        (repo_root / "tests/fixtures/contracts/valid/eval_observation.json").read_text()
    )


def _rubric(repo_root):
    return json.loads((repo_root / "evals/rubrics/phase-002/CASE-001.json").read_text())


@pytest.mark.parametrize(
    ("path", "mode"),
    [("candidate.py", "100644"), ("candidate.sh", "100644"), ("instructions.md", "100755")],
)
def test_candidate_package_code_or_executable_fails_closed(path, mode):
    assert inspect_source_entry(path, mode, b"synthetic")


def test_candidate_identity_in_blind_input_fails_closed():
    with pytest.raises(RuntimeError, match="ANONYMIZATION_IDENTITY_LEAK"):
        assert_identity_free({"review": "candidate-x"}, ["candidate-x"])


def test_candidate_label_cannot_change_grade_or_original_output(repo_root):
    first = _observation(repo_root)
    second = copy.deepcopy(first)
    before = copy.deepcopy(first)
    first["self_reported_limitations"].append("arm flavor one")
    second["self_reported_limitations"].append("arm flavor two")
    score_one = score_observation(first, _rubric(repo_root))
    score_two = score_observation(second, _rubric(repo_root))
    assert score_one["deterministic_score"] == score_two["deterministic_score"]
    before["self_reported_limitations"].append("arm flavor one")
    assert first == before


def test_human_gate_and_integration_flags_remain_false(repo_root):
    state = json.loads((repo_root / "state/project_state.json").read_text())
    schema = json.loads((repo_root / "contracts/project_state.schema.json").read_text())
    Draft202012Validator(schema).validate(state)
    legal_statuses = set(schema["properties"]["technical_adjudication_status"]["enum"])
    assert not any("HUMAN" in blocker for blocker in state["blockers"])
    assert any("CONNECT_RESET" in risk.upper() for risk in state["risks"])
    assert state["technical_adjudication_status"] in legal_statuses
    if state["technical_adjudication_status"] in {
        "AUTOMATED_ADJUDICATION_COMPLETE",
        "FAILURE_AWARE_ADJUDICATION_COMPLETE",
    }:
        assert state["automated_decision_ids"]
        assert state["next_phase_allowed"] in {
            "PHASE-EVIDENCE-EXPANSION-002D",
            "PHASE-SKILL-INTEGRATION-003",
        }
        if state["technical_adjudication_status"] == "FAILURE_AWARE_ADJUDICATION_COMPLETE":
            assert state["next_phase_allowed"] == "PHASE-EVIDENCE-EXPANSION-002D"
            assert state["selected_architecture"] is None
            assert state["accepted_component_specifications"]
    elif state["technical_adjudication_status"] == "EVIDENCE_EXPANSION_INCOMPLETE":
        assert state["next_phase_allowed"] == "PHASE-EVIDENCE-EXPANSION-002D"
    elif state["technical_adjudication_status"] == "FAILURE_AWARE_ADJUDICATION_IN_PROGRESS":
        assert state["subphase"] == "PHASE-002D-R1-FAILURE-AWARE-OUTCOME-ADJUDICATION"
        assert state["selected_architecture"] is None
        assert state["accepted_component_specifications"] == []
        assert not any(decision.endswith("002D-R1") for decision in state["automated_decision_ids"])
        assert state["next_phase_allowed"] is None
    elif state["technical_adjudication_status"] == "SPECIFICATION_PROTOCOL_COMPLETE":
        assert state["selected_architecture"] is None
        assert len(state["architecture_candidate_set"]) in {2, 3}
        assert state["next_phase_allowed"] in {
            "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL",
            "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION",
            None,
        }
    elif state["technical_adjudication_status"] == "SHADOW_PROTOTYPE_AUTHORIZATION_COMPLETE":
        shadow = state["shadow_authorization"]
        assert state["next_phase_allowed"] == "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"
        assert shadow["active_decision_id"] in state["automated_decision_ids"]
        assert shadow["final_audit_result"] == "PASS"
        assert shadow["final_replay_stable"] is True
    elif state["technical_adjudication_status"] == "COMPETITION_SKILL_RC_READY":
        assert state["subphase"] == "COMPETITION-RC1-REPAIR-AND-INTEGRATION"
        assert state["next_phase_allowed"] == "PHASE-SKILL-DEVELOPMENT-EVAL-004"
        assert state["selected_architecture"] == (
            "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
        )
        assert state["active_skill_version"] == "0.2.0-competition-rc1"
    elif state["technical_adjudication_status"] == "DEVELOPMENT_EVAL_RC2_READY":
        assert state["subphase"] == "CUMCM-2023-C-DEVELOPMENT-RC2"
        assert state["next_phase_allowed"] == "PHASE-SKILL-DEVELOPMENT-EVAL-004-B"
        assert state["development_eval"]["stress_statuses"] == {
            "A": "PASS",
            "B": "PASS",
            "C": "PASS",
        }
        assert state["active_skill_version"] == "0.2.0-competition-rc2"
    elif state["technical_adjudication_status"] == "DEVELOPMENT_EVAL_RC3_READY":
        assert state["subphase"] == "CUMCM-2020-A-DEVELOPMENT-RC3"
        assert state["next_phase_allowed"] == "PHASE-SKILL-VALIDATION-EVAL-004-C"
        assert state["development_eval"]["stress_statuses"] == {
            "A": "PASS",
            "B": "PASS",
            "C": "PASS",
        }
        assert state["active_skill_version"] == "0.2.0-competition-rc3"
    elif state["technical_adjudication_status"] == "C_TARGET_BATCH_IN_PROGRESS":
        assert state["subphase"] == "C-TARGET-STRATEGY-MIGRATION-AND-BATCH-FIRST-RUNS"
        assert state["primary_target_problem_type"] == "C"
        assert state["current_batch_id"] == "C-TARGET-BATCH-001"
        assert state["batch_skill_frozen"] is True
        assert state["batch_reference_unlocked"] is False
        assert state["next_phase_allowed"] is None
        assert state["active_skill_version"] == "0.2.0-competition-rc3"
    elif state["technical_adjudication_status"] == "C_TARGET_BATCH_POSTMORTEM_IN_PROGRESS":
        assert state["subphase"] == "C-TARGET-UNIFIED-REFERENCE-REVIEW-AND-POSTMORTEM"
        assert state["primary_target_problem_type"] == "C"
        assert state["current_batch_id"] == "C-TARGET-BATCH-001"
        assert state["batch_skill_frozen"] is True
        assert state["batch_reference_unlocked"] is True
        assert state["next_phase_allowed"] is None
        assert state["active_skill_version"] == "0.2.0-competition-rc3"
    elif state["technical_adjudication_status"] == "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT":
        assert state["subphase"] == "C-TARGET-2024C-VALIDATION-TERMINAL-EVIDENCE-INSUFFICIENT"
        assert state["primary_target_problem_type"] == "C"
        assert state["current_batch_id"] == "C-TARGET-BATCH-001"
        assert state["batch_skill_frozen"] is True
        assert state["batch_reference_unlocked"] is True
        assert state["next_phase_allowed"] == "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2"
        assert state["active_skill_version"] == "0.2.0-competition-rc4"
        assert state["blockers"] == ["RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID"]
    else:
        assert state["next_phase_allowed"] is None
    assert state["base_selected"] is False
    assert state["third_party_integrated"] is False
    expected_capability = (
        "COMPETITION_RC"
        if state["phase"]
        in {
            "PHASE-SKILL-INTEGRATION-003",
            "PHASE-SKILL-DEVELOPMENT-EVAL-004",
            "PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C",
            "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2",
        }
        else "SCAFFOLD_ONLY"
    )
    assert state["skill_capability_status"] == expected_capability
