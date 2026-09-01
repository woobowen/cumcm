"""Adversarial unit tests for the Phase 002C deterministic evidence gate."""

from __future__ import annotations

import json
import subprocess
from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator, ValidationError

from cumcm_skill_lab.adjudication.evidence_sufficiency import (
    compute_evidence_sufficiency,
)
from cumcm_skill_lab.adjudication.models import sha256_json
from cumcm_skill_lab.adjudication.native_subagent_audits import (
    blocker_test_record,
    build_first_round_bundles,
)
from cumcm_skill_lab.adjudication.phase002c_records import (
    decision_created_at,
    evaluate_direct_adoption_gates,
)
from cumcm_skill_lab.adjudication.phase002c_replay import decision_sets_equal
from cumcm_skill_lab.adjudication.phase002c_reporting import (
    _render_expansion,
    decision_rows_as_markdown,
    runtime_facts,
)
from cumcm_skill_lab.adjudication.phase_routing import build_phase_route
from cumcm_skill_lab.adjudication.pre_adjudication import (
    build_comparative_hard_gates,
    evaluate_comparative_hard_gates,
    recovery_exclusion_passed,
    verify_input_freeze,
    write_pre_adjudication,
)
from cumcm_skill_lab.adjudication.short_circuit import evaluate_short_circuit


def _item(
    arm: str,
    case: str,
    repeat: int,
    *,
    eligible: bool = True,
    classification: str = "PRIMARY_COMPLETE",
    status: str = "COMPLETED",
    task_hash: str | None = None,
) -> dict:
    return {
        "anonymous_arm_id": arm,
        "case_id": case,
        "run_index": repeat,
        "ranking_eligible": eligible,
        "classification": classification,
        "completion_status": status,
        "task_input_hash": task_hash or f"hash-{case}",
    }


def _matrix(cases: int, repeats: int = 1) -> list[dict]:
    return [
        _item(arm, f"CASE-{case:03d}", repeat)
        for case in range(1, cases + 1)
        for arm in ("A", "B", "C")
        for repeat in range(1, repeats + 1)
    ]


def _compute(items: list[dict], **kwargs) -> dict:
    return compute_evidence_sufficiency(
        items,
        balanced_case_minimum=kwargs.pop("balanced_case_minimum", 4),
        minimum_repeats=kwargs.pop("minimum_repeats", 2),
        required_arms=["A", "B", "C"],
        **kwargs,
    )


@pytest.mark.parametrize(
    ("cases", "repeats", "expected"),
    [(0, 0, "INSUFFICIENT"), (1, 1, "INSUFFICIENT"), (3, 2, "INSUFFICIENT")],
)
def test_balanced_case_threshold_short_circuits(cases, repeats, expected):
    assert _compute(_matrix(cases, repeats))["result"] == expected


@pytest.mark.parametrize("repeats", [0, 1])
def test_repeat_threshold_short_circuits(repeats):
    assert _compute(_matrix(4, repeats))["result"] == "INSUFFICIENT"


@pytest.mark.parametrize("cases", [4, 5])
def test_threshold_at_or_above_does_not_short_circuit(cases):
    result = _compute(_matrix(cases, 2))
    assert result["result"] == "SUFFICIENT"
    assert evaluate_short_circuit(result)["short_circuit"] is False


@pytest.mark.parametrize(
    ("classification", "status", "counter"),
    [
        ("RECOVERY_AFFECTED", "COMPLETED", "recovery_excluded_count"),
        ("FAILED", "FAILED", "failed_excluded_count"),
        ("SUPERSEDED", "COMPLETED", "superseded_excluded_count"),
        ("NOT_RUN", "NOT_RUN", "not_run_excluded_count"),
    ],
)
def test_ineligible_classes_never_create_balanced_case(classification, status, counter):
    items = _matrix(3, 2)
    items.extend(
        _item(
            arm,
            "CASE-004",
            1,
            eligible=False,
            classification=classification,
            status=status,
        )
        for arm in ("A", "B", "C")
    )
    result = _compute(items)
    assert result["actual"]["balanced_case_count"] == 3
    assert result["actual"][counter] == 3


def test_not_run_is_not_a_zero_score():
    item = _item("A", "CASE-001", 1, eligible=False, classification="NOT_RUN", status="NOT_RUN")
    item["score"] = 0
    result = _compute([item])
    assert result["actual"]["eligible_primary_count"] == 0


