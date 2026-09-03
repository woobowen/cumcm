"""Fail-closed tests for the L19 C2 active authorization seal."""

from __future__ import annotations

from copy import deepcopy

from cumcm_skill_lab.authorization_c1.models import sha256_json
from cumcm_skill_lab.authorization_c2.terminal import (
    build_authorization_seal,
    validate_authorization_seal,
)


def _rehash(value):
    body = deepcopy(value)
    body.pop("authorization_hash", None)
    value["authorization_hash"] = sha256_json(body)


def test_c2_seal_binds_exact_candidate_and_passing_audit(repo_root):
    value = build_authorization_seal(repo_root)
    assert validate_authorization_seal(repo_root, value) == []
    assert value["artifact_sequence_index"] == 19
    assert value["decision"] == "AUTOMATED_ACCEPTED"
    assert value["accepted_scope"] == "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY"
    assert value["final_audit_result"] == "PASS"
    assert value["final_audit_output_hash"] == value["parent_artifact_hash"]


def test_c2_seal_uses_existing_automated_decision_contract(repo_root):
    value = build_authorization_seal(repo_root)
    assert value["automated_decision_contract"] == "contracts/automated_decision.schema.json"
    assert value["automated_decision"]["decision_id"] == value["authorization_id"]
    assert value["automated_decision"]["decision"] == value["decision"]


def test_c2_seal_preserves_superseded_and_nonactive_artifacts(repo_root):
    value = build_authorization_seal(repo_root)
    assert value["supersedes"]["historical_decision"] == "RETEST_REQUIRED"
    assert value["supersedes"]["preserved"] is True
    assert value["replaces_historical_non_active_candidate"]["preserved"] is True
    assert value["replaces_failed_c1_revision"]["preserved"] is True


def test_c2_seal_rejects_wrong_candidate_bytes(repo_root):
    value = build_authorization_seal(repo_root)
    value["candidate_file_sha256"] = "0" * 64
    _rehash(value)
    assert "C2_AUTHORIZATION_SEAL_NOT_REPRODUCIBLE" in validate_authorization_seal(repo_root, value)


def test_c2_seal_rejects_wrong_auditor_hash(repo_root):
    value = build_authorization_seal(repo_root)
    value["final_audit_output_hash"] = "0" * 64
    _rehash(value)
    assert "C2_AUTHORIZATION_SEAL_NOT_REPRODUCIBLE" in validate_authorization_seal(repo_root, value)


def test_c2_seal_rejects_scope_creep(repo_root):
    value = build_authorization_seal(repo_root)
    value["selected_architecture"] = "ARCH-W1-WORKFLOW-ONLY-GUARDS"
    value["base_selected"] = True
    _rehash(value)
    errors = validate_authorization_seal(repo_root, value)
    assert "C2_AUTHORIZATION_SCOPE_CREEP" in errors


def test_c2_seal_rejects_rehashed_historical_supersession_mutation(repo_root):
    value = build_authorization_seal(repo_root)
    value["supersedes"]["decision_hash"] = "0" * 64
    _rehash(value)
    assert "C2_AUTHORIZATION_SEAL_NOT_REPRODUCIBLE" in validate_authorization_seal(repo_root, value)
