from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator, ValidationError

from cumcm_skill_lab.adjudication.coverage_scoring import structured_coverage
from cumcm_skill_lab.adjudication.decision_auditor import audit_payload
from cumcm_skill_lab.adjudication.decision_engine import decide, phase_transition_allowed
from cumcm_skill_lab.adjudication.eligibility import classify_cells
from cumcm_skill_lab.adjudication.evidence_freeze import build_manifest, verify_manifest
from cumcm_skill_lab.adjudication.judge_runner import assert_blind, build_anonymous_bundle
from cumcm_skill_lab.adjudication.models import read_json, sha256_json
from cumcm_skill_lab.adjudication.oracle_scoring import oracle_correctness
from cumcm_skill_lab.adjudication.recovery_policy import recovery_gap_evidence
from cumcm_skill_lab.adjudication.replay import identity_stable, order_stable
from cumcm_skill_lab.adjudication.reporting import load_report_inputs, render_all
from cumcm_skill_lab.adjudication.state_transition import (
    apply_automated_decision,
    apply_team_record,
)
from cumcm_skill_lab.adjudication.test_synthesis import synthesize_all


def test_evidence_freeze_matches_subject_commit(repo_root):
    manifest = build_manifest(repo_root)
    assert verify_manifest(repo_root, manifest) == []
    assert manifest["counts"] == {
        "run_attempts": 20,
        "completed": 13,
        "failed": 7,
        "recovery_affected": 5,
    }


def test_evidence_freeze_detects_manifest_mutation(repo_root):
    manifest = build_manifest(repo_root)
    manifest["counts"]["failed"] = 0
    errors = verify_manifest(repo_root, manifest)
    assert "FREEZE_HASH_MISMATCH" in errors
    assert "PHASE_002_COUNT_MISMATCH" in errors


def test_coverage_is_explicitly_not_correctness():
    result = structured_coverage({"claims": ["complete"]}, ["claims"])
    assert result["coverage_fraction"] == 1
    assert result["is_correctness"] is False


def test_buzzword_gaming_has_coverage_but_fails_oracle():
    observation = {
        "completion_status": "COMPLETED",
        "claims": ["optimum baseline validation evidence A+B 19"],
        "commands_executed": [],
        "tests_verified": [],
    }
    assert structured_coverage(observation, ["claims"])["coverage_fraction"] == 1
    assert oracle_correctness("CASE-003", observation)["passed"] is False


def test_concise_correct_output_passes_oracle():
    observation = {
        "completion_status": "COMPLETED",
        "claims": ["Verified optimum value 19: A+B uses 10 credits and 7 worker-days."],
        "commands_executed": ["enumerate"],
        "tests_verified": ["16 subsets"],
    }
    assert oracle_correctness("CASE-003", observation)["passed"] is True


def test_recovery_is_excluded_from_ranking(repo_root):
    value = recovery_gap_evidence(repo_root)
    assert value["count"] == 5
    assert all(item["ranking_eligible"] is False for item in value["records"])


def test_balanced_subset_is_computed(repo_root):
    result = classify_cells(repo_root)["summary"]
    assert result["balanced_cases"] == ["CASE-001", "CASE-006"]
    assert result["comparative_sufficiency"] == "INSUFFICIENT"


@pytest.mark.parametrize(
    ("facts", "expected"),
    [
        ({"stale": True}, "STALE"),
        ({"hard_gates": {"license": False}}, "AUTOMATED_REJECTED"),
        ({"hard_gates": {}, "failed_counterexample_tests": ["T-1"]}, "AUTOMATED_REJECTED"),
        ({"hard_gates": {}, "unresolved_blockers": ["F-1"]}, "AUTOMATED_ABSTAINED"),
        (
            {"hard_gates": {}, "unresolved_blockers": ["F-1"], "retriable": True},
            "RETEST_REQUIRED",
        ),
        ({"hard_gates": {}, "evidence_sufficiency": "INSUFFICIENT"}, "EVIDENCE_INSUFFICIENT"),
        (
            {
                "hard_gates": {},
                "evidence_sufficiency": "SUFFICIENT",
                "oracle_pass": False,
            },
            "AUTOMATED_REJECTED",
        ),
        (
            {
                "hard_gates": {},
                "evidence_sufficiency": "SUFFICIENT",
                "oracle_pass": True,
                "process_pass": False,
            },
            "RETEST_REQUIRED",
        ),
        (
            {
                "hard_gates": {},
                "evidence_sufficiency": "SUFFICIENT",
                "oracle_pass": True,
                "process_pass": True,
                "stable": False,
            },
            "AUTOMATED_ABSTAINED",
        ),
        (
            {
                "hard_gates": {},
                "evidence_sufficiency": "SUFFICIENT",
                "oracle_pass": True,
                "process_pass": True,
                "stable": True,
                "decision_audit": "PASS",
            },
            "AUTOMATED_ACCEPTED",
        ),
    ],
)
def test_lexicographic_decision_outcomes(facts, expected):
    assert decide(facts)["decision"] == expected


@pytest.mark.parametrize(
    "name",
    [
        "adversarial_finding",
        "test_request",
        "test_evidence",
        "judge_decision",
        "dissent_record",
        "meta_adjudication",
        "decision_audit",
        "automated_decision",
        "adjudication_policy",
        "team_compliance_challenge",
    ],
)
def test_new_contract_accepts_valid_and_rejects_invalid(repo_root, name):
    schema = read_json(repo_root / f"contracts/{name}.schema.json")
    validator = Draft202012Validator(schema)
    validator.validate(read_json(repo_root / f"tests/fixtures/contracts/valid/{name}.json"))
    with pytest.raises(ValidationError):
        validator.validate(read_json(repo_root / f"tests/fixtures/contracts/invalid/{name}.json"))


