import copy
import json

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError

from cumcm_skill_lab.adjudication.models import file_sha256, sha256_json
from cumcm_skill_lab.adjudication.state_transition import apply_registered_technical_transition
from cumcm_skill_lab.authorization_c1.models import git_file_bytes
from cumcm_skill_lab.specification.authorization.dependency_graph import (
    build_dependency_graph,
    cycle_nodes,
    verify_dependency_graph,
)
from cumcm_skill_lab.specification.authorization.evidence_freeze import verify_input_freeze
from cumcm_skill_lab.specification.authorization.models import (
    OLD_AUTHORIZATION_ID,
    SUBJECT_COMMIT,
    git_file_sha256,
)

R2A_START_STATE_COMMIT = "586ec15c81b530fd200ae79fa600ea060bec6727"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _r2a_start_state(repo_root):
    return json.loads(git_file_bytes(repo_root, R2A_START_STATE_COMMIT, "state/project_state.json"))


def _rehash(record, field):
    body = copy.deepcopy(record)
    body.pop(field, None)
    record[field] = sha256_json(body)


def test_r2a_input_freeze_verifies(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    assert verify_input_freeze(repo_root, manifest) == []
    assert manifest["freeze_id"] == "PHASE-002D-R2A-INPUT-FREEZE-001"


def test_r2a_freeze_binds_every_declared_immutable_file(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    assert manifest["immutable_file_count"] == len(manifest["immutable_file_hashes"])
    assert manifest["immutable_file_count"] >= 500


def test_r2a_freeze_binds_five_prerequisite_decisions(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    bindings = manifest["accepted_prerequisite_decision_hashes"]
    assert len(bindings) == 5
    assert all(len(item["decision_hash"]) == 64 for item in bindings.values())


def test_r2a_freeze_binds_all_r2_serious_finding_closures(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    assert len(manifest["serious_finding_closure_hashes"]) == 29
    assert all(len(value) == 64 for value in manifest["serious_finding_closure_hashes"].values())


def test_old_shadow_authorization_is_exact_subject_bytes(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    binding = manifest["old_shadow_authorization"]
    assert binding["decision_id"] == OLD_AUTHORIZATION_ID
    assert binding["decision"] == "RETEST_REQUIRED"
    assert file_sha256(repo_root / binding["path"]) == binding["file_sha256"]
    assert git_file_sha256(repo_root, SUBJECT_COMMIT, binding["path"]) == binding["file_sha256"]


def test_r2a_manifest_hash_mutation_fails_closed(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    manifest["r2_input_freeze_hash"] = "0" * 64
    assert "PHASE002D_R2A_MANIFEST_HASH_MISMATCH" in verify_input_freeze(repo_root, manifest)


def test_r2a_immutable_binding_mutation_fails_closed(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    first = next(iter(manifest["immutable_file_hashes"]))
    manifest["immutable_file_hashes"][first] = "0" * 64
    _rehash(manifest, "manifest_hash")
    assert "PHASE002D_R2A_IMMUTABLE_INPUT_MUTATED" in verify_input_freeze(repo_root, manifest)


def test_r2a_old_decision_binding_mutation_fails_closed(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    manifest["old_shadow_authorization"]["file_sha256"] = "0" * 64
    _rehash(manifest, "manifest_hash")
    errors = verify_input_freeze(repo_root, manifest)
    assert "PHASE002D_R2A_OLD_AUTHORIZATION_BYTES_CHANGED" in errors
    assert "PHASE002D_R2A_OLD_AUTHORIZATION_SUBJECT_MISMATCH" in errors


def test_r2a_formal_skill_hash_mutation_fails_closed(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    manifest["formal_skill_tree_hash"] = "0" * 64
    _rehash(manifest, "manifest_hash")
    assert "PHASE002D_R2A_FORMAL_SKILL_HASH_CHANGED" in verify_input_freeze(repo_root, manifest)


def test_r2a_execution_baseline_must_be_zero(repo_root):
    manifest = _json(repo_root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    manifest["prototype_executions"] = 1
    _rehash(manifest, "manifest_hash")
    assert "PHASE002D_R2A_EXECUTION_BASELINE_NONZERO" in verify_input_freeze(repo_root, manifest)


def test_r2a_dependency_graph_is_valid_and_acyclic(repo_root):
    graph = _json(repo_root / "evals/results/phase-002d-r2a/authorization_dependency_graph.json")
    assert verify_dependency_graph(repo_root, graph) == []
    assert cycle_nodes(graph) == []
    assert graph["cycle_detected"] is False


def test_r2a_dependency_graph_rebuild_is_deterministic(repo_root):
    recorded = _json(repo_root / "evals/results/phase-002d-r2a/authorization_dependency_graph.json")
    assert build_dependency_graph(repo_root) == recorded


def test_r2a_dependency_cycle_is_rejected(repo_root):
    graph = _json(repo_root / "evals/results/phase-002d-r2a/authorization_dependency_graph.json")
    graph["edges"].append({"source": "L7-FORMAL-STATE-TRANSITION", "target": "L4-R2A-ELIGIBILITY"})
    _rehash(graph, "graph_hash")
    assert "PHASE002D_R2A_DEPENDENCY_CYCLE" in verify_dependency_graph(repo_root, graph)


def test_r2a_dependency_missing_prerequisite_is_rejected(repo_root):
    graph = _json(repo_root / "evals/results/phase-002d-r2a/authorization_dependency_graph.json")
    graph["nodes"] = [item for item in graph["nodes"] if item["id"] != "L2-R2-DECISION-AUDIT"]
    graph["edges"] = [
        item
        for item in graph["edges"]
        if "L2-R2-DECISION-AUDIT" not in {item["source"], item["target"]}
    ]
    _rehash(graph, "graph_hash")
    errors = verify_dependency_graph(repo_root, graph)
    assert "PHASE002D_R2A_DEPENDENCY_REQUIRED_NODE_MISSING" in errors


def test_r2a_authorization_before_audit_back_edge_is_rejected(repo_root):
    graph = _json(repo_root / "evals/results/phase-002d-r2a/authorization_dependency_graph.json")
    graph["edges"].append(
        {
            "source": "L5-R2A-AUTHORIZATION-CANDIDATE",
            "target": "L2-R2-DECISION-AUDIT",
        }
    )
    _rehash(graph, "graph_hash")
    errors = verify_dependency_graph(repo_root, graph)
    assert "PHASE002D_R2A_DEPENDENCY_FORBIDDEN_BACK_EDGE" in errors


def test_r2a_state_transition_requires_final_audit_and_replay_edges(repo_root):
    graph = _json(repo_root / "evals/results/phase-002d-r2a/authorization_dependency_graph.json")
    graph["edges"] = [
        item
        for item in graph["edges"]
        if not (
            item["source"] == "L7-R2A-FINAL-REPLAY"
            and item["target"] == "L7-FORMAL-STATE-TRANSITION"
        )
    ]
    _rehash(graph, "graph_hash")
    assert "PHASE002D_R2A_DEPENDENCY_REQUIRED_EDGE_MISSING" in verify_dependency_graph(
        repo_root, graph
    )


def test_r2a_start_state_is_schema_valid(repo_root):
    schema = _json(repo_root / "contracts/project_state.schema.json")
    state = _r2a_start_state(repo_root)
    Draft202012Validator(schema).validate(state)
    assert state["technical_adjudication_status"] == "SHADOW_PROTOTYPE_AUTHORIZATION_IN_PROGRESS"
    assert state["selected_architecture"] is None
    assert state["next_phase_allowed"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("selected_architecture", "ARCH-W1-WORKFLOW-ONLY-GUARDS"),
        ("base_selected", True),
        ("third_party_integrated", True),
        ("next_phase_allowed", "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"),
    ],
)
def test_r2a_start_state_rejects_premature_advancement(repo_root, field, value):
    schema = _json(repo_root / "contracts/project_state.schema.json")
    state = _r2a_start_state(repo_root)
    state[field] = value
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(state)


def test_r2_to_r2a_state_transition_is_registered(repo_root):
    schema = _json(repo_root / "contracts/project_state.schema.json")
    rules = yaml.safe_load(
        (repo_root / "rules/phase002d_r2a_workflow_rules.yaml").read_text(encoding="utf-8")
    )
    candidate = _r2a_start_state(repo_root)
    source = copy.deepcopy(candidate)
    source.update(
        {
            "subphase": "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL",
            "current_plan": "plans/completed/PLAN-0002D-R2-specification-and-protocol.md",
            "technical_adjudication_status": "SPECIFICATION_PROTOCOL_COMPLETE",
            "next_phase_allowed": (
                "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL"
            ),
        }
    )
    assert apply_registered_technical_transition(source, candidate, rules, schema) == candidate


def test_r3_plan_is_preserved_after_successor_advances(repo_root):
    plans = list((repo_root / "plans/active").glob("*.md"))
    assert [item.name for item in plans] == ["PLAN-0004B-2020a-development-eval.md"]
    assert (repo_root / "plans/completed/PLAN-0004A-2023c-development-eval.md").is_file()
    assert (repo_root / "plans/completed/PLAN-0002D-R3-shadow-prototype-validation.md").is_file()
    assert (repo_root / "plans/completed/PLAN-0002D-R2-specification-and-protocol.md").is_file()
    assert (
        repo_root / "plans/completed/PLAN-0002D-R2A-shadow-authorization-closure-incomplete.md"
    ).is_file()
    assert (
        repo_root
        / "plans/completed/PLAN-0002D-R2A-C1-historical-compatibility-and-candidate-binding.md"
    ).is_file()
