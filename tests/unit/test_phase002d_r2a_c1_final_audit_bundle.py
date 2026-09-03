import json
from copy import deepcopy

from cumcm_skill_lab.authorization_c1.candidate_evidence import CLOSURE_PATH
from cumcm_skill_lab.authorization_c1.candidate_freeze import CANDIDATE_PATH, FREEZE_PATH
from cumcm_skill_lab.authorization_c1.final_audit_bundle import (
    ALLOWED_PATHS,
    BUNDLE_PATH,
    build_final_audit_bundle,
    validate_final_audit_bundle,
)
from cumcm_skill_lab.authorization_c1.models import file_sha256, sha256_json


def _read(repo_root, path):
    return json.loads((repo_root / path).read_text(encoding="utf-8"))


def _rehash(value):
    value["bundle_hash"] = sha256_json(
        {key: item for key, item in value.items() if key != "bundle_hash"}
    )
    return value


def test_c1_final_audit_bundle_validates(repo_root):
    assert validate_final_audit_bundle(repo_root, _read(repo_root, BUNDLE_PATH)) == []


def test_bundle_is_deterministically_reproducible(repo_root):
    assert _read(repo_root, BUNDLE_PATH) == build_final_audit_bundle(repo_root)


def test_bundle_contains_required_exact_candidate_fields(repo_root):
    bundle = _read(repo_root, BUNDLE_PATH)
    freeze = _read(repo_root, FREEZE_PATH)
    assert bundle["candidate_id"] == freeze["candidate_id"]
    assert bundle["candidate_file_sha256"] == file_sha256(repo_root / CANDIDATE_PATH)
    assert bundle["canonical_candidate_hash"] == freeze["canonical_candidate_hash"]
    assert bundle["candidate_freeze_hash"] == freeze["freeze_hash"]


def test_bundle_is_monotonic_child_of_candidate_closure(repo_root):
    bundle = _read(repo_root, BUNDLE_PATH)
    closure = _read(repo_root, CLOSURE_PATH)
    assert bundle["parent_artifact_hash"] == closure["closure_hash"]
    assert bundle["artifact_sequence_index"] == 9


def test_bundle_path_hashes_cover_exact_allowlist(repo_root):
    bundle = _read(repo_root, BUNDLE_PATH)
    assert bundle["allowed_paths"] == list(ALLOWED_PATHS)
    assert set(bundle["path_hashes"]) == set(ALLOWED_PATHS)
    assert all(
        digest == file_sha256(repo_root / path) for path, digest in bundle["path_hashes"].items()
    )


def test_bundle_candidate_byte_substitution_is_rejected(repo_root):
    bundle = deepcopy(_read(repo_root, BUNDLE_PATH))
    bundle["candidate_file_sha256"] = "0" * 64
    errors = validate_final_audit_bundle(repo_root, _rehash(bundle))
    assert "C1_BOUND_CANDIDATE_FILE_SHA256_MISMATCH" in errors
    assert "C1_FINAL_BUNDLE_NOT_REPRODUCIBLE" in errors


def test_bundle_canonical_hash_substitution_is_rejected(repo_root):
    bundle = deepcopy(_read(repo_root, BUNDLE_PATH))
    bundle["canonical_candidate_hash"] = "0" * 64
    errors = validate_final_audit_bundle(repo_root, _rehash(bundle))
    assert "C1_BOUND_CANONICAL_CANDIDATE_HASH_MISMATCH" in errors


def test_bundle_parent_substitution_is_rejected(repo_root):
    bundle = deepcopy(_read(repo_root, BUNDLE_PATH))
    bundle["parent_artifact_hash"] = "0" * 64
    errors = validate_final_audit_bundle(repo_root, _rehash(bundle))
    assert "C1_BOUND_PARENT_ARTIFACT_HASH_MISMATCH" in errors


def test_bundle_sequence_inversion_is_rejected(repo_root):
    bundle = deepcopy(_read(repo_root, BUNDLE_PATH))
    bundle["artifact_sequence_index"] = 8
    errors = validate_final_audit_bundle(repo_root, _rehash(bundle))
    assert "C1_BOUND_ARTIFACT_SEQUENCE_MISMATCH" in errors


def test_bundle_path_hash_substitution_is_rejected(repo_root):
    bundle = deepcopy(_read(repo_root, BUNDLE_PATH))
    target = CANDIDATE_PATH.as_posix()
    bundle["path_hashes"][target] = "0" * 64
    errors = validate_final_audit_bundle(repo_root, _rehash(bundle))
    assert f"C1_FINAL_BUNDLE_PATH_HASH_MISMATCH:{target}" in errors


def test_bundle_has_no_unresolved_findings(repo_root):
    bundle = _read(repo_root, BUNDLE_PATH)
    assert bundle["unresolved_findings"] == []
    assert len(bundle["test_evidence_hashes"]) == 30


def test_bundle_never_selects_architecture_or_routes_phase003(repo_root):
    bundle = _read(repo_root, BUNDLE_PATH)
    assert "ARCHITECTURE_SELECTION" in bundle["review_requirements"]
    assert "PHASE_003_ROUTE" in bundle["review_requirements"]
    assert "THIRD_PARTY_INTEGRATION" in bundle["review_requirements"]
