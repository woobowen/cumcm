import json
from copy import deepcopy

from cumcm_skill_lab.authorization_c1.compatibility_audits import (
    FIRST_ROUND_ROLES,
    build_compatibility_closure,
    normalize_audit,
    validate_audit,
)


def _raw(repo_root, role):
    return json.loads(
        (repo_root / f"evals/results/phase-002d-r2a-c1/subagent_outputs/raw/{role}.json").read_text(
            encoding="utf-8"
        )
    )


def test_native_audit_outputs_are_hash_bound_and_schema_valid(repo_root):
    for role in FIRST_ROUND_ROLES:
        value = normalize_audit(_raw(repo_root, role))
        assert validate_audit(repo_root, value, role) == []


def test_native_audit_hash_detects_transport_mutation(repo_root):
    role = "historical_freeze_semantics_auditor"
    value = normalize_audit(_raw(repo_root, role))
    value["verdict"] = "PASS"
    assert "C1_NATIVE_AUDIT_OUTPUT_HASH_MISMATCH" in validate_audit(repo_root, value, role)


def test_candidate_abstention_is_not_compatibility_pass_evidence(repo_root):
    audits = {role: normalize_audit(_raw(repo_root, role)) for role in FIRST_ROUND_ROLES}
    closure = build_compatibility_closure(repo_root, audits)
    assert closure["candidate_prosecutor_verdict"] == "ABSTAIN"
    assert closure["candidate_abstention_treated_as_pass"] is False
    assert len(closure["candidate_findings_deferred_to_m5_m6"]) == 6


def test_all_compatibility_serious_findings_map_to_tests(repo_root):
    audits = {role: normalize_audit(_raw(repo_root, role)) for role in FIRST_ROUND_ROLES}
    closure = build_compatibility_closure(repo_root, audits)
    closed = {item["finding_id"] for item in closure["closures"]}
    serious = {
        item["finding_id"]
        for role in (
            "historical_freeze_semantics_auditor",
            "schema_version_compatibility_auditor",
        )
        for item in audits[role]["findings"]
        if item["severity"] in {"BLOCKER", "ERROR"}
    }
    assert serious <= closed
    assert closure["unresolved_compatibility_blockers"] == []
    assert closure["result"] == "PASS"


def test_native_audit_role_substitution_is_rejected(repo_root):
    role = "historical_freeze_semantics_auditor"
    value = normalize_audit(_raw(repo_root, role))
    mutated = deepcopy(value)
    mutated["role"] = "schema_version_compatibility_auditor"
    mutated = normalize_audit(mutated)
    assert "C1_NATIVE_AUDIT_ROLE_MISMATCH" in validate_audit(repo_root, mutated, role)
