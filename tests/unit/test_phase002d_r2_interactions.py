import copy
import json

import pytest
import yaml
from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import sha256_json
from cumcm_skill_lab.specification.architecture_validator import (
    BASELINE_ID,
    CANDIDATE_CONTRACT,
    SET_CONTRACT,
    validate_architecture_candidates,
    validate_candidate_set_value,
)
from cumcm_skill_lab.specification.architecture_validator import (
    SPECIFICATION as ARCHITECTURE_SPECIFICATION,
)
from cumcm_skill_lab.specification.interaction_validator import (
    CONTRACT as INTERACTION_CONTRACT,
)
from cumcm_skill_lab.specification.interaction_validator import (
    SPECIFICATION as INTERACTION_SPECIFICATION,
)
from cumcm_skill_lab.specification.interaction_validator import (
    validate_component_interactions,
    validate_interaction_value,
)
from cumcm_skill_lab.specification.models import COMPONENT_IDS


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _interaction(repo_root):
    return _yaml(repo_root / INTERACTION_SPECIFICATION)


def _candidate_set(repo_root):
    return _yaml(repo_root / ARCHITECTURE_SPECIFICATION)


def _rehash_interaction(value):
    body = dict(value)
    body.pop("contract_hash", None)
    value["contract_hash"] = sha256_json(body)


def _rehash_candidates(value):
    body = dict(value)
    body.pop("candidate_set_hash", None)
    value["candidate_set_hash"] = sha256_json(body)


def test_component_interaction_contract_passes(repo_root):
    result = validate_component_interactions(repo_root)
    assert result["status"] == "PASS"
    assert result["state_truth"] == "state/project_state.json"


def test_interaction_has_exact_component_set(repo_root):
    value = _interaction(repo_root)
    assert {item["component_id"] for item in value["component_interfaces"]} == set(COMPONENT_IDS)


@pytest.mark.parametrize("index", range(4))
def test_no_component_can_directly_advance_state(repo_root, index):
    assert _interaction(repo_root)["component_interfaces"][index]["direct_state_advance"] is False


@pytest.mark.parametrize("truth", ["state_truth", "run", "claim", "model_comparison"])
def test_each_authority_has_one_frozen_truth(repo_root, truth):
    value = _interaction(repo_root)
    if truth == "state_truth":
        assert value[truth] == "state/project_state.json"
    else:
        assert isinstance(value["ledger_truths"][truth], str)
        assert value["ledger_truths"][truth]


def test_second_state_truth_fails(repo_root):
    schema = _json(repo_root / INTERACTION_CONTRACT)
    value = _interaction(repo_root)
    value["state_truth"] = "state/parallel.json"
    _rehash_interaction(value)
    assert "INTERACTION_SECOND_STATE_TRUTH" in validate_interaction_value(schema, value)


def test_duplicate_component_authority_fails(repo_root):
    schema = _json(repo_root / INTERACTION_CONTRACT)
    value = _interaction(repo_root)
    value["component_interfaces"][3]["component_id"] = value["component_interfaces"][0][
        "component_id"
    ]
    _rehash_interaction(value)
    assert "INTERACTION_COMPONENT_SET_INVALID" in validate_interaction_value(schema, value)


def test_conflicting_direct_write_fails(repo_root):
    schema = _json(repo_root / INTERACTION_CONTRACT)
    value = _interaction(repo_root)
    value["component_interfaces"][0]["direct_state_advance"] = True
    _rehash_interaction(value)
    errors = validate_interaction_value(schema, value)
    assert "INTERACTION_DIRECT_STATE_ADVANCE" in errors


def test_circular_dependency_fails(repo_root):
    schema = _json(repo_root / INTERACTION_CONTRACT)
    value = _interaction(repo_root)
    value["data_dependencies"].append(
        {
            "from": "accepted-versus-done-workflow-state",
            "to": "hash-bound-reproducibility-manifest",
            "artifact": "illegal reverse dependency",
            "required": True,
        }
    )
    _rehash_interaction(value)
    assert "INTERACTION_DEPENDENCY_CYCLE" in validate_interaction_value(schema, value)