def test_coverage_cannot_replace_missing_correctness_cells():
    items = _matrix(4, 2)
    for item in items:
        if item["anonymous_arm_id"] == "C" and item["case_id"] == "CASE-004":
            item["ranking_eligible"] = False
            item["coverage"] = 1.0
    assert _compute(items)["result"] == "INSUFFICIENT"


def test_aggregate_score_cannot_override_insufficiency():
    items = _matrix(2, 1)
    for item in items:
        item["aggregate_score"] = 1_000_000
    assert _compute(items)["result"] == "INSUFFICIENT"


def test_subagent_votes_cannot_override_insufficiency():
    result = _compute(_matrix(2, 1))
    result["subagent_support_votes"] = 5
    assert evaluate_short_circuit(result)["decision"] == "EVIDENCE_INSUFFICIENT"


def test_input_order_does_not_change_record_semantics():
    left = _compute(_matrix(4, 2))
    right = _compute(list(reversed(_matrix(4, 2))))
    for result in (left, right):
        result.pop("evidence_items_hash")
        result.pop("record_hash")
    assert left == right


def test_candidate_label_round_trip_does_not_change_sufficiency():
    original = _compute(_matrix(4, 2))
    swapped = deepcopy(_matrix(4, 2))
    for item in swapped:
        item["anonymous_arm_id"] = {"A": "B", "B": "A"}.get(
            item["anonymous_arm_id"], item["anonymous_arm_id"]
        )
    assert _compute(swapped)["actual"] == original["actual"]


def test_fixture_change_changes_decision():
    items = _matrix(4, 2)
    assert _compute(items)["result"] == "SUFFICIENT"
    items[-1]["ranking_eligible"] = False
    assert _compute(items)["result"] == "INSUFFICIENT"


def test_threshold_change_changes_decision():
    items = _matrix(4, 2)
    assert _compute(items, balanced_case_minimum=4)["result"] == "SUFFICIENT"
    assert _compute(items, balanced_case_minimum=5)["result"] == "INSUFFICIENT"


def test_freeze_mutation_state_yields_stale():
    result = _compute(_matrix(4, 2), frozen_evidence_valid=False)
    assert result["result"] == "STALE"
    assert evaluate_short_circuit(result)["decision"] == "STALE"


def test_task_hash_mismatch_blocks_comparison():
    items = _matrix(4, 2)
    items[-1]["task_input_hash"] = "mismatch"
    result = _compute(items)
    assert result["task_hash_consistency"]["passed"] is False
    assert result["result"] == "INSUFFICIENT"


def test_missing_task_hash_blocks_comparison():
    items = _matrix(4, 2)
    items[-1]["task_input_hash"] = None
    result = _compute(items)
    assert result["task_hash_consistency"]["passed"] is False
    assert "CASE-004" in result["task_hash_consistency"]["mismatched_cases"]


def test_duplicate_evidence_identity_is_rejected():
    items = _matrix(4, 2)
    items.append(deepcopy(items[-1]))
    with pytest.raises(ValueError, match="DUPLICATE_EVIDENCE_ID"):
        _compute(items)


def test_mandatory_hard_gate_failure_rejects_before_judges():
    result = _compute(_matrix(4, 2), mandatory_hard_gates_passed=False)
    action = evaluate_short_circuit(result)
    assert action["decision"] == "AUTOMATED_REJECTED"
    assert action["semantic_judges_status"] == "SKIPPED"


@pytest.mark.parametrize(
    "gate",
    [
        "license",
        "answer_contamination",
        "security",
        "second_state_source",
        "second_orchestrator",
        "scope_conflict",
    ],
)
def test_each_inherited_hard_gate_is_explicit_and_fail_closed(gate):
    kwargs = {
        "no_direct_adoption": True,
        "normalized_contamination_safe": True,
        "no_third_party_execution": True,
        "evaluation_scope_only": True,
    }
    controlling_input = {
        "license": "no_direct_adoption",
        "answer_contamination": "normalized_contamination_safe",
        "security": "no_third_party_execution",
        "second_state_source": "no_direct_adoption",
        "second_orchestrator": "no_direct_adoption",
        "scope_conflict": "evaluation_scope_only",
    }[gate]
    kwargs[controlling_input] = False
    result = evaluate_comparative_hard_gates(**kwargs)
    assert set(result) == {
        "license",
        "answer_contamination",
        "security",
        "second_state_source",
        "second_orchestrator",
        "scope_conflict",
    }
    assert result[gate] is False


