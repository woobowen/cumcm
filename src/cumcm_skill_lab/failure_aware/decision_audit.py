"""Mechanical decision audit after the independent Phase 002D-R1 auditor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .decisions import DECISION_FILES, validate_decisions
from .evidence_freeze import verify_input_freeze
from .models import RESULT_ROOT, check_or_write, file_sha256, read_json, sha256_json
from .native_audits import (
    BUNDLE_ROOT,
    POST_DECISION_ROLE,
    audit_path,
    validate_audit,
)
from .replay import build_replay

AUDIT_PATH = RESULT_ROOT / "decision_audit/audit.json"
CREATED_AT = "2026-09-01T23:12:32+08:00"


def _decision_map(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {envelope["automated_decision"]["decision_id"]: envelope for envelope in decisions}


def build_decision_audit(root: Path) -> dict[str, Any]:
    native_path = audit_path(root, POST_DECISION_ROLE)
    if not native_path.is_file():
        raise ValueError("FAILURE_AWARE_DECISION_AUDITOR_OUTPUT_MISSING")
    native = read_json(native_path)
    native_errors = validate_audit(root, native, role=POST_DECISION_ROLE)
    bundle = read_json(root / BUNDLE_ROOT / f"{POST_DECISION_ROLE}.json")
    decisions = [
        read_json(root / RESULT_ROOT / "automated_decisions" / filename)
        for filename in DECISION_FILES.values()
    ]
    decision_errors = validate_decisions(root, decisions)
    by_id = _decision_map(decisions)
    classifications = read_json(root / RESULT_ROOT / "failure_attribution_summary.json")
    matrix = read_json(root / RESULT_ROOT / "slot_outcomes/slot_outcome_matrix.json")
    scopes = read_json(root / RESULT_ROOT / "evidence_scopes/evidence_scope_summary.json")
    quality = read_json(root / RESULT_ROOT / "evidence_scopes/quality_sufficiency.json")
    reliability = read_json(root / RESULT_ROOT / "evidence_scopes/reliability_sufficiency.json")
    retry = read_json(root / RESULT_ROOT / "retry_bias/retry_bias_audit.json")
    authorization = read_json(root / RESULT_ROOT / "supplemental/authorization.json")
    supplemental_status = read_json(root / RESULT_ROOT / "supplemental/status.json")
    replay = build_replay(root)

    quality_decision = by_id["DECISION-QUALITY-EVIDENCE-SUFFICIENCY-002D-R1"]
    reliability_decision = by_id["DECISION-RELIABILITY-EVIDENCE-SUFFICIENCY-002D-R1"]
    architecture = by_id["DECISION-ARCHITECTURE-002D-R1"]
    components = by_id["DECISION-COMPONENT-READINESS-002D-R1"]
    supplemental = by_id["DECISION-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1"]

    checks = {
        "native_auditor_schema_valid": not native_errors,
        "native_auditor_pass": native["verdict"] == "PASS",
        "native_auditor_read_only": native["read_only"] and not native["writes_observed"],
        "native_auditor_no_nested_codex": not native["nested_codex_used"],
        "native_auditor_no_api_key": not native["api_key_used"],
        "input_freeze_valid": not verify_input_freeze(root),
        "decision_set_complete": set(by_id) == set(DECISION_FILES),
        "decision_hashes_and_contracts_valid": not decision_errors,
        "failure_attribution_exact": classifications["classification_counts"]
        == {
            "ELIGIBLE_SUCCESS": 9,
            "HARNESS_CENSORED": 2,
            "INFRASTRUCTURE_CENSORED": 1,
            "SUPERSEDED": 0,
            "TERMINAL_MODEL_SCHEMA_FAILURE": 0,
            "TERMINAL_POLICY_FAILURE": 7,
            "TERMINAL_UNSUPPORTED_CLAIM_FAILURE": 0,
            "UNKNOWN_CENSORED": 0,
            "VALID_OUTPUT_ORACLE_FAIL": 9,
        },
        "slot_resolution_exact": matrix["resolution_counts"]
        == {
            "CENSORED_HARNESS": 1,
            "CENSORED_INFRASTRUCTURE": 0,
            "RESOLVED_ELIGIBLE_SUCCESS": 9,
            "RESOLVED_TERMINAL_NEGATIVE": 14,
            "STALE": 0,
            "UNRESOLVED_UNKNOWN": 0,
        },
        "retry_bias_controls_hold": retry["earliest_eligible_enforced"]
        and retry["best_of_n_prohibited"]
        and not retry["failure_zero_imputation"],
        "all_attempts_and_costs_retained": retry["all_attempts_in_cost"]
        and retry["attempt_count"] == 28
        and retry["retry_burden"] == 4
        and retry["cost_reconciliation"]["exact_match"],
        "original_budget_not_mutated": not authorization["original_budget_mutated"],
        "recovery_not_ranked": all(not item["recovery_ranked"] for item in decisions),
        "identity_not_used": all(not item["identity_used"] for item in decisions),
        "no_majority_vote": all(not item["majority_vote_used"] for item in decisions),
        "no_human_technical_gate": all(not item["human_technical_gate_used"] for item in decisions),
        "quality_insufficient_and_unaccepted": quality["result"] == "EVIDENCE_INSUFFICIENT"
        and quality_decision["automated_decision"]["decision"] == "EVIDENCE_INSUFFICIENT"
        and quality_decision["accepted_scope"] == "NONE",
        "reliability_accepted_only": reliability["result"] == "SUFFICIENT_RELIABILITY_ONLY"
        and reliability_decision["automated_decision"]["decision"] == "AUTOMATED_ACCEPTED"
        and reliability_decision["accepted_scope"] == "RELIABILITY_ONLY",
        "quality_reliability_not_conflated": all(
            not item["quality_reliability_conflated"] for item in decisions
        ),
        "posthoc_positive_claim_prohibited": all(
            item["posthoc_observation_policy"]
            and not item["positive_performance_superiority_claim_allowed"]
            for item in decisions
        ),
        "supplemental_scope_zero": authorization["authorized_slot_ids"] == []
        and authorization["maximum_real_starts"] == 0
        and supplemental_status["model_start_count"] == 0
        and supplemental["automated_decision"]["decision"] == "AUTOMATED_REJECTED",
        "architecture_not_selected": architecture["automated_decision"]["decision"]
        == "EVIDENCE_INSUFFICIENT"
        and architecture["accepted_scope"] == "NONE",
        "component_scope_specification_only": components["accepted_scope"] == "SPECIFICATION_ONLY"
        and all(
            item["accepted_scope"] == "SPECIFICATION_ONLY"
            for item in components["automated_decision"]["component_results"]
        ),
        "terminal_negative_does_not_fill_quality": scopes["quality_evidence"]["result"]
        == "EVIDENCE_INSUFFICIENT"
        and scopes["outcome_completeness"]["resolved_terminal_negative_slots"] == 14,
        "next_phase_route_is_phase002d": all(
            item["automated_decision"]["next_phase_allowed"] == "PHASE-EVIDENCE-EXPANSION-002D"
            for item in decisions
        ),
        "offline_replay_stable": replay["stable"] and replay["variant_count"] == 5,
    }
    failures = sorted(name for name, passed in checks.items() if not passed)
    blockers = sorted(set(native["blockers"]) | set(native_errors) | set(decision_errors))
    if not replay["stable"]:
        blockers.append("OFFLINE_REPLAY_UNSTABLE")
    result = (
        "PASS"
        if not failures and not blockers
        else ("RETEST_REQUIRED" if native["verdict"] == "RETEST_REQUIRED" else "FAIL")
    )
    freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    audit = {
        "audit_id": "DECISION-AUDIT-PHASE-002D-R1",
        "role": "DECISION_AUDITOR",
        "bundle_id": bundle["bundle_id"],
        "bundle_hash": bundle["bundle_hash"],
        "input_bundle_hash": native["bundle_hash"],
        "policy_hash": file_sha256(root / "rules/phase002d_r1_workflow_rules.yaml"),
        "evidence_hash": freeze["manifest_hash"],
        "model": native["model"],
        "reasoning_setting": native["reasoning_setting"],
        "decision_ids": sorted(by_id),
        "independent": True,
        "majority_vote_used": False,
        "human_technical_gate_used": False,
        "recovery_ranked": False,
        "checks": checks,
        "result": result,
        "failures": failures,
        "blockers": sorted(set(blockers)),
        "replayable": not failures and not blockers,
        "audit_evidence_refs": [
            native["audit_id"],
            replay["replay_id"],
            freeze["freeze_id"],
        ],
        "confidence": 1.0 if result == "PASS" else 0.0,
        "checkpoint_hash": "0" * 64,
        "created_at": CREATED_AT,
    }
    audit["checkpoint_hash"] = sha256_json(
        {key: value for key, value in audit.items() if key != "checkpoint_hash"}
    )
    Draft202012Validator(read_json(root / "contracts/decision_audit.schema.json")).validate(audit)
    return audit


def check_or_write_decision_audit(root: Path, *, check: bool) -> dict[str, Any]:
    audit = build_decision_audit(root)
    errors = check_or_write(root / AUDIT_PATH, audit, check=check)
    return {
        "status": "PASS" if not errors and audit["result"] == "PASS" else "FAIL",
        "audit_result": audit["result"],
        "replayable": audit["replayable"],
        "checkpoint_hash": audit["checkpoint_hash"],
        "errors": errors,
    }
