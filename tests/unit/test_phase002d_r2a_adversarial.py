import copy

import pytest

from cumcm_skill_lab.adjudication.models import read_json, read_yaml, sha256_json
from cumcm_skill_lab.specification.authorization.adversarial_closure import (
    CLOSURE_PATH,
    EVIDENCE_PATH,
    FINDINGS_PATH,
    REQUESTS_PATH,
    TEST_IDS,
    evaluate_closures,
    synthesize_adversarial_closure,
)
from cumcm_skill_lab.specification.authorization.bindings import (
    build_synthetic_replay,
    build_synthetic_seal,
    validate_replay_binding,
    validate_supersession_binding,
)
from cumcm_skill_lab.specification.authorization.dependency_graph import (
    verify_dependency_graph,
)
from cumcm_skill_lab.specification.authorization.models import DEPENDENCY_PATH
from cumcm_skill_lab.specification.authorization.scope import (
    SCOPE_PATH,
    validate_scope_value,
)


def _rehash(value, field):
    body = copy.deepcopy(value)
    body.pop(field, None)
    value[field] = sha256_json(body)


@pytest.mark.parametrize("finding_id", tuple(TEST_IDS), ids=tuple(TEST_IDS))
def test_every_serious_attack_has_deterministic_bounded_closure(repo_root, finding_id):
    passed, evidence = evaluate_closures(repo_root)[finding_id]
    assert passed, evidence


def test_generated_attack_chain_is_complete_hash_bound_and_reproducible(repo_root):
    findings = read_json(repo_root / FINDINGS_PATH)["findings"]
    requests = read_json(repo_root / REQUESTS_PATH)["test_requests"]
    evidence = read_json(repo_root / EVIDENCE_PATH)["test_evidence"]
    closure = read_json(repo_root / CLOSURE_PATH)
    assert len(findings) == len(requests) == len(evidence) == len(TEST_IDS) == 15
    assert {item["finding_id"] for item in findings} == set(TEST_IDS)
    assert {item["finding_id"] for item in requests} == set(TEST_IDS)
    assert {item["finding_id"] for item in evidence} == set(TEST_IDS)
    assert all(item["status"] == "PASSED" and item["oracle_result"] for item in evidence)
    body = copy.deepcopy(closure)
    recorded_hash = body.pop("closure_hash")
    assert sha256_json(body) == recorded_hash
    assert synthesize_adversarial_closure(repo_root, check=True)["status"] == "PASS"


def test_fail_closed_closures_do_not_promote_unverified_future_risks(repo_root):
    closure = read_json(repo_root / CLOSURE_PATH)
    restricted = [
        item
        for item in closure["closures"]
        if item["disposition"] == "CLOSED_BY_FAIL_CLOSED_SCOPE_RESTRICTION"
    ]
    assert len(restricted) == 9
    assert all(item["underlying_risk_resolved"] is False for item in restricted)
    assert all(item["underlying_risk_status"] == "UNVERIFIED" for item in restricted)
    assert closure["underlying_future_risks_are_not_promoted_to_verified_facts"] is True
    assert closure["majority_vote_used"] is False


@pytest.mark.parametrize(
    ("section", "field", "invalid", "expected"),
    [
        (
            "path_confinement",
            "canonical_root_required",
            False,
            "SHADOW_SCOPE_PATH_CONFINEMENT_GATE_INCOMPLETE",
        ),
        (
            "path_confinement",
            "no_follow_required",
            False,
            "SHADOW_SCOPE_PATH_CONFINEMENT_GATE_INCOMPLETE",
        ),
        (
            "dependency_policy",
            "dynamic_import_allowed",
            True,
            "SHADOW_SCOPE_DEPENDENCY_GATE_INCOMPLETE",
        ),
        ("dependency_policy", "network_allowed", True, "SHADOW_SCOPE_DEPENDENCY_GATE_INCOMPLETE"),
        (
            "callability_policy",
            "production_registry_entry_allowed",
            True,
            "SHADOW_SCOPE_CALLABILITY_GATE_INCOMPLETE",
        ),
        (
            "output_policy",
            "formal_artifact_kinds_allowed",
            ["AUTOMATED_DECISION"],
            "SHADOW_SCOPE_OUTPUT_GATE_INCOMPLETE",
        ),
        (
            "execution_stages",
            "model_starts_authorized",
            1,
            "SHADOW_SCOPE_EXECUTION_STAGE_ESCALATION",
        ),
        (
            "future_runtime_gate",
            "actual_runtime_evidence_present",
            True,
            "SHADOW_SCOPE_FUTURE_RUNTIME_GATE_INCOMPLETE",
        ),
        ("rollback", "git_tracking_allowed", True, "SHADOW_SCOPE_ROLLBACK_NOT_ISOLATED"),
    ],
)
def test_hardened_scope_mutations_fail_closed(repo_root, section, field, invalid, expected):
    scope = read_yaml(repo_root / SCOPE_PATH)
    scope[section][field] = invalid
    _rehash(scope, "scope_hash")
    assert expected in validate_scope_value(repo_root, scope)


