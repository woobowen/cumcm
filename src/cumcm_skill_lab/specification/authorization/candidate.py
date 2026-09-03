"""Generate the non-active R2A authorization candidate from machine preconditions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import check_or_write, read_json, read_yaml, sha256_json

from .adversarial_closure import CLOSURE_PATH
from .bindings import ACTIVE_AUTHORIZATION_ID, CANDIDATE_ID
from .models import DEPENDENCY_PATH, FREEZE_PATH, RESULT_ROOT
from .native_audits import FIRST_ROUND_ROLES, OUTPUT_ROOT
from .preconditions import PRECONDITIONS_PATH, build_preconditions
from .scope import SCOPE_PATH

CANDIDATE_PATH = RESULT_ROOT / "authorization_candidate/candidate.json"
CREATED_AT = "2026-09-03T04:10:00+08:00"


def _finalize_core(core: dict[str, Any]) -> dict[str, Any]:
    value = dict(core)
    value["replay_hash"] = sha256_json(value)
    return value


def _decision_from_preconditions(preconditions: dict[str, Any]) -> str:
    if preconditions["eligibility"] == "STALE":
        return "STALE"
    if preconditions["all_required_pass"]:
        return "AUTOMATED_ACCEPTED"
    return "RETEST_REQUIRED"


def build_authorization_candidate(root: Path) -> dict[str, Any]:
    freeze = read_json(root / FREEZE_PATH)
    graph = read_json(root / DEPENDENCY_PATH)
    preconditions = build_preconditions(root)
    scope = read_yaml(root / SCOPE_PATH)
    closure = read_json(root / CLOSURE_PATH)
    first_round = [read_json(root / OUTPUT_ROOT / f"{role}.json") for role in FIRST_ROUND_ROLES]
    decision = _decision_from_preconditions(preconditions)
    accepted = decision == "AUTOMATED_ACCEPTED"
    failed = preconditions["failed_check_ids"]
    finding_ids = sorted(item["finding_id"] for audit in first_round for item in audit["findings"])
    test_ids = sorted(item["test_id"] for item in closure["closures"])
    proposed_route = (
        "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"
        if accepted
        else (
            None if decision == "STALE" else "PHASE-002D-R2A-SHADOW-PROTOTYPE-AUTHORIZATION-CLOSURE"
        )
    )
    core = _finalize_core(
        {
            "decision_id": ACTIVE_AUTHORIZATION_ID,
            "decision_type": "RECOVERY_POLICY",
            "target_ids": scope["candidate_ids"],
            "evidence_freeze_id": freeze["freeze_id"],
            "policy_version": "phase002d-r2a/1.0.0",
            "hard_gate_status": "PASS" if accepted else "FAIL",
            "evidence_sufficiency": "SUFFICIENT" if accepted else "INSUFFICIENT",
            "eligible_evidence": [
                FREEZE_PATH.as_posix(),
                DEPENDENCY_PATH.as_posix(),
                PRECONDITIONS_PATH.as_posix(),
                SCOPE_PATH.as_posix(),
                CLOSURE_PATH.as_posix(),
                "evals/results/phase-002d-r2/decision_audit/audit.json",
                "evals/results/phase-002d-r2/replay/replay.json",
            ],
            "excluded_evidence": [
                "AGENT_VOTES",
                "HUMAN_TECHNICAL_GATE",
                "HIDDEN_VAULT_VALUES",
                "PROTOTYPE_RESULTS",
                "MODEL_STAGE2_RESULTS",
                "THIRD_PARTY_EXECUTABLE_CONTENT",
                "LEGAL_COMPLIANCE_ASSUMPTIONS",
                "OS_ISOLATION_ASSUMPTIONS",
                "MONETARY_COST_ASSUMPTIONS",
            ],
            "judge_decisions": [],
            "dissent_findings": finding_ids,
            "tests": test_ids,
            "meta_adjudication": "DETERMINISTIC_R2A_AUTHORIZATION_CANDIDATE_NO_VOTE",
            "decision_audit": "PENDING:R2A-AUDIT-FINAL-SHADOW-AUTHORIZATION-001",
            "decision": decision,
            "reason_codes": (
                [
                    "R2_POST_AUDIT_AND_REPLAY_PREREQUISITES_PASS",
                    "BOUNDED_EXPERIMENTAL_SHADOW_SCOPE_ONLY",
                    "FUTURE_RUNTIME_GATES_FAIL_CLOSED",
                    "MODEL_STAGE2_NOT_AUTHORIZED",
                    "ARCHITECTURE_NOT_SELECTED",
                ]
                if accepted
                else [f"PRECONDITION_NOT_PASS:{item}" for item in failed] or ["INPUT_FREEZE_STALE"]
            ),
            "accepted_scope": "POLICY_ONLY" if accepted else "NONE",
            "rejected_scope": [
                "FORMAL_SKILL_IMPLEMENTATION",
                "FORMAL_INTEGRATION",
                "PRODUCTION_READY",
                "DIRECT_REUSE",
                "ARCHITECTURE_SELECTED",
                "PHASE_003_INTEGRATION",
                "MODEL_STAGE2_WITHOUT_NEW_FROZEN_AUTHORIZATION",
                "PROTOTYPE_EXECUTION_BEFORE_RUNTIME_GATES",
            ],
            "retest_requirements": failed,
            "stale_dependencies": [FREEZE_PATH.as_posix()] if decision == "STALE" else [],
            "confidence": 1.0,
            "next_phase_allowed": proposed_route,
            "created_at": CREATED_AT,
        }
    )
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_type": "SHADOW_AUTHORIZATION_CANDIDATE_NOT_ACTIVE",
        "candidate_id": CANDIDATE_ID,
        "active": False,
        "created_at": CREATED_AT,
        "automated_decision_contract": "contracts/automated_decision.schema.json",
        "proposed_automated_decision": core,
        "proposed_authorization_id": ACTIVE_AUTHORIZATION_ID,
        "proposed_accepted_scope": ("EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY" if accepted else None),
        "proposed_next_phase_allowed": proposed_route,
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["manifest_hash"],
        "dependency_graph_hash": graph["graph_hash"],
        "preconditions_hash": preconditions["preconditions_hash"],
        "scope_hash": scope["scope_hash"],
        "finding_closure_hash": closure["closure_hash"],
        "supersedes": {
            "decision_id": freeze["old_shadow_authorization"]["decision_id"],
            "artifact_path": freeze["old_shadow_authorization"]["path"],
            "decision_hash": freeze["old_shadow_authorization"]["decision_hash"],
            "file_sha256": freeze["old_shadow_authorization"]["file_sha256"],
            "historical_decision": freeze["old_shadow_authorization"]["decision"],
        },
        "supersession_reason": "POST_AUDIT_AND_REPLAY_CLOSURE",
        "historical_decision_was_correct_at_creation_time": True,
        "restrictions": [
            "NO_ARCHITECTURE_SELECTION",
            "NO_FORMAL_SKILL_INTEGRATION",
            "NO_PHASE_003",
            "NO_MODEL_STAGE2_WITHOUT_NEW_FROZEN_AUTHORIZATION",
            "NO_FILE_WRITES_BEFORE_CONFINEMENT_AND_DEPENDENCY_GATES",
            "NO_EXECUTION_BEFORE_ALL_RUNTIME_GATES",
        ],
        "unknowns": preconditions["unknowns"],
        "selected_architecture": None,
        "base_selected": False,
        "third_party_integrated": False,
        "formal_state_transition_performed": False,
        "majority_vote_used": False,
        "prototype_implemented": False,
        "prototype_executed": False,
        "real_batch_model_runs": 0,
        "api_calls": 0,
        "third_party_executions": 0,
    }
    body["candidate_hash"] = sha256_json(body)
    return body


def validate_authorization_candidate(root: Path, value: dict[str, Any]) -> list[str]:
    errors = [
        f"R2A_CANDIDATE_DECISION_SCHEMA:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(
            read_json(root / "contracts/automated_decision.schema.json")
        ).iter_errors(value.get("proposed_automated_decision", {}))
    ]
    body = dict(value)
    recorded_hash = body.pop("candidate_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("R2A_CANDIDATE_HASH_MISMATCH")
    expected = build_authorization_candidate(root)
    for field in (
        "candidate_id",
        "active",
        "proposed_authorization_id",
        "input_freeze_id",
        "input_freeze_hash",
        "dependency_graph_hash",
        "preconditions_hash",
        "scope_hash",
        "finding_closure_hash",
        "supersedes",
        "supersession_reason",
        "selected_architecture",
        "base_selected",
        "third_party_integrated",
        "formal_state_transition_performed",
        "majority_vote_used",
    ):
        if value.get(field) != expected.get(field):
            errors.append(f"R2A_CANDIDATE_{field.upper()}_MISMATCH")
    if (
        value.get("active") is not False
        or value.get("formal_state_transition_performed") is not False
    ):
        errors.append("R2A_CANDIDATE_PREMATURE_ACTIVATION")
    return sorted(set(errors))


def check_or_write_authorization_candidate(root: Path, *, check: bool) -> dict[str, Any]:
    expected = build_authorization_candidate(root)
    errors = validate_authorization_candidate(root, expected)
    errors.extend(check_or_write(root / CANDIDATE_PATH, expected, check=check))
    decision = expected["proposed_automated_decision"]
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "candidate_id": expected["candidate_id"],
        "candidate_hash": expected["candidate_hash"],
        "decision": decision["decision"],
        "proposed_accepted_scope": expected["proposed_accepted_scope"],
        "proposed_next_phase_allowed": expected["proposed_next_phase_allowed"],
        "active": expected["active"],
        "formal_state_transition_performed": expected["formal_state_transition_performed"],
    }


__all__ = [
    "CANDIDATE_PATH",
    "build_authorization_candidate",
    "check_or_write_authorization_candidate",
    "validate_authorization_candidate",
]