@pytest.mark.parametrize(
    "arms",
    [
        [],
        [{"candidate_id": None}],
        [
            {
                "candidate_id": "candidate-h",
                "direct_adoption_eligible": False,
                "contamination_status": "PASS_AFTER_NORMALIZATION",
            }
        ],
    ],
)
def test_comparative_hard_gates_require_complete_candidate_coverage(monkeypatch, arms, repo_root):
    import cumcm_skill_lab.adjudication.pre_adjudication as pre

    review = {
        "arms": arms,
        "third_party_code_executed": False,
        "candidate_dependencies_installed": False,
        "review_status": "COMPLETE_FOR_EVALUATION_ONLY",
    }
    monkeypatch.setattr(pre, "read_json", lambda _path: review)
    monkeypatch.setattr(
        pre,
        "resolve_config",
        lambda _root: {
            "direct_adoption_targets": {"HANDSOMEZR": "candidate-h", "YUSHUI": "candidate-y"}
        },
    )
    gates = build_comparative_hard_gates(repo_root)
    assert gates
    assert all(item["passed"] is False for item in gates)


@pytest.mark.parametrize(
    ("items", "expected"),
    [([], True), ([{"ranking_eligible": False}], True), ([{"ranking_eligible": True}], False)],
)
def test_recovery_exclusion_has_vacuous_safe_semantics(items, expected):
    assert recovery_exclusion_passed(items) is expected


def test_freeze_verification_rejects_added_evidence_file(repo_root, monkeypatch):
    import cumcm_skill_lab.adjudication.pre_adjudication as pre

    manifest = json.loads(
        (repo_root / "evals/results/phase-002c/input_freeze_manifest.json").read_text()
    )
    current = sorted(manifest["tracked_evidence_files"])
    monkeypatch.setattr(pre, "_evidence_files_on_disk", lambda _root: [*current, "extra.json"])
    assert "PHASE002C_EVIDENCE_INVENTORY_MISMATCH" in verify_input_freeze(repo_root, manifest)


@pytest.mark.parametrize(
    ("field", "error"),
    [
        ("policy_file_hash", "PHASE002C_POLICY_FILE_HASH_MISMATCH"),
        ("config_file_hash", "PHASE002C_CONFIG_FILE_HASH_MISMATCH"),
    ],
)
def test_raw_policy_and_config_hashes_are_verified(repo_root, field, error):
    manifest = json.loads(
        (repo_root / "evals/results/phase-002c/input_freeze_manifest.json").read_text()
    )
    manifest[field] = "f" * 64
    body = dict(manifest)
    body.pop("freeze_hash")
    manifest["freeze_hash"] = sha256_json(body)
    assert error in verify_input_freeze(repo_root, manifest)


def test_rules_contracts_and_agent_configs_are_frozen(repo_root):
    manifest = json.loads(
        (repo_root / "evals/results/phase-002c/input_freeze_manifest.json").read_text()
    )
    assert "contracts/subagent_audit.schema.json" in manifest["rule_contract_hashes"]
    assert "rules/pre_adjudication_rules.yaml" in manifest["rule_contract_hashes"]
    assert len(manifest["agent_config_hashes"]) == 5


def test_invalid_freeze_returns_formal_stale_signal(repo_root, monkeypatch):
    import cumcm_skill_lab.adjudication.pre_adjudication as pre

    monkeypatch.setattr(pre, "verify_input_freeze", lambda _root: ["MUTATED"])
    result = write_pre_adjudication(repo_root, check=True)
    assert result["status"] == "INPUT_FREEZE_BROKEN"
    assert result["decision"] == "STALE"
    assert result["semantic_judges_status"] == "BLOCKED"
    assert result["next_phase_candidate"] is None


def test_current_pre_record_names_every_inherited_hard_gate(repo_root):
    record = json.loads(
        (
            repo_root / "evals/results/phase-002c/pre_adjudication/pre_adjudication_record.json"
        ).read_text()
    )
    names = {item["gate"] for item in record["hard_gates"]}
    assert {
        "license",
        "answer_contamination",
        "security",
        "second_state_source",
        "second_orchestrator",
        "scope_conflict",
    }.issubset(names)


