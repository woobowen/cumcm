"""Seal and replay the audited C2 shadow authorization without implementing a prototype."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.authorization_c1.models import (
    CREATED_AT,
    INPUT_FREEZE_PATH,
    RESULT_ROOT,
    check_or_write_json,
    file_sha256,
    sha256_json,
)

from .candidate_evidence import CLOSURE_PATH, PRECONDITIONS_PATH, TEST_EVIDENCE_PATH, TEST_PLAN_PATH
from .candidate_freeze import CANDIDATE_PATH, DECISION_ID, FREEZE_PATH, validate_candidate_freeze
from .final_audit import FINAL_AUDIT_PATH, evaluate_final_audit_gate, validate_final_audit
from .final_audit_bundle import BUNDLE_PATH, validate_final_audit_bundle

AUTHORIZATION_PATH = RESULT_ROOT / "authorization_decision/authorization-c2.json"
REPLAY_PATH = RESULT_ROOT / "replay/replay-c2.json"
AUTHORIZATION_CONTRACT = Path("contracts/c2_authorization_seal.schema.json")
AUTOMATED_DECISION_CONTRACT = Path("contracts/automated_decision.schema.json")
OLD_R2_DECISION_PATH = Path(
    "evals/results/phase-002d-r2/automated_decisions/shadow_prototype_authorization.json"
)
OLD_R2A_CANDIDATE_PATH = Path("evals/results/phase-002d-r2a/authorization_candidate/candidate.json")
C1_FREEZE_PATH = RESULT_ROOT / "candidate_freeze/candidate_freeze_manifest-c1.json"
C2_SCOPE = "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY"
C2_ROUTE = "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"C2_TERMINAL_JSON_OBJECT_REQUIRED:{path.as_posix()}")
    return value


def _schema_errors(root: Path, contract: Path, value: dict[str, Any], prefix: str) -> list[str]:
    schema = _read_json(root / contract)
    return sorted(
        f"{prefix}:{'/'.join(map(str, error.absolute_path))}:{error.message}"
        for error in Draft202012Validator(schema).iter_errors(value)
    )


def _decision_projection(candidate: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "decision": candidate["decision"],
        "accepted_scope": candidate["accepted_scope"],
        "next_phase_allowed": candidate["next_phase_allowed"],
        "selected_architecture": candidate["selected_architecture"],
        "base_selected": candidate["base_selected"],
        "third_party_integrated": candidate["third_party_integrated"],
        "skill_capability_status": candidate["skill_capability_status"],
        "phase003_prohibited": candidate["phase003_prohibited"],
        "final_audit_result": audit["verdict"],
    }


def _build_automated_decision(
    candidate: dict[str, Any],
    freeze: dict[str, Any],
    evidence: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    accepted = candidate["decision"] == "AUTOMATED_ACCEPTED"
    decision_replay_hash = sha256_json(_decision_projection(candidate, audit))
    return {
        "decision_id": DECISION_ID,
        "decision_type": "RECOVERY_POLICY",
        "target_ids": [candidate["candidate_id"]],
        "evidence_freeze_id": freeze["freeze_id"],
        "policy_version": "phase002d-r2a-c2/1.0.0",
        "hard_gate_status": "PASS" if accepted else "FAIL",
        "evidence_sufficiency": "SUFFICIENT" if accepted else "INSUFFICIENT",
        "eligible_evidence": sorted(evidence["test_evidence_hashes"]),
        "excluded_evidence": [
            "AGENT_VOTES",
            "HUMAN_TECHNICAL_OVERRIDE",
            "HIDDEN_VAULT_VALUES",
            "PROTOTYPE_OR_MODEL_RESULTS",
            "RECOVERY_AFFECTED_COMPARATIVE_RESULTS",
            "THIRD_PARTY_EXECUTION",
        ],
        "judge_decisions": [],
        "dissent_findings": [],
        "tests": sorted(evidence["test_evidence_hashes"]),
        "meta_adjudication": "DETERMINISTIC_CANDIDATE_BOUND_POLICY_ENGINE_NO_VOTE",
        "decision_audit": audit["audit_id"],
        "decision": candidate["decision"],
        "reason_codes": (
            [
                "FINAL_AUTHORIZATION_AUDITOR_PASS",
                "EXACT_CANDIDATE_EVIDENCE_PASS",
                "HISTORICAL_AND_SCHEMA_COMPATIBILITY_PASS",
                "IMPLEMENTATION_EMBARGO_PASS",
            ]
            if accepted
            else ["C2_FROZEN_PREREQUISITE_NOT_ACCEPTED"]
        ),
        # The generic decision contract classifies this authorization as a policy scope.
        # The exact experimental execution boundary is carried by accepted_scope at the seal level.
        "accepted_scope": "POLICY_ONLY" if accepted else "NONE",
        "rejected_scope": [
            "ARCHITECTURE_SELECTION",
            "BASE_SELECTION",
            "FORMAL_SKILL_IMPLEMENTATION",
            "FORMAL_INTEGRATION",
            "PRODUCTION",
            "PHASE_003",
        ],
        "retest_requirements": [] if accepted else ["NEW_FROZEN_CANDIDATE_REVISION"],
        "stale_dependencies": [],
        "confidence": 1.0,
        "replay_hash": decision_replay_hash,
        "next_phase_allowed": candidate["next_phase_allowed"],
        "created_at": CREATED_AT,
    }


def build_authorization_seal(root: Path) -> dict[str, Any]:
    """Build L19 from frozen C2 inputs and the passing L18 audit."""
    candidate = _read_json(root / CANDIDATE_PATH)
    freeze = _read_json(root / FREEZE_PATH)
    input_freeze = _read_json(root / INPUT_FREEZE_PATH)
    preconditions = _read_json(root / PRECONDITIONS_PATH)
    plan = _read_json(root / TEST_PLAN_PATH)
    evidence = _read_json(root / TEST_EVIDENCE_PATH)
    closure = _read_json(root / CLOSURE_PATH)
    bundle = _read_json(root / BUNDLE_PATH)
    audit = _read_json(root / FINAL_AUDIT_PATH)
    old_r2 = _read_json(root / OLD_R2_DECISION_PATH)
    old_candidate = input_freeze["old_candidate"]
    c1_freeze = _read_json(root / C1_FREEZE_PATH)
    accepted = candidate["decision"] == "AUTOMATED_ACCEPTED"
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_type": "ACTIVE_SHADOW_PROTOTYPE_AUTHORIZATION",
        "authorization_id": DECISION_ID,
        "artifact_path": AUTHORIZATION_PATH.as_posix(),
        "parent_artifact_hash": audit["output_hash"],
        "artifact_sequence_index": 19,
        "automated_decision_contract": AUTOMATED_DECISION_CONTRACT.as_posix(),
        "automated_decision": _build_automated_decision(candidate, freeze, evidence, audit),
        "decision": candidate["decision"],
        "accepted_scope": C2_SCOPE if accepted else None,
        "candidate_id": candidate["candidate_id"],
        "candidate_path": CANDIDATE_PATH.as_posix(),
        "candidate_file_sha256": freeze["candidate_file_sha256"],
        "canonical_candidate_hash": freeze["canonical_candidate_hash"],
        "candidate_freeze_hash": freeze["freeze_hash"],
        "input_freeze_id": input_freeze["freeze_id"],
        "input_freeze_hash": input_freeze["manifest_hash"],
        "dependency_graph_hash": candidate["input_references"]["c2_dependency_graph_hash"],
        "dependency_resolution_hash": candidate["input_references"][
            "c2_dependency_resolution_hash"
        ],
        "preconditions_hash": preconditions["preconditions_hash"],
        "test_plan_hash": plan["test_plan_hash"],
        "test_evidence_set_hash": evidence["evidence_hash"],
        "candidate_closure_hash": closure["closure_hash"],
        "final_audit_bundle_hash": bundle["bundle_hash"],
        "final_audit_id": audit["audit_id"],
        "final_audit_result": audit["verdict"],
        "final_audit_output_hash": audit["output_hash"],
        "supersedes": {
            "decision_id": old_r2["automated_decision"]["decision_id"],
            "artifact_path": OLD_R2_DECISION_PATH.as_posix(),
            "decision_hash": old_r2["decision_hash"],
            "file_sha256": file_sha256(root / OLD_R2_DECISION_PATH),
            "historical_decision": old_r2["automated_decision"]["decision"],
            "preserved": True,
        },
        "replaces_historical_non_active_candidate": {
            **old_candidate,
            "preserved": file_sha256(root / OLD_R2A_CANDIDATE_PATH) == old_candidate["file_sha256"],
        },
        "replaces_failed_c1_revision": {
            "candidate_id": c1_freeze["candidate_id"],
            "candidate_file_sha256": c1_freeze["candidate_file_sha256"],
            "canonical_candidate_hash": c1_freeze["canonical_candidate_hash"],
            "candidate_freeze_hash": c1_freeze["freeze_hash"],
            "classification": "FROZEN_FAILED_C1_CANDIDATE",
            "preserved": True,
        },
        "supersession_reason": "POST_CANDIDATE_BOUND_EVIDENCE_AND_FINAL_AUDIT_PASS",
        "restrictions": candidate["restrictions"],
        "selected_architecture": None,
        "base_selected": False,
        "third_party_integrated": False,
        "skill_capability_status": "SCAFFOLD_ONLY",
        "prototype_implemented": False,
        "prototype_executed": False,
        "real_model_in_loop_runs": 0,
        "api_calls": 0,
        "third_party_executions": 0,
        "majority_vote_used": False,
        "next_phase_allowed": C2_ROUTE if accepted else None,
        "phase003_prohibited": True,
    }
    body["authorization_hash"] = sha256_json(body)
    return body


def validate_authorization_seal(root: Path, value: dict[str, Any]) -> list[str]:
    errors = list(evaluate_final_audit_gate(root, "SEAL")["errors"])
    freeze = _read_json(root / FREEZE_PATH)
    bundle = _read_json(root / BUNDLE_PATH)
    audit = _read_json(root / FINAL_AUDIT_PATH)
    errors.extend(validate_candidate_freeze(root, freeze))
    errors.extend(validate_final_audit_bundle(root, bundle))
    errors.extend(validate_final_audit(root, audit))
    errors.extend(_schema_errors(root, AUTHORIZATION_CONTRACT, value, "C2_SEAL_SCHEMA"))
    automated = value.get("automated_decision")
    if isinstance(automated, dict):
        errors.extend(
            _schema_errors(root, AUTOMATED_DECISION_CONTRACT, automated, "C2_AUTOMATED_DECISION")
        )
    else:
        errors.append("C2_AUTOMATED_DECISION_OBJECT_REQUIRED")
    body = deepcopy(value)
    recorded_hash = body.pop("authorization_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("C2_AUTHORIZATION_HASH_MISMATCH")
    if value != build_authorization_seal(root):
        errors.append("C2_AUTHORIZATION_SEAL_NOT_REPRODUCIBLE")
    if value.get("parent_artifact_hash") != audit.get("output_hash"):
        errors.append("C2_AUTHORIZATION_PARENT_AUDIT_HASH_MISMATCH")
    if value.get("decision") == "AUTOMATED_ACCEPTED" and (
        value.get("accepted_scope") != C2_SCOPE or value.get("next_phase_allowed") != C2_ROUTE
    ):
        errors.append("C2_AUTHORIZATION_ACCEPTED_ROUTE_OR_SCOPE_INVALID")
    if any(
        (
            value.get("selected_architecture") is not None,
            value.get("base_selected") is not False,
            value.get("third_party_integrated") is not False,
            value.get("skill_capability_status") != "SCAFFOLD_ONLY",
            value.get("phase003_prohibited") is not True,
        )
    ):
        errors.append("C2_AUTHORIZATION_SCOPE_CREEP")
    return sorted(set(errors))


def check_or_write_authorization_seal(root: Path, *, check: bool) -> dict[str, Any]:
    gate = evaluate_final_audit_gate(root, "SEAL")
    if gate["status"] != "PASS":
        return {**gate, "artifact_created": False}
    value = build_authorization_seal(root)
    errors = _schema_errors(root, AUTHORIZATION_CONTRACT, value, "C2_SEAL_SCHEMA")
    automated = value["automated_decision"]
    errors.extend(
        _schema_errors(root, AUTOMATED_DECISION_CONTRACT, automated, "C2_AUTOMATED_DECISION")
    )
    if not errors:
        errors.extend(check_or_write_json(root / AUTHORIZATION_PATH, value, check=check))
    if not errors:
        errors.extend(validate_authorization_seal(root, _read_json(root / AUTHORIZATION_PATH)))
    return {
        "action": "SEAL",
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "authorization_id": value["authorization_id"],
        "authorization_hash": value["authorization_hash"],
        "decision": value["decision"],
        "accepted_scope": value["accepted_scope"],
        "next_phase_allowed": value["next_phase_allowed"],
        "artifact_created": not check and not errors,
        "artifact_path": AUTHORIZATION_PATH.as_posix(),
    }


__all__ = [
    "AUTHORIZATION_PATH",
    "REPLAY_PATH",
    "build_authorization_seal",
    "check_or_write_authorization_seal",
    "validate_authorization_seal",
]