@pytest.mark.parametrize(
    ("field", "invalid", "expected"),
    [
        ("input_freeze_hash", "6" * 64, "R2A_REPLAY_INPUT_FREEZE_HASH_MISMATCH"),
        ("active_decision_hash", "7" * 64, "R2A_REPLAY_ACTIVE_DECISION_HASH_MISMATCH"),
        (
            "final_audit_checkpoint_hash",
            "8" * 64,
            "R2A_REPLAY_FINAL_AUDIT_CHECKPOINT_HASH_MISMATCH",
        ),
        ("stable", False, "R2A_REPLAY_UNSTABLE"),
    ],
)
def test_replay_binding_mutations_fail_closed(repo_root, field, invalid, expected):
    seal = build_synthetic_seal(repo_root)
    replay = build_synthetic_replay(repo_root, seal)
    replay[field] = invalid
    _rehash(replay, "replay_hash")
    assert expected in validate_replay_binding(repo_root, replay, seal)


@pytest.mark.parametrize(
    ("target", "invalid", "expected"),
    [
        (
            "authorization_id",
            "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2",
            "R2A_SEAL_REUSES_HISTORICAL_DECISION_ID",
        ),
        (
            "artifact_path",
            "evals/results/phase-002d-r2/automated_decisions/shadow_prototype_authorization.json",
            "R2A_SEAL_OVERWRITES_HISTORICAL_ARTIFACT",
        ),
        ("supersedes.decision_hash", "9" * 64, "R2A_SEAL_SUPERSESSION_DECISION_HASH_MISMATCH"),
        ("supersedes.file_sha256", "a" * 64, "R2A_SEAL_SUPERSESSION_FILE_SHA256_MISMATCH"),
    ],
)
def test_supersession_identity_mutations_fail_closed(repo_root, target, invalid, expected):
    seal = build_synthetic_seal(repo_root)
    if target.startswith("supersedes."):
        seal["supersedes"][target.split(".", 1)[1]] = invalid
    else:
        seal[target] = invalid
    _rehash(seal, "authorization_hash")
    assert expected in validate_supersession_binding(repo_root, seal)


@pytest.mark.parametrize(
    ("mutation", "expected", "rehash"),
    [
        ("duplicate_node", "PHASE002D_R2A_DEPENDENCY_DUPLICATE_NODE", True),
        ("dangling_endpoint", "PHASE002D_R2A_DEPENDENCY_DANGLING_ENDPOINT", True),
        ("node_level", "PHASE002D_R2A_DEPENDENCY_NODE_LEVEL_MISMATCH", True),
        ("level_regression", "PHASE002D_R2A_DEPENDENCY_LEVEL_REGRESSION", True),
        ("state_unreachable", "PHASE002D_R2A_DEPENDENCY_STATE_NOT_REACHABLE_FROM_INPUT", True),
        ("edge_semantics", "PHASE002D_R2A_DEPENDENCY_EDGE_SEMANTICS_INVALID", True),
        ("stale_hash", "PHASE002D_R2A_DEPENDENCY_GRAPH_HASH_MISMATCH", False),
    ],
)
def test_dependency_graph_semantic_mutations_fail_closed(repo_root, mutation, expected, rehash):
    graph = read_json(repo_root / DEPENDENCY_PATH)
    if mutation == "duplicate_node":
        graph["nodes"].append(copy.deepcopy(graph["nodes"][0]))
    elif mutation == "dangling_endpoint":
        graph["edges"].append({"source": "L0-COMPONENT-SPECS", "target": "L7-MISSING"})
    elif mutation == "node_level":
        graph["nodes"][0]["level"] = 1
    elif mutation == "level_regression":
        graph["edges"].append({"source": "L4-R2A-ELIGIBILITY", "target": "L3-R2-REPLAY"})
    elif mutation == "state_unreachable":
        graph["edges"] = [
            item
            for item in graph["edges"]
            if not (
                item["source"] == "L0-CLEAN-ROOM-PROVENANCE"
                and item["target"] == "L4-R2A-ELIGIBILITY"
            )
        ]
    elif mutation == "edge_semantics":
        graph["historical_evidence_references_create_edges"] = True
    else:
        graph["input_freeze_hash"] = "b" * 64
    if rehash:
        _rehash(graph, "graph_hash")
    assert expected in verify_dependency_graph(repo_root, graph)