def test_report_runtime_claims_follow_machine_inputs():
    data = {
        "route": {"phase002d_started": False},
        "pre": {
            "decision": "EVIDENCE_INSUFFICIENT",
            "short_circuit": True,
            "semantic_judges_status": "SKIPPED",
        },
        "state": {
            "selected_architecture": None,
            "third_party_integrated": False,
            "skill_capability_status": "SCAFFOLD_ONLY",
        },
        "transport": {
            "status": "AUTOMATED_ADJUDICATION_INCOMPLETE",
            "diagnostics": {"one": "hash", "two": "hash"},
            "terminal_failure_class": "RESPONSES_CONNECT_RESET",
        },
        "audits": [{"nested_codex_used": False, "api_key_used": False, "writes_observed": False}],
    }
    before = runtime_facts(data)
    data["route"]["phase002d_started"] = True
    data["pre"]["short_circuit"] = False
    data["state"]["third_party_integrated"] = True
    data["transport"]["status"] = "RECOVERED"
    data["audits"][0]["nested_codex_used"] = True
    after = runtime_facts(data)
    assert before != after
    assert before["phase002d_report_status"] == "Draft; Not Executed"
    assert "through an evidence-sufficiency short circuit" in before["phase002c_outcome_summary"]
    assert after["phase002d_started"] is True
    assert after["phase002d_report_status"] == "Execution Recorded"
    assert "without an evidence-sufficiency short circuit" in after["phase002c_outcome_summary"]
    assert after["third_party_integrated"] is True
    assert after["transport_repaired"] is True
    assert after["nested_codex_used"] is True


def test_reports_derive_phase002d_execution_and_short_circuit_from_machine_inputs():
    data = {
        "sufficiency": {
            "required_arms": ["ARM-A", "ARM-B", "ARM-C"],
            "thresholds": {"balanced_case_minimum": 1, "minimum_repeats": 1},
            "actual": {
                "cell_repeat_counts": {"CASE-001": {"ARM-A": 1, "ARM-B": 1, "ARM-C": 1}},
                "balanced_cases": ["CASE-001"],
            },
        },
        "route": {"phase002d_started": False},
        "pre": {
            "decision": "EVIDENCE_INSUFFICIENT",
            "short_circuit": True,
            "semantic_judges_status": "SKIPPED",
        },
        "state": {
            "selected_architecture": None,
            "third_party_integrated": False,
            "skill_capability_status": "SCAFFOLD_ONLY",
        },
        "transport": {
            "status": "AUTOMATED_ADJUDICATION_INCOMPLETE",
            "diagnostics": {},
            "terminal_failure_class": "RESPONSES_CONNECT_RESET",
        },
        "audits": [
            {
                "role": "dissent_and_cost_auditor",
                "nested_codex_used": False,
                "api_key_used": False,
                "writes_observed": False,
                "cost_assessment": {"token_cost": "TOKEN-FACT", "time_cost": "TIME-FACT"},
            }
        ],
    }
    before = _render_expansion(data)
    data["route"]["phase002d_started"] = True
    data["pre"]["short_circuit"] = False
    after = _render_expansion(data)
    assert "(Draft; Not Executed)" in before
    assert "(Execution Recorded)" in after
    assert "TOKEN-FACT" in after
    assert "TIME-FACT" in after
    assert runtime_facts(data)["phase002c_outcome_summary"] not in before


@pytest.mark.parametrize(
    ("decision", "audit", "expected", "phase003"),
    [
        ("EVIDENCE_INSUFFICIENT", "PASS", "PHASE-EVIDENCE-EXPANSION-002D", False),
        ("AUTOMATED_REJECTED", "PASS", "PHASE-EVIDENCE-EXPANSION-002D", False),
        ("EVIDENCE_INSUFFICIENT", "FAIL", None, False),
        ("RETEST_REQUIRED", "PASS", None, False),
        ("AUTOMATED_ACCEPTED", "PASS", None, False),
    ],
)
def test_phase_routes(decision, audit, expected, phase003):
    record = {"decision_id": "D", "decision": decision}
    route = build_phase_route(record, audit_result=audit)
    assert route["next_phase_allowed"] == expected
    assert route["phase003_allowed"] is phase003
    assert route["phase002d_started"] is False