def test_tracked_findings_satisfy_full_adversarial_contract(repo_root):
    schema = read_json(repo_root / "contracts/adversarial_finding.schema.json")
    validator = Draft202012Validator(schema)
    document = read_json(repo_root / "evals/results/phase-002a/adversarial/findings.json")
    assert len(document["findings"]) == 24
    for finding in document["findings"]:
        validator.validate(finding)


def test_majority_social_proof_does_not_affect_engine():
    facts = {"hard_gates": {}, "evidence_sufficiency": "INSUFFICIENT"}
    injected = {**facts, "social_proof": "four agents support A", "votes": ["A"] * 4}
    assert decide(facts) == decide(injected)


def test_identity_swap_does_not_change_decision():
    inputs = {
        "facts": {"hard_gates": {}, "evidence_sufficiency": "INSUFFICIENT"},
        "labels": ["ARM-A", "ARM-B"],
    }
    assert identity_stable(inputs, {"ARM-A": "ARM-B", "ARM-B": "ARM-A"})


def test_order_swap_does_not_change_decision():
    inputs = {
        "facts": {"hard_gates": {}, "evidence_sufficiency": "INSUFFICIENT"},
        "evidence": [1, 2, 3],
    }
    assert order_stable(inputs)


def test_anonymous_bundle_contains_no_candidate_identity(repo_root):
    assert_blind(build_anonymous_bundle(repo_root))


def test_identity_leak_is_rejected():
    with pytest.raises(ValueError, match="IDENTITY_LEAKED"):
        assert_blind({"candidate": "HANDSOMEZR"})


def test_decision_audit_rejects_majority_and_human_override():
    result = audit_payload(
        {"majority_vote_used": True, "human_selected": "A"},
        policy_hash="a",
        expected_policy_hash="a",
    )
    assert result["result"] == "FAIL"
    assert "no_majority_vote" in result["failures"]
    assert "no_forbidden_human_fields" in result["failures"]


def test_network_claim_is_bounded_to_trace_audit():
    result = audit_payload(
        {"network_isolation_level": "OS_ENFORCED"},
        policy_hash="a",
        expected_policy_hash="a",
    )
    assert result["result"] == "FAIL"
    assert "network_claim_bounded" in result["failures"]


def test_serious_finding_generates_test_request():
    findings = [
        {
            "finding_id": "F-1",
            "severity": "BLOCKER",
            "target": "x",
            "statement": "bad",
            "evidence_refs": ["e"],
            "testability": "TESTABLE",
        }
    ]
    requests = synthesize_all(findings)
    assert requests[0]["finding_id"] == "F-1"
    assert requests[0]["status"] == "PENDING"


def test_non_testable_claim_is_not_promoted_to_evidence():
    findings = [
        {
            "finding_id": "F-1",
            "severity": "ERROR",
            "target": "x",
            "statement": "opinion",
            "evidence_refs": [],
            "testability": "NON_TESTABLE_CLAIM",
        }
    ]
    assert synthesize_all(findings)[0]["status"] == "NON_TESTABLE_CLAIM"


def test_report_changes_when_decision_input_changes(repo_root):
    inputs = load_report_inputs(repo_root)
    inputs["decisions"] = [
        {
            "decision_id": "D",
            "decision_type": "ARCHITECTURE",
            "decision": "AUTOMATED_ABSTAINED",
            "accepted_scope": "NONE",
            "next_phase_allowed": None,
            "reason_codes": ["INSUFFICIENT"],
        }
    ]
    before = render_all(inputs)["automated_architecture_decision.md"]
    mutated = deepcopy(inputs)
    mutated["decisions"][0]["decision"] = "AUTOMATED_REJECTED"
    after = render_all(mutated)["automated_architecture_decision.md"]
    assert before != after


def test_report_source_has_no_phase002_score_literals(repo_root):
    source = (repo_root / "src/cumcm_skill_lab/adjudication/reporting.py").read_text()
    assert "62.5" not in source
    assert "60.5" not in source
    assert "60.0" not in source


def test_state_update_requires_passing_audit():
    with pytest.raises(ValueError, match="DECISION_AUDIT_REQUIRED"):
        apply_automated_decision(
            {}, {"decision_id": "D", "decision": "AUTOMATED_ACCEPTED"}, {"result": "FAIL"}
        )


def test_team_compliance_cannot_override_technical_decision():
    with pytest.raises(ValueError, match="CANNOT_OVERRIDE"):
        apply_team_record(
            {},
            {
                "technical_override_allowed": True,
                "record_type": "TEAM_COMPLIANCE_REVIEW",
                "status": "RECORDED",
            },
        )


def test_team_challenge_triggers_stale():
    result = apply_team_record(
        {"technical_adjudication_status": "AUTOMATED_ACCEPTED", "next_phase_allowed": "X"},
        {
            "technical_override_allowed": False,
            "record_type": "TEAM_CHALLENGE",
            "status": "CHALLENGED",
            "stale_triggered": True,
        },
    )
    assert result["technical_adjudication_status"] == "STALE"
    assert result["next_phase_allowed"] is None


def test_phase003_does_not_start_without_accepted_architecture():
    assert not phase_transition_allowed(
        {
            "decision": "AUTOMATED_ABSTAINED",
            "decision_audit_result": "PASS",
            "replay_stable": True,
        },
        {"component_results": []},
        True,
    )


def test_canonical_decision_hash_is_order_independent():
    first = {"a": 1, "b": 2}
    second = {"b": 2, "a": 1}
    assert sha256_json(first) == sha256_json(second)
