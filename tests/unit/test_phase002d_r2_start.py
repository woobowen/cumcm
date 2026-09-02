import copy
import json

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError

from cumcm_skill_lab.adjudication.state_transition import apply_registered_technical_transition
from cumcm_skill_lab.specification.implementation_embargo import verify_embargo
from cumcm_skill_lab.specification.models import COMPONENT_IDS, verify_input_freeze


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_r2_input_freeze_verifies_all_historical_inputs(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2/input_freeze_manifest.json")
    assert verify_input_freeze(repo_root, manifest) == []
    assert manifest["accepted_component_specification_ids"] == list(COMPONENT_IDS)
    assert manifest["selected_architecture"] is None


def test_r2_input_freeze_hash_mutation_fails_closed(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2/input_freeze_manifest.json")
    manifest["phase002d_r1_freeze_hash"] = "0" * 64
    assert "PHASE002D_R2_MANIFEST_HASH_MISMATCH" in verify_input_freeze(repo_root, manifest)


def test_r2_implementation_embargo_verifies(repo_root):
    embargo = _json(repo_root / "evals/results/phase-002d-r2/implementation_embargo.json")
    assert verify_embargo(repo_root, embargo) == []
    assert embargo["prohibited_component_implementation"] is True
    assert embargo["prohibited_shadow_prototype_execution"] is True


def test_r2_implementation_embargo_hash_mutation_fails_closed(repo_root):
    embargo = _json(repo_root / "evals/results/phase-002d-r2/implementation_embargo.json")
    embargo["is_component_implementation"] = True
    assert "IMPLEMENTATION_EMBARGO_HASH_MISMATCH" in verify_embargo(repo_root, embargo)


def test_r2_state_is_schema_valid_and_keeps_boundary(repo_root):
    schema = _json(repo_root / "contracts/project_state.schema.json")
    state = _json(repo_root / "state/project_state.json")
    Draft202012Validator(schema).validate(state)
    assert state["technical_adjudication_status"] == "SPECIFICATION_PROTOCOL_IN_PROGRESS"
    assert state["accepted_component_specifications"] == list(COMPONENT_IDS)
    assert state["architecture_candidate_set"] == []
    assert state["selected_architecture"] is None
    assert state["next_phase_allowed"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("selected_architecture", "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"),
        ("architecture_candidate_set", ["ARCH-S0-RETAIN-SCAFFOLD-ONLY"]),
        ("next_phase_allowed", "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"),
        ("base_selected", True),
        ("third_party_integrated", True),
    ],
)
def test_r2_in_progress_state_rejects_premature_advancement(repo_root, field, value):
    schema = _json(repo_root / "contracts/project_state.schema.json")
    state = _json(repo_root / "state/project_state.json")
    state[field] = value
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(state)


def test_r2_transition_from_completed_r1_is_registered(repo_root):
    schema = _json(repo_root / "contracts/project_state.schema.json")
    rules = yaml.safe_load(
        (repo_root / "rules/phase002d_r2_workflow_rules.yaml").read_text(encoding="utf-8")
    )
    candidate = _json(repo_root / "state/project_state.json")
    source = copy.deepcopy(candidate)
    source["subphase"] = "PHASE-002D-R1-FAILURE-AWARE-OUTCOME-ADJUDICATION"
    source["current_plan"] = "plans/completed/PLAN-0002D-R1-failure-aware-outcomes.md"
    source["technical_adjudication_status"] = "FAILURE_AWARE_ADJUDICATION_COMPLETE"
    source["architecture_candidate_set"] = []
    source["next_phase_allowed"] = "PHASE-EVIDENCE-EXPANSION-002D"
    assert apply_registered_technical_transition(source, candidate, rules, schema) == candidate