def test_phase003_requires_explicit_prerequisites():
    route = build_phase_route(
        {"decision_id": "D", "decision": "AUTOMATED_ACCEPTED"},
        audit_result="PASS",
        phase003_prerequisites_met=True,
    )
    assert route["next_phase_allowed"] == "PHASE-SKILL-INTEGRATION-003"


def _safe_candidate() -> tuple[dict, dict]:
    return (
        {
            "answer_leakage_risk": "LOW",
            "integration_conflict_risk": "LOW",
            "state_management": "NONE",
            "skill_names": ["single-skill"],
            "dangerous_or_privileged_instructions": [],
            "network_dependencies": [],
        },
        {"license_status": "MIT"},
    )


def _gates(candidate: dict, arm: dict, **kwargs) -> dict[str, bool]:
    return evaluate_direct_adoption_gates(
        candidate,
        arm,
        review_status=kwargs.pop("review_status", "FULL_RUNTIME_VERIFIED"),
        third_party_code_executed=kwargs.pop("third_party_code_executed", True),
        candidate_dependencies_installed=kwargs.pop("candidate_dependencies_installed", True),
    )


@pytest.mark.parametrize(
    "license_status", ["", "UNKNOWN_NO_LICENSE", "MIT_WITH_EXCLUSIONS", "UNRECOGNIZED"]
)
def test_license_hard_gate_rejects_unknown_or_excluded(license_status):
    candidate, arm = _safe_candidate()
    arm["license_status"] = license_status
    assert _gates(candidate, arm)["license"] is False


@pytest.mark.parametrize("risk", ["HIGH: paper-derived", "BLOCKER: answer demo"])
def test_answer_contamination_hard_gate(risk):
    candidate, arm = _safe_candidate()
    candidate["answer_leakage_risk"] = risk
    assert _gates(candidate, arm)["answer_contamination"] is False


def test_second_state_source_hard_gate():
    candidate, arm = _safe_candidate()
    candidate["state_management"] = "parallel decision log"
    assert _gates(candidate, arm)["second_state_source"] is False


@pytest.mark.parametrize("mode", ["risk", "skills"])
def test_second_orchestrator_hard_gate(mode):
    candidate, arm = _safe_candidate()
    if mode == "risk":
        candidate["integration_conflict_risk"] = "HIGH orchestrator conflict"
    else:
        candidate["skill_names"] = ["orchestrator", "worker"]
    assert _gates(candidate, arm)["second_orchestrator"] is False


def test_scope_hard_gate_blocks_eval_only_package():
    candidate, arm = _safe_candidate()
    assert (
        _gates(candidate, arm, review_status="COMPLETE_FOR_EVALUATION_ONLY")["scope_conflict"]
        is False
    )


@pytest.mark.parametrize("field", ["dangerous_or_privileged_instructions", "network_dependencies"])
def test_security_hard_gate(field):
    candidate, arm = _safe_candidate()
    candidate[field] = ["unsafe"]
    assert _gates(candidate, arm)["security"] is False


@pytest.mark.parametrize(("executed", "installed"), [(False, False), (True, False), (False, True)])
def test_full_runtime_gate_requires_execution_and_dependencies(executed, installed):
    candidate, arm = _safe_candidate()
    assert (
        _gates(
            candidate,
            arm,
            third_party_code_executed=executed,
            candidate_dependencies_installed=installed,
        )["full_runtime_verification"]
        is False
    )


def test_direct_adoption_known_safe_evidence_passes_all_gates():
    candidate, arm = _safe_candidate()
    assert all(_gates(candidate, arm).values())


@pytest.mark.parametrize(
    ("field", "gate"),
    [
        ("answer_leakage_risk", "answer_contamination"),
        ("integration_conflict_risk", "second_orchestrator"),
        ("state_management", "second_state_source"),
        ("skill_names", "second_orchestrator"),
        ("dangerous_or_privileged_instructions", "security"),
        ("network_dependencies", "security"),
    ],
)
def test_direct_adoption_missing_evidence_fails_closed(field, gate):
    candidate, arm = _safe_candidate()
    candidate.pop(field)
    assert _gates(candidate, arm)[gate] is False