@pytest.mark.parametrize(
    "required_text",
    ["security", "hash", "reproducibility", "leakage", "claim", "state transition"],
)
def test_failure_precedence_is_explicit(repo_root, required_text):
    text = " ".join(_interaction(repo_root)["failure_precedence"]).lower()
    assert required_text.lower() in text


def test_stale_propagation_available_without_direct_write(repo_root):
    interfaces = _interaction(repo_root)["component_interfaces"]
    assert all(item["can_produce_stale"] for item in interfaces)
    assert all(item["direct_state_advance"] is False for item in interfaces)


def test_architecture_candidate_set_passes_without_selection(repo_root):
    result = validate_architecture_candidates(repo_root)
    assert result["status"] == "PASS"
    assert result["selected_architecture"] is None
    assert 2 <= len(result["candidate_ids"]) <= 3


def test_architecture_baseline_is_required_and_present(repo_root):
    value = _candidate_set(repo_root)
    assert value["baseline_id"] == BASELINE_ID
    assert BASELINE_ID in {item["architecture_id"] for item in value["candidates"]}


@pytest.mark.parametrize("index", range(3))
def test_every_candidate_has_one_skill_and_state_truth(repo_root, index):
    candidate = _candidate_set(repo_root)["candidates"][index]
    assert candidate["formal_skill_count"] == 1
    assert candidate["state_truth_sources"] == ["state/project_state.json"]
    assert candidate["prototype_scope"] == "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY"


def test_architecture_preselection_is_rejected(repo_root):
    value = _candidate_set(repo_root)
    value["selected_architecture"] = value["candidates"][0]["architecture_id"]
    _rehash_candidates(value)
    errors = validate_candidate_set_value(
        _json(repo_root / SET_CONTRACT), _json(repo_root / CANDIDATE_CONTRACT), value
    )
    assert "ARCHITECTURE_PRESELECTED" in errors


def test_second_formal_skill_is_rejected(repo_root):
    value = _candidate_set(repo_root)
    value["candidates"][1]["formal_skill_count"] = 2
    _rehash_candidates(value)
    errors = validate_candidate_set_value(
        _json(repo_root / SET_CONTRACT), _json(repo_root / CANDIDATE_CONTRACT), value
    )
    assert "ARCHITECTURE_SECOND_FORMAL_SKILL" in errors


def test_second_state_source_is_rejected(repo_root):
    value = _candidate_set(repo_root)
    value["candidates"][1]["state_truth_sources"] = ["state/parallel.json"]
    _rehash_candidates(value)
    errors = validate_candidate_set_value(
        _json(repo_root / SET_CONTRACT), _json(repo_root / CANDIDATE_CONTRACT), value
    )
    assert "ARCHITECTURE_SECOND_STATE_SOURCE" in errors


@pytest.mark.parametrize("count", [0, 1, 4])
def test_candidate_count_outside_two_to_three_fails(repo_root, count):
    schema = _json(repo_root / SET_CONTRACT)
    source = _candidate_set(repo_root)["candidates"]
    value = _candidate_set(repo_root)
    value["candidates"] = [copy.deepcopy(source[index % len(source)]) for index in range(count)]
    if count == 4:
        for index, item in enumerate(value["candidates"]):
            item["architecture_id"] = f"ARCH-X{index}"
    assert list(Draft202012Validator(schema).iter_errors(value))


def test_whole_upstream_package_is_prohibited(repo_root):
    text = " ".join(
        entry
        for candidate in _candidate_set(repo_root)["candidates"]
        for entry in candidate["prohibited_behavior"]
    ).lower()
    assert "third-party" in text or "upstream" in text


@pytest.mark.parametrize(
    "field",
    [
        "component_placement",
        "data_flow",
        "state_flow",
        "failure_flow",
        "stale_flow",
        "security_boundary",
        "falsification_conditions",
        "public_tests",
        "hidden_tests",
        "prohibited_behavior",
    ],
)
def test_candidate_required_field_removal_fails(repo_root, field):
    schema = _json(repo_root / CANDIDATE_CONTRACT)
    candidate = copy.deepcopy(_candidate_set(repo_root)["candidates"][1])
    candidate.pop(field)
    assert list(Draft202012Validator(schema).iter_errors(candidate))
