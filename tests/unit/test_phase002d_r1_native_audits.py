from copy import deepcopy

import pytest

from cumcm_skill_lab.failure_aware.models import read_json, sha256_json
from cumcm_skill_lab.failure_aware.native_audits import (
    BUNDLE_ROOT,
    FIRST_ROUND_ROLES,
    build_first_round_bundles,
    check_or_write_first_round_bundles,
    validate_audit,
)


def _audit(repo_root, role):
    bundle = read_json(repo_root / BUNDLE_ROOT / f"{role}.json")
    body = {
        "audit_id": f"AUDIT-PHASE-002D-R1-{role.upper()}",
        "role": role,
        "round": "FIRST_ROUND",
        "independent": True,
        "read_only": True,
        "identity_blind": True,
        "peer_output_access": "NONE",
        "expected_conclusion_visible": False,
        "model": "INHERITED_NATIVE_SUBAGENT",
        "reasoning_setting": "INHERITED_PARENT_UNEXPOSED",
        "bundle_id": bundle["bundle_id"],
        "bundle_hash": bundle["bundle_hash"],
        "verdict": "PASS",
        "findings": [],
        "blockers": [],
        "cost_assessment": None,
        "writes_observed": False,
        "nested_codex_used": False,
        "web_used": False,
        "mcp_used": False,
        "majority_vote_used": False,
        "api_key_used": False,
        "created_at": "2026-09-01T23:12:32+08:00",
    }
    return {**body, "output_hash": sha256_json(body)}


@pytest.mark.parametrize("role", FIRST_ROUND_ROLES)
def test_each_first_round_bundle_is_isolated_and_identity_blind(repo_root, role):
    bundle = build_first_round_bundles(repo_root)[role]
    assert bundle["independent"] is True
    assert bundle["read_only"] is True
    assert bundle["identity_blind"] is True
    assert bundle["peer_output_access"] == "NONE"
    assert bundle["peer_outputs_visible"] is False
    assert bundle["expected_conclusion_visible"] is False


@pytest.mark.parametrize("role", FIRST_ROUND_ROLES)
def test_each_bundle_hash_and_allowed_file_set_are_replayable(repo_root, role):
    bundle = build_first_round_bundles(repo_root)[role]
    body = dict(bundle)
    recorded_hash = body.pop("bundle_hash")
    assert sha256_json(body) == recorded_hash
    assert all((repo_root / path).is_file() for path in bundle["allowed_file_references"])
    assert all("subagent_audits/" not in path for path in bundle["allowed_file_references"])


@pytest.mark.parametrize("role", FIRST_ROUND_ROLES)
def test_schema_valid_minimal_native_audit_passes_role_validation(repo_root, role):
    assert validate_audit(repo_root, _audit(repo_root, role), role=role) == []


def test_written_bundles_remain_frozen_and_remediation_is_test_bound(repo_root):
    result = check_or_write_first_round_bundles(repo_root, check=True)
    assert result["status"] == "PASS"
    assert result["errors"] == []
    assert result["roles"] == list(FIRST_ROUND_ROLES)
    assert result["all_serious_findings_closed"] is True
    assert set(result["post_audit_remediation_drift"]) == {
        "src/cumcm_skill_lab/failure_aware/retry_bias.py",
        "src/cumcm_skill_lab/failure_aware/slot_matrix.py",
        "evals/results/phase-002d-r1/retry_bias/retry_bias_audit.json",
        "evals/results/phase-002d-r1/slot_outcomes/slot_outcome_matrix.json",
        "evals/results/phase-002d-r1/slot_outcomes/slot_outcome_matrix.csv",
        "evals/results/phase-002d-r1/slot_outcomes/records/CASE-004-ARM-A-R2.json",
        "plans/active/PLAN-0002D-R1-failure-aware-outcomes.md",
    }


@pytest.mark.parametrize(
    ("field", "value", "error_fragment"),
    [
        ("identity_blind", False, "SUBAGENT_SCHEMA"),
        ("peer_output_access", "FROZEN_PREDECESSORS_ONLY", "SUBAGENT_PEER_ACCESS_INVALID"),
        ("bundle_hash", "0" * 64, "SUBAGENT_BUNDLE_HASH_MISMATCH"),
        ("writes_observed", True, "SUBAGENT_SCHEMA"),
        ("nested_codex_used", True, "SUBAGENT_SCHEMA"),
        ("web_used", True, "SUBAGENT_SCHEMA"),
        ("mcp_used", True, "SUBAGENT_SCHEMA"),
        ("majority_vote_used", True, "SUBAGENT_SCHEMA"),
        ("api_key_used", True, "SUBAGENT_SCHEMA"),
    ],
)
def test_native_audit_prohibited_mutations_fail_closed(repo_root, field, value, error_fragment):
    role = FIRST_ROUND_ROLES[0]
    audit = _audit(repo_root, role)
    audit[field] = value
    body = dict(audit)
    body.pop("output_hash")
    audit["output_hash"] = sha256_json(body)
    assert any(error_fragment in item for item in validate_audit(repo_root, audit, role=role))


def test_native_audit_output_hash_tampering_fails_closed(repo_root):
    role = FIRST_ROUND_ROLES[0]
    audit = _audit(repo_root, role)
    audit["verdict"] = "ABSTAIN"
    assert f"SUBAGENT_OUTPUT_HASH_MISMATCH:{role}" in validate_audit(repo_root, audit, role=role)


def test_native_audit_unknown_references_fail_closed(repo_root):
    role = FIRST_ROUND_ROLES[0]
    audit = _audit(repo_root, role)
    audit["findings"] = [
        {
            "finding_id": "UNKNOWN-REF",
            "severity": "ERROR",
            "target": "reference validation",
            "statement": "synthetic unknown references",
            "counterexample": None,
            "evidence_refs": ["UNKNOWN-EVIDENCE"],
            "file_references": ["unknown/file.json"],
            "testability": "TESTABLE",
            "required_test": "tests/unit/test_phase002d_r1_native_audits.py",
            "pass_condition": "unknown references fail",
            "status": "OPEN",
        }
    ]
    body = deepcopy(audit)
    body.pop("output_hash")
    audit["output_hash"] = sha256_json(body)
    errors = validate_audit(repo_root, audit, role=role)
    assert any("SUBAGENT_EVIDENCE_REF_INVALID" in item for item in errors)
    assert any("SUBAGENT_FILE_REF_INVALID" in item for item in errors)


def test_native_audit_pass_with_blocker_fails_closed(repo_root):
    role = FIRST_ROUND_ROLES[0]
    audit = _audit(repo_root, role)
    audit["blockers"] = ["MISSING-FINDING"]
    body = dict(audit)
    body.pop("output_hash")
    audit["output_hash"] = sha256_json(body)
    errors = validate_audit(repo_root, audit, role=role)
    assert f"SUBAGENT_BLOCKER_REF_INVALID:{role}" in errors
    assert f"SUBAGENT_PASS_WITH_BLOCKER:{role}" in errors