@pytest.mark.parametrize(
    ("field", "value", "gate"),
    [
        ("answer_leakage_risk", "UNKNOWN", "answer_contamination"),
        ("integration_conflict_risk", "UNKNOWN", "second_orchestrator"),
        ("state_management", "UNKNOWN", "second_state_source"),
    ],
)
def test_direct_adoption_unknown_evidence_fails_closed(field, value, gate):
    candidate, arm = _safe_candidate()
    candidate[field] = value
    assert _gates(candidate, arm)[gate] is False


@pytest.mark.parametrize("review_status", ["", "UNKNOWN", "COMPLETE_FOR_EVALUATION_ONLY"])
def test_direct_adoption_unverified_scope_fails_closed(review_status):
    candidate, arm = _safe_candidate()
    assert _gates(candidate, arm, review_status=review_status)["scope_conflict"] is False


def test_decision_timestamp_comes_from_frozen_policy(repo_root):
    assert decision_created_at(repo_root) == "2026-09-01T11:57:13+08:00"


def test_final_replay_compares_decision_sets_independent_of_file_order():
    decisions = [
        {"decision_id": "DECISION-A", "decision": "EVIDENCE_INSUFFICIENT"},
        {"decision_id": "DECISION-B", "decision": "AUTOMATED_REJECTED"},
    ]
    assert decision_sets_equal(decisions, list(reversed(decisions)))


def test_final_replay_rejects_duplicate_decision_ids():
    decision = {"decision_id": "DECISION-A", "decision": "EVIDENCE_INSUFFICIENT"}
    assert decision_sets_equal([decision], [decision, dict(decision)]) is False


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ([], []),
        ([{"decision_id": "DECISION-A", "decision": "X"}], []),
        (
            [{"decision_id": "DECISION-A", "decision": "X"}],
            [{"decision_id": "DECISION-A", "decision": "Y"}],
        ),
        ([{"decision_id": "", "decision": "X"}], [{"decision_id": "", "decision": "X"}]),
        ([{"decision_id": 1, "decision": "X"}], [{"decision_id": 1, "decision": "X"}]),
    ],
)
def test_final_replay_rejects_incomplete_or_invalid_decision_sets(left, right):
    assert decision_sets_equal(left, right) is False


def test_first_round_bundles_expose_hash_bound_replay_implementation(repo_root):
    bundles = build_first_round_bundles(repo_root)
    for bundle in bundles.values():
        assert (
            "src/cumcm_skill_lab/adjudication/phase002c_replay.py"
            in bundle["allowed_file_references"]
        )


def test_component_value_is_not_an_input_to_whole_package_gates():
    candidate, arm = _safe_candidate()
    baseline = _gates(candidate, arm)
    candidate["valuable_components"] = ["claim gate", "hash manifest"]
    assert _gates(candidate, arm) == baseline


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("human_gate", True),
        ("human_approved", True),
        ("human_selected", "A"),
        ("majority_vote_result", "PASS"),
    ],
)
def test_automated_decision_contract_rejects_human_or_vote_fields(repo_root, field, value):
    schema = json.loads((repo_root / "contracts/automated_decision.schema.json").read_text())
    record = json.loads(
        (repo_root / "tests/fixtures/contracts/valid/automated_decision.json").read_text()
    )
    record[field] = value
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(record)


@pytest.mark.parametrize("scope", ["DIRECT_REUSE", "IMPLEMENTATION_READY", "PRODUCTION_READY"])
def test_component_scope_cannot_exceed_specification(repo_root, scope):
    schema = json.loads((repo_root / "contracts/automated_decision.schema.json").read_text())
    record = json.loads(
        (repo_root / "tests/fixtures/contracts/valid/automated_decision.json").read_text()
    )
    record["decision_type"] = "COMPONENT_READINESS"
    record["component_results"] = [
        {
            "mechanism_id": "m",
            "decision": "AUTOMATED_ACCEPTED",
            "accepted_scope": scope,
            "reason_codes": ["x"],
            "evidence_refs": ["e"],
            "required_tests": ["t"],
            "maintenance_cost": "LOW",
        }
    ]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(record)


