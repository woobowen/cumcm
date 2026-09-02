import copy

from cumcm_skill_lab.adjudication.models import read_json, sha256_json
from cumcm_skill_lab.specification.authorization.candidate import build_authorization_candidate
from cumcm_skill_lab.specification.authorization.final_audit import (
    FINAL_BUNDLE_PATH,
    REPLAY_INPUTS_PATH,
    STATE_PROPOSAL_PATH,
    recorded_final_audit_bundle,
)
from cumcm_skill_lab.specification.authorization.native_audits import (
    FINAL_ROLE,
    normalize_subagent_output,
    validate_subagent_output,
)


def test_failed_remediation_bundle_is_preserved_but_not_current(repo_root):
    state_proposal = read_json(repo_root / STATE_PROPOSAL_PATH)
    current_candidate = build_authorization_candidate(repo_root)
    audit = read_json(repo_root / "evals/results/phase-002d-r2a/authorization_audit/audit.json")
    assert state_proposal["candidate_hash"] != current_candidate["candidate_hash"]
    assert audit["verdict"] == "RETEST_REQUIRED"
    assert audit["blockers"] == ["R2A-FINAL-002"]


def test_final_bundle_is_hash_bound_and_allowlisted(repo_root):
    recorded = recorded_final_audit_bundle(repo_root)
    body = copy.deepcopy(recorded)
    recorded_hash = body.pop("bundle_hash")
    assert sha256_json(body) == recorded_hash
    assert set(recorded["allowed_paths"]) == set(recorded["path_hashes"])


def test_final_bundle_enforces_native_read_only_no_vote_constraints(repo_root):
    constraints = read_json(repo_root / FINAL_BUNDLE_PATH)["constraints"]
    assert constraints == {
        "abstention_allowed": True,
        "api_allowed": False,
        "expected_conclusion_visible": False,
        "fabricated_evidence_allowed": False,
        "majority_vote_allowed": False,
        "mcp_allowed": False,
        "nested_codex_allowed": False,
        "peer_output_access": "FROZEN_PREDECESSORS_ONLY",
        "read_only": True,
        "web_allowed": False,
        "writes_allowed": False,
    }


def test_state_proposal_is_non_active_and_fail_closed(repo_root):
    value = read_json(repo_root / STATE_PROPOSAL_PATH)
    body = copy.deepcopy(value)
    recorded_hash = body.pop("proposal_hash")
    assert sha256_json(body) == recorded_hash
    assert value["active"] is False
    assert value["formal_state_transition_performed"] is False
    assert value["pending_hard_gates"] == {
        "active_authorization_seal": "NOT_CREATED",
        "final_authorization_auditor": "PENDING",
        "final_replay": "NOT_RUN",
    }
    proposed = value["proposed_transition"]
    assert proposed["selected_architecture"] is None
    assert proposed["base_selected"] is False
    assert proposed["third_party_integrated"] is False
    assert proposed["phase003_prohibited"] is True


def test_replay_inputs_do_not_claim_replay_or_active_decision(repo_root):
    value = read_json(repo_root / REPLAY_INPUTS_PATH)
    body = copy.deepcopy(value)
    recorded_hash = body.pop("replay_inputs_hash")
    assert sha256_json(body) == recorded_hash
    assert value["active_decision_available"] is False
    assert value["final_audit_status"] == "PENDING"
    assert value["replay_performed"] is False
    assert len(value["permutation_plan"]) == 3


def test_final_bundle_has_no_hidden_vault_value_paths(repo_root):
    allowed = read_json(repo_root / FINAL_BUNDLE_PATH)["allowed_paths"]
    assert not any(path.startswith("benchmark-vault/") for path in allowed)
    assert not any("seed" in path.lower() or "oracle" in path.lower() for path in allowed)


def _sample_final_output(repo_root):
    bundle = recorded_final_audit_bundle(repo_root)
    value = {
        "audit_id": "R2A-AUDIT-FINAL-SHADOW-AUTHORIZATION-001",
        "role": FINAL_ROLE,
        "round": "POST_DECISION",
        "independent": True,
        "read_only": True,
        "peer_output_access": "FROZEN_PREDECESSORS_ONLY",
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
        "created_at": "2026-09-03T04:35:00+08:00",
        "output_hash": "0" * 64,
    }
    return normalize_subagent_output(value)


def test_final_output_contract_accepts_bound_post_decision_audit(repo_root):
    value = _sample_final_output(repo_root)
    assert validate_subagent_output(repo_root, value, FINAL_ROLE) == []


def test_final_output_rejects_first_round_or_peer_invisible_claim(repo_root):
    value = _sample_final_output(repo_root)
    value["round"] = "FIRST_ROUND"
    value["peer_output_access"] = "NONE"
    value = normalize_subagent_output(value)
    errors = validate_subagent_output(repo_root, value, FINAL_ROLE)
    assert "R2A_FINAL_AUDIT_ROUND_MISMATCH" in errors
    assert "R2A_FINAL_AUDIT_PEER_VISIBILITY_MISMATCH" in errors
