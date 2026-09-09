import copy
import json

import pytest
from jsonschema import Draft202012Validator


def _inputs(repo_root):
    schema = json.loads((repo_root / "contracts/project_state.schema.json").read_text())
    historical = json.loads(
        (repo_root / "evals/results/phase-004c5/qualification/predecessor_state.json").read_text()
    )
    state = copy.deepcopy(historical)
    state.update(
        phase="PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5",
        subphase="RC8-FACT-BINDING-REPAIR",
        current_plan="plans/active/PLAN-0004C5-rc8-fact-binding-and-fresh-validation.md",
        current_branch="feat/phase004c5-p0-01-finalization-hf22-repro",
        technical_adjudication_status="C_TARGET_EVIDENCE_REPAIR_IN_PROGRESS",
        target_candidate_version="0.2.0-competition-rc8",
        current_validation_case=None,
        next_phase_allowed=None,
        answer_access_status="SEALED_NOT_ACCESSED",
    )
    return Draft202012Validator(schema), historical, state


def test_historical_and_new_repair_identities_remain_valid(repo_root):
    validator, old, current = _inputs(repo_root)
    assert list(validator.iter_errors(old)) == []
    assert list(validator.iter_errors(current)) == []
    old["active_skill_version"] = "0.2.0-competition-rc8"
    assert list(validator.iter_errors(old))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("active_skill_version", "0.2.0-competition-rc8"),
        ("current_validation_case", "CUMCM-2016-C-VALIDATION-004"),
        ("next_phase_allowed", "PHASE-SKILL-C-TARGET-HELDOUT-004D"),
        ("target_candidate_version", "0.2.0-competition-rc7"),
    ],
)
def test_repair_cannot_activate_or_start_fresh_case(repo_root, field, value):
    validator, _, state = _inputs(repo_root)
    state[field] = value
    assert list(validator.iter_errors(state))


def test_ready_requires_new_active_identity_and_no_blocker(repo_root):
    validator, _, state = _inputs(repo_root)
    state.update(
        technical_adjudication_status="C_TARGET_RC8_READY_VALIDATION_PENDING",
        subphase="RC8-FROZEN-PENDING-FRESH-C-VALIDATION",
        active_skill_version="0.2.0-competition-rc8",
        blockers=[],
    )
    assert list(validator.iter_errors(state)) == []
    state["blockers"] = ["AUDIT_UNRESOLVED"]
    assert list(validator.iter_errors(state))
