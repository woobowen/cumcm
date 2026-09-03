import json
from copy import deepcopy

import pytest

import cumcm_skill_lab.authorization_c1.candidate_freeze as candidate_module
from cumcm_skill_lab.authorization_c1.candidate_freeze import (
    CANDIDATE_ID,
    RESERVED_SELF_HASH_FIELDS,
    build_candidate,
    build_candidate_freeze,
    canonical_candidate_hash,
    validate_candidate,
    validate_candidate_freeze,
)
from cumcm_skill_lab.authorization_c1.models import file_sha256


def _write(path, value, *, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if compact
        else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    )
    path.write_text(text, encoding="utf-8")


def test_candidate_decision_is_derived_and_scope_is_bounded(repo_root):
    candidate = build_candidate(repo_root)
    assert candidate["decision"] == "AUTOMATED_ACCEPTED"
    assert candidate["accepted_scope"] == "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY"
    assert candidate["next_phase_allowed"] == "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"
    assert candidate["selected_architecture"] is None
    assert candidate["phase003_prohibited"] is True


def test_candidate_contains_no_self_referential_hash_or_timestamp(repo_root):
    candidate = build_candidate(repo_root)
    assert not RESERVED_SELF_HASH_FIELDS.intersection(candidate)
    assert "created_at" not in candidate


def test_canonical_hash_is_stable_under_object_key_order(repo_root):
    candidate = build_candidate(repo_root)
    reordered = dict(reversed(list(candidate.items())))
    assert canonical_candidate_hash(candidate) == canonical_candidate_hash(reordered)


def test_canonical_hash_retains_unknown_fields(repo_root):
    candidate = build_candidate(repo_root)
    mutated = {**candidate, "unknown_attack_field": "MUST_NOT_BE_DROPPED"}
    assert canonical_candidate_hash(candidate) != canonical_candidate_hash(mutated)


@pytest.mark.parametrize("field", sorted(RESERVED_SELF_HASH_FIELDS))
def test_canonical_hash_rejects_reserved_self_hash_fields(repo_root, field):
    candidate = {**build_candidate(repo_root), field: "0" * 64}
    with pytest.raises(ValueError, match="C1_CANDIDATE_SELF_HASH_FIELD_PROHIBITED"):
        canonical_candidate_hash(candidate)


def test_candidate_semantic_mutation_is_rejected(repo_root):
    candidate = build_candidate(repo_root)
    candidate["selected_architecture"] = "ARCH-W1-WORKFLOW-ONLY-GUARDS"
    errors = validate_candidate(repo_root, candidate)
    assert "C1_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH" in errors
    assert "C1_CANDIDATE_ARCHITECTURE_SELECTION_PROHIBITED" in errors


def test_candidate_id_mutation_is_rejected(repo_root):
    candidate = build_candidate(repo_root)
    candidate["candidate_id"] = "CANDIDATE-ATTACKER"
    assert "C1_CANDIDATE_ID_MISMATCH" in validate_candidate(repo_root, candidate)


def test_freeze_binds_exact_file_and_canonical_hash(repo_root):
    candidate = build_candidate(repo_root)
    manifest = build_candidate_freeze(repo_root, candidate)
    assert manifest["candidate_id"] == CANDIDATE_ID
    assert manifest["candidate_file_sha256"] == file_sha256(
        repo_root / candidate_module.CANDIDATE_PATH
    )
    assert manifest["canonical_candidate_hash"] == canonical_candidate_hash(candidate)


def test_candidate_byte_mutation_after_freeze_is_rejected(repo_root, tmp_path, monkeypatch):
    candidate = build_candidate(repo_root)
    path = tmp_path / "candidate.json"
    monkeypatch.setattr(candidate_module, "CANDIDATE_PATH", path)
    _write(path, candidate)
    manifest = build_candidate_freeze(repo_root, candidate)
    _write(path, candidate, compact=True)
    errors = validate_candidate_freeze(repo_root, manifest)
    assert "C1_CANDIDATE_FILE_SHA256_MISMATCH" in errors


def test_candidate_semantic_mutation_after_freeze_is_rejected(repo_root, tmp_path, monkeypatch):
    candidate = build_candidate(repo_root)
    path = tmp_path / "candidate.json"
    monkeypatch.setattr(candidate_module, "CANDIDATE_PATH", path)
    _write(path, candidate)
    manifest = build_candidate_freeze(repo_root, candidate)
    mutated = deepcopy(candidate)
    mutated["accepted_scope"] = "FORMAL_INTEGRATION"
    _write(path, mutated)
    errors = validate_candidate_freeze(repo_root, manifest)
    assert "C1_CANDIDATE_CANONICAL_HASH_MISMATCH" in errors


def test_candidate_freeze_strictly_follows_compatibility_closure(repo_root):
    candidate = build_candidate(repo_root)
    manifest = build_candidate_freeze(repo_root, candidate)
    closure = json.loads(
        (repo_root / "evals/results/phase-002d-r2a-c1/compatibility_tests/closure.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["parent_artifact_hash"] == closure["closure_hash"]
    assert manifest["artifact_sequence_index"] == closure["artifact_sequence_index"] + 1


def test_old_candidate_is_replacement_context_not_c1_evidence(repo_root):
    candidate = build_candidate(repo_root)
    old = candidate["replaces_non_active_candidate"]
    assert old["candidate_id"] == "CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A"
    assert old["classification"] == "HISTORICAL_NON_ACTIVE_CANDIDATE"
    assert candidate["candidate_id"] != old["candidate_id"]
