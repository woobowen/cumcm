import copy
import json

import pytest
import yaml
from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import file_sha256, sha256_json
from cumcm_skill_lab.specification.component_validator import (
    COMPONENT_CONTRACT,
    INPUT_ROOT,
    validate_component_author_bundles,
    validate_component_specifications,
)
from cumcm_skill_lab.specification.models import COMPONENT_IDS


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _spec(repo_root, component_id):
    return yaml.safe_load(
        (repo_root / f"specifications/components/{component_id}.yaml").read_text(encoding="utf-8")
    )


def _interaction(repo_root):
    return yaml.safe_load(
        (repo_root / "specifications/interactions/component_interaction_contract.yaml").read_text(
            encoding="utf-8"
        )
    )


def test_all_component_author_bundles_are_frozen_and_valid(repo_root):
    assert validate_component_author_bundles(repo_root) == []


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_component_author_bundle_is_peer_invisible_read_only(repo_root, component_id):
    bundle = _json(repo_root / INPUT_ROOT / component_id / "bundle.json")
    assert bundle["component_id"] == component_id
    assert bundle["independent"] is True
    assert bundle["read_only"] is True
    assert bundle["peer_outputs_visible"] is False
    assert bundle["expected_conclusion_visible"] is False


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_component_author_bundle_hash_and_sources_replay(repo_root, component_id):
    bundle = _json(repo_root / INPUT_ROOT / component_id / "bundle.json")
    body = dict(bundle)
    recorded = body.pop("bundle_hash")
    assert sha256_json(body) == recorded
    assert all(
        file_sha256(repo_root / path) == value for path, value in body["source_hashes"].items()
    )


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_component_decision_excerpt_is_only_specification_scope(repo_root, component_id):
    decision = _json(repo_root / INPUT_ROOT / component_id / "decision.json")
    body = dict(decision)
    recorded = body.pop("excerpt_hash")
    assert sha256_json(body) == recorded
    assert decision["decision"] == "AUTOMATED_ACCEPTED"
    assert decision["accepted_scope"] == "SPECIFICATION_ONLY"
    assert decision["component_result"]["mechanism_id"] == component_id


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_each_frozen_component_spec_is_contract_valid(repo_root, component_id):
    schema = _json(repo_root / COMPONENT_CONTRACT)
    errors = list(Draft202012Validator(schema).iter_errors(_spec(repo_root, component_id)))
    assert errors == []


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_each_component_spec_has_clean_room_scope_and_single_state_boundary(
    repo_root, component_id
):
    spec = _spec(repo_root, component_id)
    assert spec["accepted_scope"] == "SPECIFICATION_ONLY"
    assert spec["status"] == "SPECIFICATION_FROZEN"
    assert spec["clean_room_provenance"]["allowed_reuse_mode"] == "REFERENCE_ABSTRACT_MECHANISM"
    interaction = _interaction(repo_root)
    interface = next(
        item for item in interaction["component_interfaces"] if item["component_id"] == component_id
    )
    assert interaction["state_truth"] == "state/project_state.json"
    assert interface["state_access"].startswith("READ_ONLY")
    assert interface["direct_state_advance"] is False
    assert all("benchmark-vault" not in value for value in spec["state_read_set"])


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_each_component_has_public_hidden_and_model_in_loop_tests(repo_root, component_id):
    spec = _spec(repo_root, component_id)
    assert len(spec["public_conformance_tests"]) >= 4
    assert len(spec["hidden_property_tests"]) >= 2
    assert len(spec["model_in_loop_tests"]) >= 1


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_each_component_hashes_are_canonical(repo_root, component_id):
    spec = _spec(repo_root, component_id)
    provenance = dict(spec["clean_room_provenance"])
    provenance_hash = provenance.pop("provenance_hash")
    assert sha256_json(provenance) == provenance_hash
    body = dict(spec)
    spec_hash = body.pop("specification_hash")
    assert sha256_json(body) == spec_hash


REQUIRED_FAIL_CLOSED_FIELDS = (
    "decision_source",
    "accepted_scope",
    "purpose",
    "non_goals",
    "inputs",
    "outputs",
    "preconditions",
    "postconditions",
    "invariants",
    "stale_propagation",
    "failure_modes",
    "acceptance_metrics",
    "rollback",
    "unknowns",
)


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
@pytest.mark.parametrize("field", REQUIRED_FAIL_CLOSED_FIELDS)
def test_missing_component_contract_field_fails_closed(repo_root, component_id, field):
    schema = _json(repo_root / COMPONENT_CONTRACT)
    candidate = copy.deepcopy(_spec(repo_root, component_id))
    candidate.pop(field)
    errors = list(Draft202012Validator(schema).iter_errors(candidate))
    assert any(error.validator == "required" for error in errors)


@pytest.mark.parametrize("component_id", COMPONENT_IDS)
def test_component_implementation_scope_is_rejected(repo_root, component_id):
    schema = _json(repo_root / COMPONENT_CONTRACT)
    candidate = copy.deepcopy(_spec(repo_root, component_id))
    candidate["accepted_scope"] = "IMPLEMENTATION_READY"
    assert list(Draft202012Validator(schema).iter_errors(candidate))


def test_component_registry_and_specs_validate_as_one_set(repo_root):
    result = validate_component_specifications(repo_root)
    assert result["status"] == "PASS"
    assert result["component_count"] == 4
    assert result["component_ids"] == sorted(COMPONENT_IDS)
