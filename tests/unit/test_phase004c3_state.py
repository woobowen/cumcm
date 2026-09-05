from __future__ import annotations

import copy
import json

import pytest
from jsonschema import Draft202012Validator, ValidationError


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_phase004c3_live_state_is_schema_valid_and_preserves_boundaries(repo_root) -> None:
    state = _load(repo_root / "state/project_state.json")
    schema = _load(repo_root / "contracts/project_state.schema.json")

    Draft202012Validator(schema).validate(state)
    assert state["schema_version"] == "2.4.0"
    assert state["phase"] == "PHASE-SKILL-C-TARGET-EVIDENCE-REPAIR-004C3"
    assert state["subphase"] == "RC6-RELEASE-AND-EVIDENCE-SEMANTICS-REPAIR"
    assert state["technical_adjudication_status"] == "C_TARGET_EVIDENCE_REPAIR_IN_PROGRESS"
    assert state["active_skill_version"] == "0.2.0-competition-rc5-blocked"
    assert state["previous_validation_cases"] == [
        "CUMCM-2024-C-VALIDATION-001",
        "CUMCM-2019-C-VALIDATION-002",
    ]
    assert state["current_validation_case"] is None
    assert state["next_phase_allowed"] is None
    assert state["blockers"] == ["RC5_VERSION_FILE_MISMATCH"]
    assert state["selected_architecture"] == "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
    assert state["skill_capability_status"] == "COMPETITION_RC"
    assert state["third_party_integrated"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "2.3.0"),
        ("current_plan", "plans/active/another-plan.md"),
        ("current_branch", "main"),
        ("active_skill_version", "0.2.0-competition-rc6"),
        ("current_validation_case", "CUMCM-2018-C-VALIDATION-003"),
        ("next_phase_allowed", "PHASE-SKILL-C-TARGET-HELDOUT-004D"),
        ("base_selected", True),
        ("third_party_integrated", True),
        ("blockers", []),
    ],
)
def test_phase004c3_start_state_mutations_fail_closed(repo_root, field, value) -> None:
    state = copy.deepcopy(_load(repo_root / "state/project_state.json"))
    schema = _load(repo_root / "contracts/project_state.schema.json")
    state[field] = value

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(state)
