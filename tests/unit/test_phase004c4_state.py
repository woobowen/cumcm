from __future__ import annotations

import copy
import json

import pytest
from jsonschema import Draft202012Validator, ValidationError


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_phase004c4_fresh_validation_state_is_schema_valid_and_preserves_blocked_history(
    repo_root,
) -> None:
    state = _load(repo_root / "state/project_state.json")
    schema = _load(repo_root / "contracts/project_state.schema.json")

    Draft202012Validator(schema).validate(state)
    assert state["schema_version"] == "2.4.0"
    assert state["phase"] == "PHASE-SKILL-C-TARGET-RUNTIME-PIPELINE-CLOSURE-004C4"
    assert state["subphase"] == "C-TARGET-FRESH-VALIDATION-TERMINAL"
    assert state["technical_adjudication_status"] == "C_TARGET_VALIDATION_FAILED"
    assert state["current_plan"] == (
        "plans/active/PLAN-0004C4-actual-controller-closure-and-fresh-validation.md"
    )
    assert state["active_skill_version"] == "0.2.0-competition-rc7"
    assert state["blocked_candidate_version"] == "0.2.0-competition-rc6"
    assert state["target_candidate_version"] == "0.2.0-competition-rc7"
    assert state["previous_validation_cases"] == [
        "CUMCM-2024-C-VALIDATION-001",
        "CUMCM-2019-C-VALIDATION-002",
    ]
    assert state["current_validation_case"] == "CUMCM-2017-C-VALIDATION-003F"
    assert state["next_phase_allowed"] == "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5"
    assert state["answer_access_status"] == "SEALED_AT_TERMINAL_FREEZE"
    assert state["blockers"] == [
        "VALIDATION_FINALIZATION_INTERFACE_CONTRACT_FAILURE",
        "VALIDATION_FINAL_RUN_NOT_COMPLETED",
        "VALIDATION_HANDOFF_NOT_REACHED",
    ]
    assert state["selected_architecture"] == ("ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL")
    assert state["third_party_integrated"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("current_plan", "plans/active/another-plan.md"),
        ("current_branch", "main"),
        ("active_skill_version", "0.2.0-competition-rc5-blocked"),
        ("blocked_candidate_version", "0.2.0-competition-rc7"),
        ("target_candidate_version", "0.2.0-competition-rc6"),
        ("current_validation_case", None),
        ("next_phase_allowed", "PHASE-SKILL-C-TARGET-HELDOUT-004D"),
        ("base_selected", True),
        ("third_party_integrated", True),
    ],
)
def test_phase004c4_fresh_validation_state_mutations_fail_closed(repo_root, field, value) -> None:
    state = copy.deepcopy(_load(repo_root / "state/project_state.json"))
    schema = _load(repo_root / "contracts/project_state.schema.json")
    state[field] = value

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(state)
