"""Generate the seven Phase 002D-R1 failure-aware automated decisions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .evidence_freeze import verify_input_freeze
from .evidence_scopes import build_evidence_scope_summary
from .models import RESULT_ROOT, check_or_write, hashed_body, read_json, sha256_json
from .native_audits import FIRST_ROUND_ROLES, validate_first_round
from .retry_bias import build_retry_bias_audit
from .slot_matrix import build_slot_matrix
from .supplemental import build_authorization

DECISION_ROOT = RESULT_ROOT / "automated_decisions"
QUALITY_PATH = RESULT_ROOT / "evidence_scopes/quality_sufficiency.json"
RELIABILITY_PATH = RESULT_ROOT / "evidence_scopes/reliability_sufficiency.json"
CREATED_AT = "2026-09-01T23:12:32+08:00"
DECISION_FILES = {
    "DECISION-FAILURE-SEMANTICS-002D-R1": "failure_semantics.json",
    "DECISION-SLOT-RESOLUTION-002D-R1": "slot_resolution.json",
    "DECISION-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1": "supplemental_authorization.json",
    "DECISION-QUALITY-EVIDENCE-SUFFICIENCY-002D-R1": "quality_evidence_sufficiency.json",
    "DECISION-RELIABILITY-EVIDENCE-SUFFICIENCY-002D-R1": ("reliability_evidence_sufficiency.json"),
    "DECISION-ARCHITECTURE-002D-R1": "architecture.json",
    "DECISION-COMPONENT-READINESS-002D-R1": "component_readiness.json",
}
ARCHITECTURE_CANDIDATES = (
    "NATIVE_SINGLE_SKILL_CLEAN_ROOM",
    "RETAIN_SCAFFOLD_ONLY",
    "EVIDENCE_INSUFFICIENT",
    "AUTOMATED_ABSTAINED",
    "AUTOMATED_REJECTED",
)


def evaluate_architecture_gate(
    *, freeze_valid: bool, quality_sufficient: bool, posthoc_policy: bool
) -> dict[str, Any]:
    if not freeze_valid:
        return {
            "decision": "AUTOMATED_REJECTED",
            "reason": "INPUT_FREEZE_BROKEN",
            "rejected_candidates": list(ARCHITECTURE_CANDIDATES),
        }
    if not quality_sufficient:
        return {
            "decision": "EVIDENCE_INSUFFICIENT",
            "reason": "QUALITY_EVIDENCE_INSUFFICIENT",
            "rejected_candidates": ["NATIVE_SINGLE_SKILL_CLEAN_ROOM"],
        }
    if posthoc_policy:
        return {
            "decision": "AUTOMATED_ABSTAINED",
            "reason": "POSTHOC_POLICY_CANNOT_SELECT_ARCHITECTURE",
            "rejected_candidates": [],
        }
    return {
        "decision": "RETEST_REQUIRED",
        "reason": "INDEPENDENT_ARCHITECTURE_TEST_REQUIRED",
        "rejected_candidates": [],
    }


def apply_team_compliance_review(technical_decision: str, requested_override: str | None) -> str:
    if requested_override is not None and requested_override != technical_decision:
        raise ValueError("TEAM_COMPLIANCE_CANNOT_OVERRIDE_TECHNICAL_DECISION")
    return technical_decision


def build_sufficiency_records(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    scopes = build_evidence_scope_summary(root)
    retry = build_retry_bias_audit(root)
    quality_values = scopes["quality_evidence"]
    quality_body = {
        "schema_version": "1.0.0",
        "record_id": "PHASE-002D-R1-QUALITY-EVIDENCE-SUFFICIENCY-001",
        "scope": "QUALITY_EVIDENCE",
        "balanced_case_count": quality_values["balanced_case_count"],
        "required_balanced_cases": quality_values["required_balanced_cases"],
        "minimum_repeat_depth": quality_values["minimum_repeat_depth"],
        "required_repeat_depth": quality_values["required_repeat_depth"],
        "terminal_negative_fills_gate": False,
        "result": quality_values["result"],
        "reason_codes": [
            "BALANCED_CASE_MINIMUM_NOT_MET",
            "ELIGIBLE_QUALITY_REPEAT_DEPTH_NOT_MET",
        ],
    }
    reliability_values = scopes["reliability_evidence"]
    resolved_slots = scopes["outcome_completeness"]["resolved_slot_count"]
    checks = {
        "frozen_attempt_census_complete": reliability_values["attempt_count"] == 28,
        "all_attempts_in_cost": retry["all_attempts_in_cost"],
        "cost_totals_exact": retry["cost_reconciliation"]["exact_match"],
        "retry_burden_retained": retry["retry_burden"] == 4,
        "historical_protocol_deviations_explicit": bool(retry["historical_protocol_deviations"]),
        "resolved_slot_fraction_at_least_90_percent": resolved_slots / 24 >= 0.9,
        "failure_not_zero_imputed": not retry["failure_zero_imputation"],
    }
    reliability_body = {
        "schema_version": "1.0.0",
        "record_id": "PHASE-002D-R1-RELIABILITY-EVIDENCE-SUFFICIENCY-001",
        "scope": "RELIABILITY_EVIDENCE",
        "checks": checks,
        "metrics": reliability_values,
        "resolved_slot_count": resolved_slots,
        "expected_slot_count": 24,
        "result": "SUFFICIENT_RELIABILITY_ONLY"
        if all(checks.values())
        else "EVIDENCE_INSUFFICIENT",
        "quality_claim_allowed": False,
        "performance_superiority_claim_allowed": False,
        "reason_codes": [
            "FROZEN_PROTOCOL_ATTEMPT_CENSUS_COMPLETE",
            "OBSERVED_RELIABILITY_CAN_BE_REPORTED_DESCRIPTIVELY",
            "QUALITY_SCOPE_REMAINS_SEPARATE",
        ],
    }
    return (
        hashed_body(quality_body, "record_hash"),
        hashed_body(reliability_body, "record_hash"),
    )


def _audit_context(root: Path) -> tuple[list[str], list[str]]:
    findings = []
    for role in FIRST_ROUND_ROLES:
        audit = read_json(root / RESULT_ROOT / f"subagent_audits/{role}.json")
        findings.extend(item["finding_id"] for item in audit["findings"])
    tests = read_json(root / RESULT_ROOT / "adversarial_tests/test_evidence.json")
    return sorted(findings), sorted(item["test_id"] for item in tests["evidence"])


def _common(
    root: Path,
    *,
    decision_id: str,
    decision_type: str,
    target_ids: list[str],
    evidence_sufficiency: str,
) -> dict[str, Any]:
    freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    findings, tests = _audit_context(root)
    return {
        "decision_id": decision_id,
        "decision_type": decision_type,
        "target_ids": target_ids,
        "evidence_freeze_id": freeze["freeze_id"],
        "policy_version": "phase002d-r1/1.0.0",
        "hard_gate_status": "PASS",
        "evidence_sufficiency": evidence_sufficiency,
        "eligible_evidence": [],
        "excluded_evidence": [
            "RECOVERY_AFFECTED_EVIDENCE",
            "AGENT_VOTES",
            "HUMAN_TECHNICAL_GATE",
            "ARM_IDENTITY",
        ],
        "judge_decisions": [],
        "dissent_findings": findings,
        "tests": tests,
        "meta_adjudication": "DETERMINISTIC_FAILURE_AWARE_POLICY_ENGINE_NO_VOTE",
        "decision_audit": "PENDING:FAILURE_AWARE_DECISION_AUDITOR",
        "rejected_scope": [],
        "retest_requirements": [],
        "stale_dependencies": [],
        "confidence": 1.0,
        "next_phase_allowed": "PHASE-EVIDENCE-EXPANSION-002D",
        "created_at": CREATED_AT,
    }


def _wrap(core: dict[str, Any], *, evidence_scope: str, accepted_scope: str) -> dict[str, Any]:
    core["replay_hash"] = "0" * 64
    core["replay_hash"] = sha256_json(
        {key: value for key, value in core.items() if key != "replay_hash"}
    )
    body = {
        "schema_version": "1.0.0",
        "automated_decision_contract": "contracts/automated_decision.schema.json",
        "automated_decision": core,
        "evidence_scope": evidence_scope,
        "accepted_scope": accepted_scope,
        "posthoc_observation_policy": True,
        "positive_performance_superiority_claim_allowed": False,
        "quality_reliability_conflated": False,
        "terminal_negative_zero_imputed": False,
        "majority_vote_used": False,
        "human_technical_gate_used": False,
        "recovery_ranked": False,
        "identity_used": False,
    }
    return hashed_body(body, "failure_aware_hash")


def build_decisions(root: Path) -> list[dict[str, Any]]:
    if verify_input_freeze(root):
        raise ValueError("PHASE002D_R1_INPUT_FREEZE_BROKEN")
    if validate_first_round(root):
        raise ValueError("PHASE002D_R1_FIRST_ROUND_AUDITS_INVALID")
    closure = read_json(root / RESULT_ROOT / "adversarial_tests/finding_closure.json")
    if not closure["all_serious_findings_closed"]:
        raise ValueError("PHASE002D_R1_SERIOUS_FINDINGS_OPEN")

    scopes = build_evidence_scope_summary(root)
    _, matrix, _ = build_slot_matrix(root)
    retry = build_retry_bias_audit(root)
    supplemental = build_authorization(root)
    quality, reliability = build_sufficiency_records(root)
    policy = _common(
        root,
        decision_id="DECISION-FAILURE-SEMANTICS-002D-R1",
        decision_type="RECOVERY_POLICY",
        target_ids=["FAILURE_AWARE_EVIDENCE_USAGE"],
        evidence_sufficiency="SUFFICIENT",
    )
    policy.update(
        {
            "eligible_evidence": ["PHASE-002D-R1-FAILURE-ATTRIBUTION-001"],
            "decision": "AUTOMATED_ACCEPTED",
            "reason_codes": [
                "FAILURES_ARE_OBSERVED_CATEGORICAL_OUTCOMES",
                "CENSORED_OUTCOMES_EXCLUDED_FROM_COMPARATIVE_RANKING",
            ],
            "accepted_scope": "POLICY_ONLY",
            "rejected_scope": ["HISTORICAL_ATTEMPT_MUTATION", "FAILURE_AS_ZERO_SCORE"],
        }
    )
    slot = _common(
        root,
        decision_id="DECISION-SLOT-RESOLUTION-002D-R1",
        decision_type="RECOVERY_POLICY",
        target_ids=["PHASE-002D-24-SLOT-OUTCOME-MATRIX"],
        evidence_sufficiency="SUFFICIENT",
    )
    slot.update(
        {
            "eligible_evidence": [matrix["matrix_id"], retry["audit_id"]],
            "decision": "AUTOMATED_ACCEPTED",
            "reason_codes": [
                "23_OF_24_SLOTS_RESOLVED",
                "TERMINAL_PREDECESSOR_CANNOT_BE_ERASED",
                "EARLIEST_ELIGIBLE_SELECTION_ENFORCED",
            ],
            "accepted_scope": "POLICY_ONLY",
            "rejected_scope": ["BEST_OF_N", "RETRY_UNTIL_SUCCESS"],
        }
    )
    supplemental_core = _common(
        root,
        decision_id="DECISION-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1",
        decision_type="RECOVERY_POLICY",
        target_ids=["SUPPLEMENTAL_GENERIC_RUNS"],
        evidence_sufficiency="SUFFICIENT",
    )
    supplemental_core.update(
        {
            "eligible_evidence": [supplemental["decision_id"]],
            "decision": supplemental["decision"],
            "reason_codes": [
                "ZERO_AUTHORIZED_CENSORED_SLOTS",
                "HARNESS_SEMANTIC_EQUIVALENCE_NOT_ESTABLISHED",
            ],
            "accepted_scope": "NONE",
            "rejected_scope": ["SUPPLEMENTAL_GENERIC_RUNS", "TERMINAL_SLOT_RETRY"],
        }
    )
    quality_core = _common(
        root,
        decision_id="DECISION-QUALITY-EVIDENCE-SUFFICIENCY-002D-R1",
        decision_type="EVIDENCE_SUFFICIENCY",
        target_ids=["QUALITY_EVIDENCE"],
        evidence_sufficiency="INSUFFICIENT",
    )
    quality_core.update(
        {
            "eligible_evidence": [quality["record_id"]],
            "decision": "EVIDENCE_INSUFFICIENT",
            "reason_codes": quality["reason_codes"],
            "accepted_scope": "NONE",
            "rejected_scope": ["QUALITY_SUPERIORITY", "BASE_SELECTION", "PHASE_003"],
            "retest_requirements": [
                "A newly frozen acquisition design must reach four balanced cases.",
                "A newly frozen acquisition design must reach quality repeat depth two.",
            ],
        }
    )
    reliability_core = _common(
        root,
        decision_id="DECISION-RELIABILITY-EVIDENCE-SUFFICIENCY-002D-R1",
        decision_type="EVIDENCE_SUFFICIENCY",
        target_ids=["OBSERVED_COHORT_RELIABILITY"],
        evidence_sufficiency="SUFFICIENT",
    )
    reliability_core.update(
        {
            "eligible_evidence": [reliability["record_id"], retry["audit_id"]],
            "decision": "AUTOMATED_ACCEPTED",
            "reason_codes": reliability["reason_codes"],
            "accepted_scope": "RELIABILITY_ONLY",
            "rejected_scope": ["QUALITY_INFERENCE", "PERFORMANCE_SUPERIORITY"],
            "confidence": 0.9,
        }
    )
    architecture_gate = evaluate_architecture_gate(
        freeze_valid=True,
        quality_sufficient=quality["result"] != "EVIDENCE_INSUFFICIENT",
        posthoc_policy=True,
    )
    architecture = _common(
        root,
        decision_id="DECISION-ARCHITECTURE-002D-R1",
        decision_type="ARCHITECTURE",
        target_ids=["RETAIN_SCAFFOLD_ONLY"],
        evidence_sufficiency="INSUFFICIENT",
    )
    architecture.update(
        {
            "eligible_evidence": [quality["record_id"], reliability["record_id"]],
            "decision": architecture_gate["decision"],
            "reason_codes": [
                "QUALITY_EVIDENCE_INSUFFICIENT",
                "POSTHOC_POLICY_CANNOT_PROVE_ARCHITECTURE_SUPERIORITY",
                "RETAIN_SCAFFOLD_ONLY_WITHOUT_SELECTION",
            ],
            "accepted_scope": "NONE",
            "rejected_scope": [
                "NATIVE_SINGLE_SKILL_CLEAN_ROOM",
                "BASE_SELECTION",
                "IMPLEMENTATION_READY",
                "PHASE_003",
            ],
            "retest_requirements": quality_core["retest_requirements"],
        }
    )
    mechanisms = (
        "accepted-versus-done-workflow-state",
        "claim-evidence-support-gate",
        "hash-bound-reproducibility-manifest",
        "leakage-safe-model-comparison-gate",
    )
    components = _common(
        root,
        decision_id="DECISION-COMPONENT-READINESS-002D-R1",
        decision_type="COMPONENT_READINESS",
        target_ids=list(mechanisms),
        evidence_sufficiency="SUFFICIENT",
    )
    components.update(
        {
            "eligible_evidence": [
                scopes["scope_summary_id"],
                "PHASE-002D-R1-FIRST-ROUND-FINDING-CLOSURE-001",
            ],
            "decision": "AUTOMATED_ACCEPTED",
            "reason_codes": [
                "REPEATED_GAPS_SUPPORT_SPECIFICATION_ONLY",
                "IMPLEMENTATION_EFFECT_NOT_ESTABLISHED",
            ],
            "accepted_scope": "SPECIFICATION_ONLY",
            "component_results": [
                {
                    "mechanism_id": mechanism,
                    "decision": "AUTOMATED_ACCEPTED",
                    "accepted_scope": "SPECIFICATION_ONLY",
                    "reason_codes": [
                        "REPEATED_COMPONENT_GAP_OBSERVED",
                        "SPECIFICATION_NOT_IMPLEMENTATION",
                    ],
                    "evidence_refs": [scopes["scope_summary_id"]],
                    "required_tests": [f"FUTURE-IMPLEMENTATION-TEST:{mechanism}"],
                    "maintenance_cost": "MEDIUM",
                }
                for mechanism in mechanisms
            ],
            "rejected_scope": [
                "DIRECT_REUSE",
                "IMPLEMENTATION_READY",
                "PRODUCTION_READY",
                "INTEGRATED",
            ],
            "confidence": 0.8,
        }
    )
    return [
        _wrap(policy, evidence_scope="POLICY", accepted_scope="POLICY_ONLY"),
        _wrap(slot, evidence_scope="OUTCOME_COMPLETENESS", accepted_scope="POLICY_ONLY"),
        _wrap(supplemental_core, evidence_scope="POLICY", accepted_scope="NONE"),
        _wrap(quality_core, evidence_scope="QUALITY_EVIDENCE", accepted_scope="NONE"),
        _wrap(
            reliability_core,
            evidence_scope="RELIABILITY_EVIDENCE",
            accepted_scope="RELIABILITY_ONLY",
        ),
        _wrap(architecture, evidence_scope="QUALITY_EVIDENCE", accepted_scope="NONE"),
        _wrap(
            components,
            evidence_scope="COMPONENT_GAP_EVIDENCE",
            accepted_scope="SPECIFICATION_ONLY",
        ),
    ]


def validate_decisions(root: Path, decisions: list[dict[str, Any]]) -> list[str]:
    core_validator = Draft202012Validator(
        read_json(root / "contracts/automated_decision.schema.json")
    )
    envelope_validator = Draft202012Validator(
        read_json(root / "contracts/failure_aware_decision.schema.json")
    )
    errors = []
    ids = []
    for envelope in decisions:
        core = envelope["automated_decision"]
        ids.append(core["decision_id"])
        if core.get("accepted_scope") != envelope.get("accepted_scope"):
            errors.append(f"FAILURE_AWARE_ACCEPTED_SCOPE_MISMATCH:{core['decision_id']}")
        errors.extend(
            f"AUTOMATED_DECISION:{item.message}" for item in core_validator.iter_errors(core)
        )
        errors.extend(
            f"FAILURE_AWARE_DECISION:{item.message}"
            for item in envelope_validator.iter_errors(envelope)
        )
        body = dict(envelope)
        recorded_hash = body.pop("failure_aware_hash", None)
        if sha256_json(body) != recorded_hash:
            errors.append(f"FAILURE_AWARE_HASH_MISMATCH:{core['decision_id']}")
    if set(ids) != set(DECISION_FILES) or len(ids) != len(set(ids)):
        errors.append("FAILURE_AWARE_DECISION_SET_MISMATCH")
    return sorted(set(errors))


def check_or_write_sufficiency(root: Path, *, scope: str, check: bool) -> dict[str, Any]:
    quality, reliability = build_sufficiency_records(root)
    value, path = (quality, QUALITY_PATH) if scope == "quality" else (reliability, RELIABILITY_PATH)
    errors = check_or_write(root / path, value, check=check)
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "scope": value["scope"],
        "result": value["result"],
        "record_hash": value["record_hash"],
    }


def check_or_write_decisions(root: Path, *, check: bool) -> dict[str, Any]:
    decisions = build_decisions(root)
    errors = validate_decisions(root, decisions)
    for envelope in decisions:
        decision_id = envelope["automated_decision"]["decision_id"]
        errors.extend(
            check_or_write(
                root / DECISION_ROOT / DECISION_FILES[decision_id], envelope, check=check
            )
        )
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "decision_count": len(decisions),
        "decisions": {
            item["automated_decision"]["decision_id"]: {
                "decision": item["automated_decision"]["decision"],
                "accepted_scope": item["accepted_scope"],
                "hash": item["failure_aware_hash"],
            }
            for item in decisions
        },
    }
