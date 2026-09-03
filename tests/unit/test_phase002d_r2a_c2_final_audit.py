import json
from copy import deepcopy

import pytest

from cumcm_skill_lab.authorization_c1.models import sha256_json
from cumcm_skill_lab.authorization_c2.final_audit import (
    FINAL_AUDIT_PATH,
    OUTPUT_AUDIT_PATH,
    RAW_AUDIT_PATH,
    evaluate_final_audit_gate,
    validate_final_audit,
)
from cumcm_skill_lab.authorization_c2.final_audit_bundle import BUNDLE_PATH


def _read(repo_root, path):
    return json.loads((repo_root / path).read_text(encoding="utf-8"))


def _rehash(value):
    value["output_hash"] = sha256_json(
        {key: item for key, item in value.items() if key != "output_hash"}
    )
    return value


def test_c2_final_audit_is_structurally_valid_pass(repo_root):
    raw = _read(repo_root, RAW_AUDIT_PATH)
    normalized = _read(repo_root, OUTPUT_AUDIT_PATH)
    final = _read(repo_root, FINAL_AUDIT_PATH)
    assert "output_hash" not in raw
    assert normalized == final
    assert validate_final_audit(repo_root, final) == []
    assert final["verdict"] == "PASS"
    assert final["findings"] == []
    assert final["unresolved_blockers"] == []
    assert final["artifact_sequence_index"] == 18


def test_c2_final_audit_is_exact_child_of_bundle(repo_root):
    audit = _read(repo_root, FINAL_AUDIT_PATH)
    bundle = _read(repo_root, BUNDLE_PATH)
    assert audit["bundle_hash"] == bundle["bundle_hash"]
    assert audit["parent_artifact_hash"] == bundle["bundle_hash"]
    assert audit["candidate_id"] == bundle["candidate_id"]
    assert audit["candidate_file_sha256"] == bundle["candidate_file_sha256"]
    assert audit["canonical_candidate_hash"] == bundle["canonical_candidate_hash"]
    assert audit["candidate_freeze_hash"] == bundle["candidate_freeze_hash"]


@pytest.mark.parametrize("action", ["SEAL", "REPLAY", "STATE_TRANSITION"])
def test_c2_final_pass_opens_each_terminal_gate(repo_root, action):
    gate = evaluate_final_audit_gate(repo_root, action)
    assert gate["status"] == "PASS"
    assert gate["errors"] == []
    assert gate["audit_result"] == "PASS"


def test_c2_final_audit_bundle_substitution_is_rejected(repo_root):
    audit = deepcopy(_read(repo_root, FINAL_AUDIT_PATH))
    audit["bundle_hash"] = "0" * 64
    errors = validate_final_audit(repo_root, _rehash(audit))
    assert "C2_FINAL_AUDIT_BUNDLE_HASH_MISMATCH" in errors


def test_c2_final_audit_parent_or_sequence_substitution_is_rejected(repo_root):
    audit = deepcopy(_read(repo_root, FINAL_AUDIT_PATH))
    audit["parent_artifact_hash"] = "0" * 64
    audit["artifact_sequence_index"] = 17
    errors = validate_final_audit(repo_root, _rehash(audit))
    assert "C2_FINAL_AUDIT_PARENT_ARTIFACT_HASH_MISMATCH" in errors
    assert "C2_FINAL_AUDIT_ARTIFACT_SEQUENCE_INDEX_MISMATCH" in errors


def test_c2_final_pass_with_open_serious_finding_is_rejected(repo_root):
    audit = deepcopy(_read(repo_root, FINAL_AUDIT_PATH))
    audit["findings"] = [
        {
            "finding_id": "SYNTHETIC-BLOCKER",
            "severity": "BLOCKER",
            "status": "OPEN",
            "statement": "synthetic",
            "evidence_paths": ["synthetic"],
            "required_test": "SYNTHETIC-TEST",
        }
    ]
    errors = validate_final_audit(repo_root, _rehash(audit))
    assert "C2_FINAL_AUDIT_PASS_WITH_UNRESOLVED_SERIOUS_FINDING" in errors
