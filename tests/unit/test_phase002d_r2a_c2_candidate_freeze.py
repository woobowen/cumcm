import json
from copy import deepcopy

from cumcm_skill_lab.authorization_c1.models import file_sha256
from cumcm_skill_lab.authorization_c2.candidate_freeze import (
    C1_FINAL_AUDIT_PATH,
    CANDIDATE_ID,
    CANDIDATE_PATH,
    CREATION_COMMIT,
    DEPENDENCY_RESOLUTION_PATH,
    FREEZE_PATH,
    build_candidate,
    canonical_candidate_hash,
    frozen_revision_rewrite_errors,
    validate_candidate,
    validate_candidate_freeze,
)
from cumcm_skill_lab.specification.implementation_embargo import verify_embargo


def _read(repo_root, path):
    return json.loads((repo_root / path).read_text(encoding="utf-8"))


def test_c2_candidate_is_reproducible_and_accepted(repo_root):
    candidate = _read(repo_root, CANDIDATE_PATH)
    assert candidate == build_candidate(repo_root)
    assert validate_candidate(repo_root, candidate) == []
    assert candidate["candidate_id"] == CANDIDATE_ID
    assert candidate["revision"] == "C2"
    assert candidate["active"] is False
    assert candidate["decision"] == "AUTOMATED_ACCEPTED"
    assert candidate["accepted_scope"] == "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY"
    assert candidate["next_phase_allowed"] == "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"


def test_c2_candidate_binds_corrected_graph_and_c1_failure(repo_root):
    candidate = _read(repo_root, CANDIDATE_PATH)
    resolution = _read(repo_root, DEPENDENCY_RESOLUTION_PATH)
    audit = _read(repo_root, C1_FINAL_AUDIT_PATH)
    assert (
        candidate["input_references"]["c2_dependency_graph_hash"]
        == resolution["corrected_graph"]["graph_hash"]
    )
    assert (
        candidate["input_references"]["c2_dependency_resolution_hash"]
        == resolution["resolution_hash"]
    )
    assert candidate["retests_candidate"]["final_audit_output_hash"] == audit["output_hash"]
    assert candidate["retests_candidate"]["finding_id"] == "R2A-C1-FINAL-001"


def test_c2_freeze_binds_exact_new_candidate_bytes(repo_root):
    candidate = _read(repo_root, CANDIDATE_PATH)
    freeze = _read(repo_root, FREEZE_PATH)
    resolution = _read(repo_root, DEPENDENCY_RESOLUTION_PATH)
    assert validate_candidate_freeze(repo_root, freeze) == []
    assert freeze["candidate_file_sha256"] == file_sha256(repo_root / CANDIDATE_PATH)
    assert freeze["canonical_candidate_hash"] == canonical_candidate_hash(candidate)
    assert freeze["parent_artifact_hash"] == resolution["resolution_hash"]
    assert freeze["artifact_sequence_index"] == 12
    assert freeze["creation_commit"] == CREATION_COMMIT


def test_c2_tuple_is_distinct_from_c1(repo_root):
    c1 = _read(
        repo_root,
        "evals/results/phase-002d-r2a-c1/candidate_freeze/candidate_freeze_manifest-c1.json",
    )
    c2 = _read(repo_root, FREEZE_PATH)
    assert c2["candidate_id"] != c1["candidate_id"]
    assert c2["candidate_file_sha256"] != c1["candidate_file_sha256"]
    assert c2["canonical_candidate_hash"] != c1["canonical_candidate_hash"]
    assert c2["freeze_hash"] != c1["freeze_hash"]


def test_c2_candidate_rejects_scope_and_dependency_drift(repo_root):
    candidate = _read(repo_root, CANDIDATE_PATH)
    scope_drift = deepcopy(candidate)
    scope_drift["selected_architecture"] = "ARCH-ATTACKER"
    assert "C2_CANDIDATE_ARCHITECTURE_SELECTION_PROHIBITED" in validate_candidate(
        repo_root, scope_drift
    )
    dependency_drift = deepcopy(candidate)
    dependency_drift["input_references"]["c2_dependency_graph_hash"] = "0" * 64
    assert "C2_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH" in validate_candidate(
        repo_root, dependency_drift
    )


def test_c2_frozen_bytes_are_write_once(repo_root):
    current = (repo_root / CANDIDATE_PATH).read_bytes()
    proposed = current + b" "
    assert frozen_revision_rewrite_errors(current, current) == []
    assert frozen_revision_rewrite_errors(current, proposed) == [
        "C2_FROZEN_CANDIDATE_REWRITE_PROHIBITED"
    ]


def test_c2_authorization_governance_does_not_release_implementation_embargo(repo_root):
    assert verify_embargo(repo_root) == []
    candidate = _read(repo_root, CANDIDATE_PATH)
    assert candidate["prototype_implemented"] is False
    assert candidate["prototype_executed"] is False
    assert candidate["selected_architecture"] is None
