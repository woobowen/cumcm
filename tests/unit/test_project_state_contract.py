import copy
import json

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError

from cumcm_skill_lab.adjudication.state_transition import apply_registered_technical_transition


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_project_state_schema_is_legal_status_truth_source(repo_root):
    schema = _read_json(repo_root / "contracts/project_state.schema.json")
    statuses = schema["properties"]["technical_adjudication_status"]["enum"]
    assert len(statuses) == len(set(statuses))
    assert "FAILURE_AWARE_ADJUDICATION_IN_PROGRESS" in statuses
    assert "FAILURE_AWARE_ADJUDICATION_COMPLETE" in statuses


def test_failure_aware_state_fixture_is_valid(repo_root):
    schema = _read_json(repo_root / "contracts/project_state.schema.json")
    state = _read_json(repo_root / "tests/fixtures/contracts/valid/project_state.json")
    Draft202012Validator(schema).validate(state)
    assert state["technical_adjudication_status"] == "FAILURE_AWARE_ADJUDICATION_IN_PROGRESS"


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("next_phase_allowed", "PHASE-SKILL-INTEGRATION-003"),
        ("base_selected", True),
        ("third_party_integrated", True),
        ("skill_capability_status", "IMPLEMENTED"),
        ("selected_architecture", "NATIVE_SINGLE_SKILL_CLEAN_ROOM"),
        ("accepted_component_specifications", ["claim-evidence-support-gate"]),
    ],
)
def test_failure_aware_in_progress_invariants_fail_closed(repo_root, field, invalid):
    schema = _read_json(repo_root / "contracts/project_state.schema.json")
    state = _read_json(repo_root / "tests/fixtures/contracts/valid/project_state.json")
    state[field] = invalid
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(state)


def test_failure_aware_transition_is_registered_and_schema_valid(repo_root):
    schema = _read_json(repo_root / "contracts/project_state.schema.json")
    rules = yaml.safe_load(
        (repo_root / "rules/phase002d_r1_workflow_rules.yaml").read_text(encoding="utf-8")
    )
    candidate = _read_json(repo_root / "tests/fixtures/contracts/valid/project_state.json")
    source = copy.deepcopy(candidate)
    source["technical_adjudication_status"] = "EVIDENCE_EXPANSION_INCOMPLETE"
    source["subphase"] = None
    source["next_phase_allowed"] = "PHASE-EVIDENCE-EXPANSION-002D"
    result = apply_registered_technical_transition(source, candidate, rules, schema)
    assert result == candidate


def test_unregistered_failure_aware_transition_fails_closed(repo_root):
    schema = _read_json(repo_root / "contracts/project_state.schema.json")
    rules = yaml.safe_load(
        (repo_root / "rules/phase002d_r1_workflow_rules.yaml").read_text(encoding="utf-8")
    )
    candidate = _read_json(repo_root / "tests/fixtures/contracts/valid/project_state.json")
    source = copy.deepcopy(candidate)
    source["technical_adjudication_status"] = "AUTOMATED_ADJUDICATION_COMPLETE"
    with pytest.raises(ValueError, match="TECHNICAL_STATUS_TRANSITION_NOT_ALLOWED"):
        apply_registered_technical_transition(source, candidate, rules, schema)


def test_registered_transition_still_rejects_invalid_target_invariants(repo_root):
    schema = _read_json(repo_root / "contracts/project_state.schema.json")
    rules = yaml.safe_load(
        (repo_root / "rules/phase002d_r1_workflow_rules.yaml").read_text(encoding="utf-8")
    )
    candidate = _read_json(repo_root / "tests/fixtures/contracts/valid/project_state.json")
    candidate["next_phase_allowed"] = "PHASE-SKILL-INTEGRATION-003"
    source = copy.deepcopy(candidate)
    source["technical_adjudication_status"] = "EVIDENCE_EXPANSION_INCOMPLETE"
    with pytest.raises(ValueError, match="PROJECT_STATE_INVARIANT_FAILED"):
        apply_registered_technical_transition(source, candidate, rules, schema)


def test_failure_aware_complete_state_is_registered_and_bounded(repo_root):
    schema = _read_json(repo_root / "contracts/project_state.schema.json")
    rules = yaml.safe_load(
        (repo_root / "rules/phase002d_r1_closure_rules.yaml").read_text(encoding="utf-8")
    )
    source = _read_json(repo_root / "tests/fixtures/contracts/valid/project_state.json")
    candidate = copy.deepcopy(source)
    candidate["technical_adjudication_status"] = "FAILURE_AWARE_ADJUDICATION_COMPLETE"
    candidate["accepted_component_specifications"] = ["claim-evidence-support-gate"]
    candidate["next_phase_allowed"] = "PHASE-EVIDENCE-EXPANSION-002D"
    result = apply_registered_technical_transition(source, candidate, rules, schema)
    assert result == candidate


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("next_phase_allowed", None),
        ("next_phase_allowed", "PHASE-SKILL-INTEGRATION-003"),
        ("accepted_component_specifications", []),
        ("selected_architecture", "NATIVE_SINGLE_SKILL_CLEAN_ROOM"),
        ("base_selected", True),
    ],
)
def test_failure_aware_complete_state_fails_closed(repo_root, field, invalid):
    schema = _read_json(repo_root / "contracts/project_state.schema.json")
    candidate = _read_json(repo_root / "tests/fixtures/contracts/valid/project_state.json")
    candidate["technical_adjudication_status"] = "FAILURE_AWARE_ADJUDICATION_COMPLETE"
    candidate["accepted_component_specifications"] = ["claim-evidence-support-gate"]
    candidate["next_phase_allowed"] = "PHASE-EVIDENCE-EXPANSION-002D"
    candidate[field] = invalid
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(candidate)
