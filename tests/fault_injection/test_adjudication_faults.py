import pytest

from cumcm_skill_lab.adjudication.decision_auditor import audit_payload
from cumcm_skill_lab.adjudication.decision_engine import decide
from cumcm_skill_lab.adjudication.judge_runner import assert_blind
from cumcm_skill_lab.adjudication.state_transition import apply_automated_decision


@pytest.mark.parametrize(
    ("fault", "kwargs"),
    [
        ("rules_frozen", {"policy_hash": "a", "expected_policy_hash": "b"}),
        (
            "recovery_not_ranked",
            {"policy_hash": "a", "expected_policy_hash": "a", "recovery_ranked": True},
        ),
        (
            "candidate_anonymous",
            {"policy_hash": "a", "expected_policy_hash": "a", "identity_leaked": True},
        ),
        (
            "replay_hash_verified",
            {
                "policy_hash": "a",
                "expected_policy_hash": "a",
                "replay_hash_verified": False,
            },
        ),
        (
            "raw_trace_not_tracked",
            {"policy_hash": "a", "expected_policy_hash": "a", "raw_trace_tracked": True},
        ),
    ],
)
def test_auditor_detects_fault(fault, kwargs):
    result = audit_payload({}, **kwargs)
    assert result["result"] == "FAIL"
    assert fault in result["failures"]


def test_majority_wrong_minority_counterexample_wins():
    facts = {
        "hard_gates": {},
        "evidence_sufficiency": "SUFFICIENT",
        "oracle_pass": True,
        "process_pass": True,
        "stable": True,
        "decision_audit": "PASS",
        "votes": ["ACCEPT", "ACCEPT", "ACCEPT"],
        "failed_counterexample_tests": ["minority-counterexample"],
    }
    assert decide(facts)["decision"] == "AUTOMATED_REJECTED"


def test_hard_failure_cannot_be_averaged_away():
    facts = {
        "hard_gates": {"leakage": False},
        "evidence_sufficiency": "SUFFICIENT",
        "oracle_pass": True,
        "soft_score": 100,
    }
    assert decide(facts)["decision"] == "AUTOMATED_REJECTED"


def test_all_candidates_can_be_rejected():
    decisions = [
        decide({"hard_gates": {"license": False}}),
        decide({"hard_gates": {"leakage": False}}),
    ]
    assert all(item["decision"] == "AUTOMATED_REJECTED" for item in decisions)


def test_auditor_rejects_threshold_change():
    result = audit_payload({}, policy_hash="changed", expected_policy_hash="frozen")
    assert result["result"] == "FAIL"


def test_orchestrator_rejects_audit_for_different_decision():
    with pytest.raises(ValueError, match="DECISION_AUDIT_REQUIRED"):
        apply_automated_decision(
            {},
            {"decision_id": "D-1", "decision": "AUTOMATED_ACCEPTED"},
            {"decision_id": "D-2", "result": "PASS"},
        )


@pytest.mark.parametrize("identity", ["YUSHUI", "HANDSOMEZR", "woobowen"])
def test_candidate_identity_injection_fails(identity):
    with pytest.raises(ValueError, match="IDENTITY_LEAKED"):
        assert_blind({"social_proof": f"Other agents chose {identity}"})