def test_subagent_contract_rejects_write_behavior(repo_root):
    schema = json.loads((repo_root / "contracts/subagent_audit.schema.json").read_text())
    record = json.loads(
        (repo_root / "tests/fixtures/contracts/valid/subagent_audit.json").read_text()
    )
    record["writes_observed"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(record)


@pytest.mark.parametrize("field", ["nested_codex_used", "api_key_used"])
def test_subagent_contract_rejects_forbidden_runtime_use(repo_root, field):
    schema = json.loads((repo_root / "contracts/subagent_audit.schema.json").read_text())
    record = json.loads(
        (repo_root / "tests/fixtures/contracts/valid/subagent_audit.json").read_text()
    )
    record[field] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(record)


def test_subagent_output_without_schema_fields_is_invalid(repo_root):
    schema = json.loads((repo_root / "contracts/subagent_audit.schema.json").read_text())
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate({"verdict": "PASS"})


@pytest.mark.parametrize(
    ("finding_status", "expected"),
    [("OPEN", "PENDING"), ("UNRESOLVED", "PENDING"), ("RESOLVED", "PASS")],
)
def test_dissent_blocker_becomes_executable_test(finding_status, expected):
    finding = {
        "finding_id": "F-BLOCKER",
        "severity": "BLOCKER",
        "testability": "TESTABLE",
        "required_test": (
            "tests/unit/test_phase002c_evidence_gate.py::test_missing_task_hash_blocks_comparison"
        ),
        "pass_condition": "missing hash is rejected",
        "status": finding_status,
        "evidence_refs": ["EVIDENCE-SUFFICIENCY-PHASE-002C"],
    }
    record = blocker_test_record("AUDIT-X", finding)
    assert record["status"] == expected
    assert (record["result_hash"] is not None) is (expected == "PASS")


def test_non_testable_claim_cannot_become_a_failing_test():
    finding = {
        "finding_id": "F-CLAIM",
        "severity": "BLOCKER",
        "testability": "NON_TESTABLE_CLAIM",
        "required_test": None,
        "pass_condition": None,
        "status": "UNRESOLVED",
        "evidence_refs": ["EVIDENCE-SUFFICIENCY-PHASE-002C"],
    }
    assert blocker_test_record("AUDIT-X", finding)["status"] == "NON_TESTABLE_CLAIM"


@pytest.mark.parametrize(
    "role",
    [
        "evidence_sufficiency_auditor",
        "adjudication_policy_prosecutor",
        "dissent_and_cost_auditor",
        "reproducibility_auditor",
        "automated_decision_auditor",
    ],
)
def test_project_agent_is_read_only_and_inherits_model(repo_root, role):
    text = (repo_root / f".codex/agents/{role}.toml").read_text()
    assert 'sandbox_mode = "read-only"' in text
    assert "model =" not in text
    assert "reasoning_effort =" not in text
    assert "nested Codex" in text
    assert "API key" in text


@pytest.mark.parametrize(
    "script",
    [
        "run_pre_adjudication.py",
        "run_phase002c_decision.py",
        "audit_phase002c_decision.py",
        "replay_phase002c_decision.py",
        "summarize_phase002c.py",
    ],
)
def test_phase002c_scripts_expose_help(repo_root, script):
    result = subprocess.run(
        [str(repo_root / ".venv/bin/python"), str(repo_root / "scripts" / script), "--help"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--check" in result.stdout


def test_policy_and_config_do_not_hardcode_current_actuals(repo_root):
    text = (repo_root / "adjudication/configs/phase-002c.yaml").read_text()
    text += (repo_root / "adjudication/policies/phase-002c.yaml").read_text()
    assert "actual_balanced" not in text
    assert "actual_repeats" not in text
    assert "current_candidate_decision" not in text


def test_report_projection_changes_with_decision_record():
    decision = {
        "decision_id": "D",
        "decision_type": "EVIDENCE_SUFFICIENCY",
        "decision": "EVIDENCE_INSUFFICIENT",
        "accepted_scope": "NONE",
        "decision_audit": "A",
        "next_phase_allowed": "PHASE-EVIDENCE-EXPANSION-002D",
    }
    before = decision_rows_as_markdown([decision])
    decision["decision"] = "RETEST_REQUIRED"
    after = decision_rows_as_markdown([decision])
    assert before != after


def test_historical_transport_failure_records_remain(repo_root):
    phase_a = sorted((repo_root / "evals/results/phase-002a/runtime").glob("blind_failure_*.json"))
    phase_b = sorted(
        (repo_root / "evals/results/phase-002b/transport_diagnostics").glob(
            "correctness_attempt_*.json"
        )
    )
    assert len(phase_a) == 3
    assert len(phase_b) == 2
