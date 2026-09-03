import json
from copy import deepcopy

import pytest

from cumcm_skill_lab.authorization_c1.dependency_c2 import (
    RESOLUTION_PATH,
    build_dependency_resolution,
    validate_audit_replay_order,
    validate_dependency_resolution,
)
from cumcm_skill_lab.authorization_c1.final_audit import (
    FINAL_AUDIT_PATH,
    evaluate_final_audit_gate,
    validate_final_audit,
)
from cumcm_skill_lab.authorization_c1.final_audit_bundle import BUNDLE_PATH
from cumcm_skill_lab.authorization_c1.models import sha256_json


def _read(repo_root, path):
    return json.loads((repo_root / path).read_text(encoding="utf-8"))


def test_structurally_valid_c1_final_audit_is_preserved_as_fail(repo_root):
    audit = _read(repo_root, FINAL_AUDIT_PATH)
    assert validate_final_audit(repo_root, audit) == []
    assert audit["verdict"] == "FAIL"
    assert audit["unresolved_blockers"] == ["R2A-C1-FINAL-001"]


@pytest.mark.parametrize("action", ["SEAL", "REPLAY", "STATE_TRANSITION"])
def test_c1_final_fail_blocks_terminal_actions(repo_root, action):
    gate = evaluate_final_audit_gate(repo_root, action)
    assert gate["status"] == "BLOCKED"
    assert "C1_FINAL_AUTHORIZATION_AUDIT_NOT_PASS" in gate["errors"]
    assert "C1_FINAL_AUTHORIZATION_AUDIT_BLOCKERS_PRESENT" in gate["errors"]


def test_final_audit_unbound_to_bundle_is_rejected(repo_root):
    audit = deepcopy(_read(repo_root, FINAL_AUDIT_PATH))
    audit["bundle_hash"] = "0" * 64
    audit["output_hash"] = sha256_json(
        {key: value for key, value in audit.items() if key != "output_hash"}
    )
    assert "C1_FINAL_AUDIT_BUNDLE_HASH_MISMATCH" in validate_final_audit(repo_root, audit)


def test_final_audit_parent_or_sequence_substitution_is_rejected(repo_root):
    audit = deepcopy(_read(repo_root, FINAL_AUDIT_PATH))
    audit["parent_artifact_hash"] = "0" * 64
    audit["artifact_sequence_index"] = 9
    audit["output_hash"] = sha256_json(
        {key: value for key, value in audit.items() if key != "output_hash"}
    )
    errors = validate_final_audit(repo_root, audit)
    assert "C1_FINAL_AUDIT_PARENT_ARTIFACT_HASH_MISMATCH" in errors
    assert "C1_FINAL_AUDIT_ARTIFACT_SEQUENCE_INDEX_MISMATCH" in errors


def test_c1_source_graph_exposes_semantic_audit_replay_cycle(repo_root):
    source = _read(repo_root, "evals/results/phase-002d-r2a/authorization_dependency_graph.json")
    source["prerequisite_replay_node"] = "L3-R2-REPLAY"
    audit = _read(repo_root, "evals/results/phase-002d-r2/decision_audit/audit.json")
    assert validate_audit_replay_order(
        source, audit, "evals/results/phase-002d-r2/replay/replay.json"
    ) == [
        "C1_R2_AUDIT_REPLAY_SEMANTIC_CYCLE",
        "C1_R2_REPLAY_TO_AUDIT_PREREQUISITE_EDGE_MISSING",
    ]


def test_c2_dependency_resolution_closes_exact_final_finding(repo_root):
    value = _read(repo_root, RESOLUTION_PATH)
    assert value == build_dependency_resolution(repo_root)
    assert validate_dependency_resolution(repo_root, value) == []
    assert value["finding_id"] == "R2A-C1-FINAL-001"
    assert value["status"] == "PASS"
    assert value["corrected_graph_errors"] == []
    assert value["corrected_graph"]["cycle_detected"] is False


def test_c2_resolution_is_child_of_c1_final_audit(repo_root):
    resolution = _read(repo_root, RESOLUTION_PATH)
    audit = _read(repo_root, FINAL_AUDIT_PATH)
    bundle = _read(repo_root, BUNDLE_PATH)
    assert audit["parent_artifact_hash"] == bundle["bundle_hash"]
    assert resolution["parent_artifact_hash"] == audit["output_hash"]
    assert resolution["artifact_sequence_index"] == 11
