import copy

import pytest

from cumcm_skill_lab.adjudication.models import read_json, sha256_json
from cumcm_skill_lab.specification.authorization import candidate as candidate_module
from cumcm_skill_lab.specification.authorization.candidate import (
    CANDIDATE_PATH,
    build_authorization_candidate,
    check_or_write_authorization_candidate,
    validate_authorization_candidate,
)
from cumcm_skill_lab.specification.authorization.preconditions import (
    PRECONDITIONS_PATH,
    build_preconditions,
    check_or_write_preconditions,
    validate_preconditions_value,
)


def _rehash(value, field):
    body = copy.deepcopy(value)
    body.pop(field, None)
    value[field] = sha256_json(body)


@pytest.mark.parametrize("check_id", [f"R2A-PRE-{index:02d}" for index in range(1, 28)])
def test_all_27_authorization_preconditions_are_machine_passed(repo_root, check_id):
    record = build_preconditions(repo_root)
    check = {item["check_id"]: item for item in record["checks"]}[check_id]
    assert check["status"] == "PASS", check["observed"]
    assert check["required"] is True
    assert check["evidence_refs"]


def test_preconditions_are_hash_bound_and_reproducible(repo_root):
    record = read_json(repo_root / PRECONDITIONS_PATH)
    body = copy.deepcopy(record)
    recorded_hash = body.pop("preconditions_hash")
    assert sha256_json(body) == recorded_hash
    assert build_preconditions(repo_root) == record
    assert validate_preconditions_value(repo_root, record) == []
    assert check_or_write_preconditions(repo_root, check=True)["status"] == "PASS"


def test_preconditions_preserve_material_unknowns(repo_root):
    unknowns = set(build_preconditions(repo_root)["unknowns"])
    assert unknowns == {
        "CLEAN_ROOM_LEGAL_COMPLIANCE_NOT_PROVEN",
        "HIDDEN_VAULT_OS_ISOLATION_NOT_VERIFIED",
        "PROTOTYPE_EFFECTIVENESS_UNMEASURED",
        "MONETARY_COST_UNKNOWN",
    }


@pytest.mark.parametrize(
    "mutation",
    ["missing_check", "failed_check", "wrong_count", "wrong_failure_list", "stale_hash"],
)
def test_precondition_record_mutations_fail_closed(repo_root, mutation):
    record = build_preconditions(repo_root)
    if mutation == "missing_check":
        record["checks"].pop()
        record["required_check_count"] = 26
        record["passed_check_count"] = 26
    elif mutation == "failed_check":
        record["checks"][0]["status"] = "FAIL"
    elif mutation == "wrong_count":
        record["passed_check_count"] = 26
    elif mutation == "wrong_failure_list":
        record["failed_check_ids"] = ["R2A-PRE-01"]
    else:
        record["passed_check_count"] = 26
        assert "R2A_PRECONDITION_HASH_MISMATCH" in validate_preconditions_value(repo_root, record)
        return
    _rehash(record, "preconditions_hash")
    assert validate_preconditions_value(repo_root, record)


def test_candidate_is_data_driven_non_active_and_schema_valid(repo_root):
    candidate = read_json(repo_root / CANDIDATE_PATH)
    assert build_authorization_candidate(repo_root) == candidate
    assert validate_authorization_candidate(repo_root, candidate) == []
    assert check_or_write_authorization_candidate(repo_root, check=True)["status"] == "PASS"
    assert candidate["record_type"] == "SHADOW_AUTHORIZATION_CANDIDATE_NOT_ACTIVE"
    assert candidate["active"] is False
    assert candidate["formal_state_transition_performed"] is False
    assert candidate["proposed_automated_decision"]["decision"] == "AUTOMATED_ACCEPTED"
    assert candidate["proposed_accepted_scope"] == "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY"


def test_candidate_retest_is_derived_from_failed_precondition(repo_root, monkeypatch):
    preconditions = build_preconditions(repo_root)
    preconditions["checks"][0]["status"] = "FAIL"
    preconditions["passed_check_count"] = 26
    preconditions["failed_check_ids"] = ["R2A-PRE-01"]
    preconditions["all_required_pass"] = False
    preconditions["eligibility"] = "RETEST_REQUIRED"
    _rehash(preconditions, "preconditions_hash")
    monkeypatch.setattr(candidate_module, "build_preconditions", lambda _root: preconditions)
    candidate = candidate_module.build_authorization_candidate(repo_root)
    core = candidate["proposed_automated_decision"]
    assert core["decision"] == "RETEST_REQUIRED"
    assert core["hard_gate_status"] == "FAIL"
    assert candidate["proposed_accepted_scope"] is None
    assert candidate["proposed_next_phase_allowed"].endswith("AUTHORIZATION-CLOSURE")


def test_candidate_stale_is_derived_from_stale_preconditions(repo_root, monkeypatch):
    preconditions = build_preconditions(repo_root)
    preconditions["all_required_pass"] = False
    preconditions["eligibility"] = "STALE"
    preconditions["failed_check_ids"] = ["R2A-PRE-01"]
    monkeypatch.setattr(candidate_module, "build_preconditions", lambda _root: preconditions)
    candidate = candidate_module.build_authorization_candidate(repo_root)
    assert candidate["proposed_automated_decision"]["decision"] == "STALE"
    assert candidate["proposed_next_phase_allowed"] is None


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("active", True),
        ("formal_state_transition_performed", True),
        ("selected_architecture", "ARCH-W1-WORKFLOW-ONLY-GUARDS"),
        ("base_selected", True),
        ("third_party_integrated", True),
        ("majority_vote_used", True),
        ("scope_hash", "0" * 64),
    ],
)
def test_candidate_boundary_mutations_fail_closed(repo_root, field, invalid):
    candidate = build_authorization_candidate(repo_root)
    candidate[field] = invalid
    _rehash(candidate, "candidate_hash")
    assert validate_authorization_candidate(repo_root, candidate)


def test_historical_candidate_does_not_replace_c2_active_decision(repo_root):
    state = read_json(repo_root / "state/project_state.json")
    candidate = read_json(repo_root / CANDIDATE_PATH)
    assert state["technical_adjudication_status"] == "SHADOW_PROTOTYPE_AUTHORIZATION_COMPLETE"
    assert state["next_phase_allowed"] == "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"
    assert candidate["proposed_authorization_id"] not in state["automated_decision_ids"]
    assert state["shadow_authorization"]["candidate_id"] != candidate["candidate_id"]
    assert state["shadow_authorization"]["active_decision_id"].endswith("R2A-C2")
