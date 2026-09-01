"""Authorize only protocol-identical, targeted Phase 002D-R1 supplemental starts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .evidence_freeze import verify_input_freeze
from .models import RESULT_ROOT, SOURCE_ROOT, check_or_write, hashed_body, read_json, sha256_json
from .native_audits import validate_first_round
from .slot_matrix import build_slot_matrix

AUTHORIZATION_PATH = RESULT_ROOT / "supplemental/authorization.json"
BUDGET_PATH = RESULT_ROOT / "supplemental/budget.json"
PRE_AUDIT_PATH = RESULT_ROOT / "supplemental/authorization_pre_audit.json"
STATUS_PATH = RESULT_ROOT / "supplemental/status.json"
BLOCKER_TEST_EVIDENCE_PATH = RESULT_ROOT / "adversarial_tests/test_evidence.json"

PROTOCOL_FIELDS = (
    "cohort_hash",
    "model",
    "reasoning_setting",
    "prompt_hash",
    "schema_hash",
    "fixture_hash",
    "package_hash",
    "scorer_hash",
    "oracle_hash",
    "transport_profile",
)
START_PRECONDITIONS = (
    "input_freeze_pass",
    "five_subagent_outputs_valid",
    "blocker_tests_passed",
    "authorization_accepted",
    "authorization_pre_audit_pass",
    "supplemental_budget_frozen",
    "authorized_slot_list_nonempty",
)


def build_protocol_fingerprint(root: Path) -> dict[str, str]:
    source = read_json(root / SOURCE_ROOT / "input_freeze_manifest.json")
    r1 = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    return {
        "cohort_hash": r1["cohort_hash"],
        "model": r1["model"],
        "reasoning_setting": r1["reasoning_setting"],
        "prompt_hash": sha256_json(source["bound_code_hashes"]),
        "schema_hash": sha256_json(source["output_schema_hashes"]),
        "fixture_hash": sha256_json(source["case_fixture_rubric_hashes"]),
        "package_hash": sha256_json(source["candidate_package_hashes"]),
        "scorer_hash": source["scorer_hash"],
        "oracle_hash": source["oracle_hash"],
        "transport_profile": r1["transport_profile"],
    }


def protocol_compatibility(frozen: dict[str, str], candidate: dict[str, str]) -> dict[str, Any]:
    drift = [field for field in PROTOCOL_FIELDS if candidate.get(field) != frozen.get(field)]
    return {
        "result": "PASS" if not drift else "NEW_PROTOCOL_COHORT_REQUIRED",
        "drift_fields": drift,
        "pool_with_current_evidence": not drift,
    }


def harness_semantic_equivalence(root: Path) -> dict[str, Any]:
    slot_id = "CASE-001-ARM-A-R2"
    attempts = (
        "EXP-CASE-001-ARM-A-R2-A01",
        "EXP-CASE-001-ARM-A-R2-A03",
    )
    bound_files = []
    body = {
        "schema_version": "1.0.0",
        "equivalence_id": "PHASE-002D-R1-HARNESS-SEMANTIC-EQUIVALENCE-001",
        "slot_id": slot_id,
        "attempt_ids": list(attempts),
        "status": "NOT_ESTABLISHED",
        "claimed_namespace": ".harness/",
        "bound_file_hashes": bound_files,
        "semantic_equivalence_pass": False,
        "supplemental_eligible": False,
        "reason": "CLAIMED_FILES_HAVE_NO_AUTHORITATIVE_BOUND_WORKSPACE_FILES",
        "evidence_refs": [
            f"evals/results/phase-002d/attempts/{attempt_id}.json" for attempt_id in attempts
        ],
    }
    return hashed_body(body, "equivalence_hash")


def build_authorization(root: Path) -> dict[str, Any]:
    slots, matrix, _ = build_slot_matrix(root)
    freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    equivalence = harness_semantic_equivalence(root)
    assessments = []
    authorized = []
    for slot in slots:
        resolution = slot["outcome_resolution"]
        if resolution == "CENSORED_INFRASTRUCTURE":
            eligible = True
            reason = "INFRASTRUCTURE_CENSORED"
        elif resolution == "CENSORED_HARNESS":
            eligible = equivalence["semantic_equivalence_pass"]
            reason = (
                "HARNESS_SEMANTIC_EQUIVALENCE_PASS"
                if eligible
                else "HARNESS_SEMANTIC_EQUIVALENCE_NOT_ESTABLISHED"
            )
        else:
            eligible = False
            reason = f"PROHIBITED_{resolution}"
        assessments.append(
            {
                "slot_id": slot["slot_id"],
                "outcome_resolution": resolution,
                "eligible": eligible,
                "reason": reason,
            }
        )
        if eligible:
            authorized.append(slot["slot_id"])
    decision = "AUTOMATED_ACCEPTED" if authorized else "AUTOMATED_REJECTED"
    body = {
        "schema_version": "1.0.0",
        "decision_id": "DECISION-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1",
        "decision": decision,
        "target": "TARGETED_CENSORED_SLOTS_ONLY" if authorized else "SUPPLEMENTAL_GENERIC_RUNS",
        "accepted_scope": "TARGETED_CENSORED_SLOTS_ONLY" if authorized else "NONE",
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["manifest_hash"],
        "slot_matrix_hash": matrix["matrix_hash"],
        "harness_semantic_equivalence": equivalence,
        "slot_assessments": assessments,
        "authorized_slot_ids": authorized,
        "maximum_real_starts": min(4, len(authorized) * 2),
        "maximum_starts_per_slot": 2 if authorized else 0,
        "protocol_fingerprint": build_protocol_fingerprint(root),
        "generic_retry_authorized": False,
        "original_budget_mutated": False,
        "api_key_used": False,
        "api_billing_used": False,
        "majority_vote_used": False,
        "human_technical_gate_used": False,
        "evidence_refs": [
            "PHASE-002D-R1-INPUT-FREEZE-001",
            "PHASE-002D-R1-SLOT-OUTCOME-MATRIX-001",
            equivalence["equivalence_id"],
        ],
    }
    return hashed_body(body, "authorization_hash")


def build_budget(authorization: dict[str, Any]) -> dict[str, Any]:
    authorized = authorization["authorized_slot_ids"]
    body = {
        "schema_version": "1.0.0",
        "budget_id": "PHASE-002D-R1-SUPPLEMENTAL-BUDGET-001",
        "status": "FROZEN" if authorized else "NOT_AUTHORIZED",
        "authorization_id": authorization["decision_id"],
        "authorization_hash": authorization["authorization_hash"],
        "source_budget_id": "PHASE-002D-FROZEN-BUDGET-001",
        "source_budget_mutated": False,
        "authorized_slot_ids": authorized,
        "maximum_total_starts": authorization["maximum_real_starts"],
        "maximum_starts_per_slot": authorization["maximum_starts_per_slot"],
        "concurrency": 1,
        "fresh_sessions_only": True,
        "resume_allowed": False,
        "recovery_allowed": False,
        "protocol_fingerprint": authorization["protocol_fingerprint"],
        "immutable": True,
        "api_key_used": False,
        "api_billing_used": False,
    }
    return hashed_body(body, "budget_hash")


def evaluate_start_preconditions(preconditions: dict[str, bool]) -> list[str]:
    return [name for name in START_PRECONDITIONS if preconditions.get(name) is not True]


def _blocker_tests_passed(root: Path) -> bool:
    path = root / BLOCKER_TEST_EVIDENCE_PATH
    if not path.is_file():
        return False
    evidence = read_json(path).get("evidence", [])
    serious = [item for item in evidence if item["finding_id"] != "EXPERIMENT-PROTOCOL-003"]
    return bool(serious) and all(item["status"] == "PASSED" for item in serious)


def build_pre_audit(root: Path, authorization: dict[str, Any], budget: dict[str, Any]) -> dict:
    checks = {
        "input_freeze_pass": not verify_input_freeze(root),
        "five_subagent_outputs_valid": not validate_first_round(root),
        "blocker_tests_passed": _blocker_tests_passed(root),
        "authorization_scope_valid": (
            not authorization["authorized_slot_ids"]
            and authorization["decision"] == "AUTOMATED_REJECTED"
            and authorization["maximum_real_starts"] == 0
        ),
        "supplemental_budget_bounded": budget["maximum_total_starts"] <= 4,
        "original_budget_immutable": not authorization["original_budget_mutated"],
    }
    body = {
        "schema_version": "1.0.0",
        "audit_id": "AUDIT-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1",
        "checks": checks,
        "result": "PASS" if all(checks.values()) else "RETEST_REQUIRED",
        "authorization_hash": authorization["authorization_hash"],
        "budget_hash": budget["budget_hash"],
    }
    return hashed_body(body, "audit_hash")


def build_status_receipt(
    root: Path,
    authorization: dict[str, Any],
    budget: dict[str, Any],
    pre_audit: dict[str, Any],
) -> dict[str, Any]:
    preconditions = {
        "input_freeze_pass": not verify_input_freeze(root),
        "five_subagent_outputs_valid": not validate_first_round(root),
        "blocker_tests_passed": _blocker_tests_passed(root),
        "authorization_accepted": authorization["decision"] == "AUTOMATED_ACCEPTED",
        "authorization_pre_audit_pass": pre_audit["result"] == "PASS",
        "supplemental_budget_frozen": budget["status"] == "FROZEN",
        "authorized_slot_list_nonempty": bool(authorization["authorized_slot_ids"]),
    }
    missing = evaluate_start_preconditions(preconditions)
    body = {
        "schema_version": "1.0.0",
        "receipt_id": "PHASE-002D-R1-SUPPLEMENTAL-STATUS-001",
        "authorization_hash": authorization["authorization_hash"],
        "budget_hash": budget["budget_hash"],
        "pre_audit_hash": pre_audit["audit_hash"],
        "preconditions": preconditions,
        "missing_preconditions": missing,
        "authorized_slot_ids": authorization["authorized_slot_ids"],
        "model_start_count": 0,
        "maximum_real_starts": authorization["maximum_real_starts"],
        "launch_locked": bool(missing),
        "status": (
            "ZERO_STARTS_NOT_AUTHORIZED" if not authorization["authorized_slot_ids"] else "READY"
        ),
        "api_key_used": False,
        "api_billing_used": False,
    }
    return hashed_body(body, "receipt_hash")


def check_or_write_supplemental(root: Path, *, check: bool) -> dict[str, Any]:
    authorization = build_authorization(root)
    budget = build_budget(authorization)
    pre_audit = build_pre_audit(root, authorization, budget)
    status = build_status_receipt(root, authorization, budget, pre_audit)
    outputs = {
        AUTHORIZATION_PATH: authorization,
        BUDGET_PATH: budget,
        PRE_AUDIT_PATH: pre_audit,
        STATUS_PATH: status,
    }
    errors: list[str] = []
    for contract, value in (
        ("contracts/supplemental_run_authorization.schema.json", authorization),
        ("contracts/supplemental_budget.schema.json", budget),
    ):
        errors.extend(
            f"SUPPLEMENTAL_SCHEMA:{item.message}"
            for item in Draft202012Validator(read_json(root / contract)).iter_errors(value)
        )
    for path, value in outputs.items():
        errors.extend(check_or_write(root / path, value, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "decision": authorization["decision"],
        "authorized_slot_ids": authorization["authorized_slot_ids"],
        "maximum_real_starts": authorization["maximum_real_starts"],
        "model_start_count": status["model_start_count"],
        "authorization_hash": authorization["authorization_hash"],
        "budget_hash": budget["budget_hash"],
        "receipt_hash": status["receipt_hash"],
    }
