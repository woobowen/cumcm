import copy

import pytest

from cumcm_skill_lab.adjudication.models import read_json, sha256_json
from cumcm_skill_lab.specification.authorization.native_audits import (
    FIRST_ROUND_ROLES,
    INPUT_ROOT,
    OUTPUT_ROOT,
    RAW_OUTPUT_ROOT,
    build_audit_bundle,
    check_or_write_first_round_bundles,
    check_or_write_normalized_first_round_outputs,
    normalize_subagent_output,
    validate_subagent_output,
)


@pytest.mark.parametrize("role", FIRST_ROUND_ROLES)
def test_first_round_bundle_is_deterministic_and_hash_bound(repo_root, role):
    recorded = read_json(repo_root / INPUT_ROOT / f"{role}.json")
    assert build_audit_bundle(repo_root, role) == recorded
    body = copy.deepcopy(recorded)
    recorded_hash = body.pop("bundle_hash")
    assert sha256_json(body) == recorded_hash


@pytest.mark.parametrize("role", FIRST_ROUND_ROLES)
def test_first_round_bundle_is_read_only_peer_invisible(repo_root, role):
    bundle = read_json(repo_root / INPUT_ROOT / f"{role}.json")
    constraints = bundle["constraints"]
    assert constraints["read_only"] is True
    assert constraints["writes_allowed"] is False
    assert constraints["peer_output_access"] == "NONE"
    assert constraints["expected_conclusion_visible"] is False
    assert not any("subagent_outputs" in path for path in bundle["allowed_paths"])


@pytest.mark.parametrize("role", FIRST_ROUND_ROLES)
def test_first_round_bundle_denies_external_execution_surfaces(repo_root, role):
    constraints = read_json(repo_root / INPUT_ROOT / f"{role}.json")["constraints"]
    assert constraints["nested_codex_allowed"] is False
    assert constraints["web_allowed"] is False
    assert constraints["mcp_allowed"] is False
    assert constraints["api_allowed"] is False
    assert constraints["majority_vote_allowed"] is False


def test_all_first_round_bundles_check_without_writes(repo_root):
    assert check_or_write_first_round_bundles(repo_root, check=True)["status"] == "PASS"


def _sample_output(repo_root, role):
    bundle = build_audit_bundle(repo_root, role)
    value = {
        "audit_id": f"AUDIT-{role}",
        "role": role,
        "round": "FIRST_ROUND",
        "independent": True,
        "read_only": True,
        "peer_output_access": "NONE",
        "model": "INHERITED_PARENT_UNEXPOSED",
        "reasoning_setting": "INHERITED_PARENT_UNEXPOSED",
        "bundle_id": bundle["bundle_id"],
        "bundle_hash": bundle["bundle_hash"],
        "verdict": "PASS",
        "findings": [],
        "blockers": [],
        "cost_assessment": None,
        "writes_observed": False,
        "nested_codex_used": False,
        "api_key_used": False,
        "api_calls": 0,
        "web_used": False,
        "mcp_used": False,
        "majority_vote_used": False,
        "expected_conclusion_visible": False,
        "uncertainties": [],
        "created_at": "2026-09-03T03:00:00+08:00",
    }
    value["output_hash"] = sha256_json(value)
    return value


@pytest.mark.parametrize("role", FIRST_ROUND_ROLES)
def test_r2a_subagent_output_contract_accepts_hash_bound_output(repo_root, role):
    assert validate_subagent_output(repo_root, _sample_output(repo_root, role), role) == []


def test_r2a_subagent_output_rejects_bundle_substitution(repo_root):
    role = FIRST_ROUND_ROLES[0]
    value = _sample_output(repo_root, role)
    value["bundle_hash"] = "0" * 64
    value["output_hash"] = sha256_json(
        {key: item for key, item in value.items() if key != "output_hash"}
    )
    assert "R2A_SUBAGENT_BUNDLE_MISMATCH" in validate_subagent_output(repo_root, value, role)


def test_r2a_subagent_output_rejects_serious_finding_without_test(repo_root):
    role = FIRST_ROUND_ROLES[0]
    value = _sample_output(repo_root, role)
    value["findings"] = [
        {
            "finding_id": "R2A-TEST-B1",
            "severity": "BLOCKER",
            "target": "DAG",
            "statement": "synthetic serious finding",
            "counterexample": "synthetic counterexample",
            "evidence_refs": ["authorization_dependency_graph.json"],
            "file_references": ["evals/results/phase-002d-r2a/authorization_dependency_graph.json"],
            "testability": "TESTABLE",
            "required_test": None,
            "pass_condition": "synthetic pass condition",
            "status": "OPEN",
        }
    ]
    value["output_hash"] = sha256_json(
        {key: item for key, item in value.items() if key != "output_hash"}
    )
    assert "R2A_SUBAGENT_SERIOUS_FINDING_WITHOUT_TEST" in validate_subagent_output(
        repo_root, value, role
    )


@pytest.mark.parametrize("role", FIRST_ROUND_ROLES)
def test_raw_first_round_output_is_preserved_and_normalized(repo_root, role):
    raw = read_json(repo_root / RAW_OUTPUT_ROOT / f"{role}.json")
    normalized = read_json(repo_root / OUTPUT_ROOT / f"{role}.json")
    assert raw["output_hash"] == "0" * 64
    assert normalize_subagent_output(raw) == normalized
    assert validate_subagent_output(repo_root, normalized, role) == []


def test_all_normalized_first_round_outputs_check_without_writes(repo_root):
    result = check_or_write_normalized_first_round_outputs(repo_root, check=True)
    assert result["status"] == "PASS", result["errors"]
