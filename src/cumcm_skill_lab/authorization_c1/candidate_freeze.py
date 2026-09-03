"""Generate and byte-freeze the immutable C1 authorization candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    INPUT_FREEZE_PATH,
    RESULT_ROOT,
    check_or_write_json,
    file_sha256,
    sha256_json,
)

CANDIDATE_ID = "CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C1"
DECISION_ID = "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C1"
OLD_CANDIDATE_ID = "CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A"
OLD_DECISION_ID = "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2"
CANDIDATE_PATH = RESULT_ROOT / "candidate_revision/candidate-c1.json"
FREEZE_PATH = RESULT_ROOT / "candidate_freeze/candidate_freeze_manifest-c1.json"
COMPATIBILITY_CLOSURE_PATH = RESULT_ROOT / "compatibility_tests/closure.json"
CREATION_COMMIT = "de16bfe71cc172a7e27434eb9b6a0d61b3ef00d9"
CANONICALIZATION_VERSION = "C1-CANONICAL-JSON-1.0.0"
RESERVED_SELF_HASH_FIELDS = frozenset(
    {
        "candidate_hash",
        "candidate_file_sha256",
        "canonical_candidate_hash",
        "candidate_freeze_hash",
        "freeze_hash",
    }
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_candidate_hash(value: dict[str, Any]) -> str:
    """Hash every semantic field; arrays keep order and unknown fields are retained."""
    present = sorted(RESERVED_SELF_HASH_FIELDS.intersection(value))
    if present:
        raise ValueError(f"C1_CANDIDATE_SELF_HASH_FIELD_PROHIBITED:{present[0]}")
    return sha256_json(value)


def _decision_from_prerequisites(root: Path) -> str:
    history = _read_json(root / RESULT_ROOT / "historical_verification/record.json")
    schema = _read_json(root / RESULT_ROOT / "schema_resolution/record.json")
    compatibility = _read_json(root / COMPATIBILITY_CLOSURE_PATH)
    old_preconditions = _read_json(
        root / "evals/results/phase-002d-r2a/authorization_preconditions.json"
    )
    r2_audit = _read_json(root / "evals/results/phase-002d-r2/decision_audit/audit.json")
    r2_replay = _read_json(root / "evals/results/phase-002d-r2/replay/replay.json")
    gates = (
        history["result"] == "PASS",
        schema["result"] == "PASS",
        compatibility["result"] == "PASS",
        not compatibility["unresolved_compatibility_blockers"],
        old_preconditions["all_required_pass"] is True,
        r2_audit["result"] == "PASS",
        r2_replay["stable"] is True,
    )
    return "AUTOMATED_ACCEPTED" if all(gates) else "RETEST_REQUIRED"


def build_candidate(root: Path) -> dict[str, Any]:
    freeze = _read_json(root / INPUT_FREEZE_PATH)
    history = _read_json(root / RESULT_ROOT / "historical_verification/record.json")
    schema = _read_json(root / RESULT_ROOT / "schema_resolution/record.json")
    compatibility = _read_json(root / COMPATIBILITY_CLOSURE_PATH)
    old_preconditions = _read_json(
        root / "evals/results/phase-002d-r2a/authorization_preconditions.json"
    )
    old_graph = _read_json(
        root / "evals/results/phase-002d-r2a/authorization_dependency_graph.json"
    )
    old_candidate = _read_json(
        root / "evals/results/phase-002d-r2a/authorization_candidate/candidate.json"
    )
    decision = _decision_from_prerequisites(root)
    accepted = decision == "AUTOMATED_ACCEPTED"
    return {
        "schema_version": "1.0.0",
        "record_type": "SHADOW_AUTHORIZATION_CANDIDATE_NOT_ACTIVE",
        "candidate_id": CANDIDATE_ID,
        "revision": "C1",
        "active": False,
        "proposed_authorization_id": DECISION_ID,
        "decision": decision,
        "accepted_scope": "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY" if accepted else None,
        "next_phase_allowed": ("PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION" if accepted else None),
        "input_references": {
            "c1_input_freeze_hash": freeze["manifest_hash"],
            "historical_compatibility_hash": history["record_hash"],
            "schema_resolution_hash": schema["record_hash"],
            "compatibility_closure_hash": compatibility["closure_hash"],
            "r2a_dependency_graph_hash": old_graph["graph_hash"],
            "r2a_scope_hash": old_candidate["scope_hash"],
            "r2a_historical_preconditions_hash": old_preconditions["preconditions_hash"],
            "formal_skill_tree_hash": freeze["protected_bindings"]["formal_skill_tree_hash"],
            "benchmark_hash": freeze["protected_bindings"]["benchmark_hash"],
            "threshold_hash": freeze["protected_bindings"]["threshold_hash"],
            "protocol_hash": freeze["protected_bindings"]["protocol_hash"],
            "implementation_embargo_hash": freeze["protected_bindings"][
                "implementation_embargo_hash"
            ],
        },
        "supersedes": {
            "decision_id": OLD_DECISION_ID,
            "decision_hash": "795166071e24497abf27f2be807b006bfa89660ad3d7d99b18c0631f1c304e1d",
            "historical_decision": "RETEST_REQUIRED",
        },
        "replaces_non_active_candidate": {
            "candidate_id": OLD_CANDIDATE_ID,
            "candidate_file_sha256": freeze["old_candidate"]["file_sha256"],
            "canonical_candidate_hash": freeze["old_candidate"]["canonical_candidate_hash"],
            "classification": "HISTORICAL_NON_ACTIVE_CANDIDATE",
        },
        "restrictions": [
            "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY",
            "NO_ARCHITECTURE_SELECTION",
            "NO_FORMAL_SKILL_WRITE",
            "NO_FORMAL_INTEGRATION",
            "NO_HIDDEN_VAULT_ACCESS",
            "NO_THIRD_PARTY_CODE_OR_EXECUTION",
            "NO_MODEL_STAGE2_WITHOUT_NEW_FROZEN_AUTHORIZATION",
            "NO_PHASE_003",
        ],
        "selected_architecture": None,
        "base_selected": False,
        "third_party_integrated": False,
        "skill_capability_status": "SCAFFOLD_ONLY",
        "phase003_prohibited": True,
        "prototype_implemented": False,
        "prototype_executed": False,
        "real_model_in_loop_runs": 0,
        "api_calls": 0,
        "third_party_executions": 0,
        "majority_vote_used": False,
        "unknowns": [
            "CLEAN_ROOM_LEGAL_COMPLIANCE_NOT_PROVEN",
            "HIDDEN_VAULT_OS_ISOLATION_NOT_VERIFIED",
            "PROTOTYPE_EFFECTIVENESS_UNMEASURED",
            "MONETARY_COST_UNKNOWN",
        ],
    }


def validate_candidate(root: Path, value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        canonical_candidate_hash(value)
    except ValueError as exc:
        errors.append(str(exc))
    expected = build_candidate(root)
    if value != expected:
        errors.append("C1_CANDIDATE_SEMANTIC_PAYLOAD_MISMATCH")
    if value.get("candidate_id") != CANDIDATE_ID:
        errors.append("C1_CANDIDATE_ID_MISMATCH")
    if value.get("active") is not False:
        errors.append("C1_CANDIDATE_PREMATURELY_ACTIVE")
    if value.get("selected_architecture") is not None:
        errors.append("C1_CANDIDATE_ARCHITECTURE_SELECTION_PROHIBITED")
    if value.get("base_selected") is not False or value.get("third_party_integrated") is not False:
        errors.append("C1_CANDIDATE_FORMAL_INTEGRATION_PROHIBITED")
    return sorted(set(errors))


def build_candidate_freeze(root: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    input_freeze = _read_json(root / INPUT_FREEZE_PATH)
    compatibility = _read_json(root / COMPATIBILITY_CLOSURE_PATH)
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "freeze_id": "PHASE-002D-R2A-C1-CANDIDATE-FREEZE-001",
        "candidate_id": CANDIDATE_ID,
        "candidate_path": CANDIDATE_PATH.as_posix(),
        "candidate_file_sha256": file_sha256(root / CANDIDATE_PATH),
        "canonical_candidate_hash": canonical_candidate_hash(candidate),
        "canonicalization_version": CANONICALIZATION_VERSION,
        "canonicalization": {
            "encoding": "UTF-8",
            "object_keys": "SORTED",
            "separators": [",", ":"],
            "array_order": "PRESERVED",
            "unknown_fields": "INCLUDED",
            "reserved_self_hash_fields": sorted(RESERVED_SELF_HASH_FIELDS),
            "timestamps": "NOT_PRESENT_IN_CANDIDATE",
        },
        "source_input_freeze_hash": input_freeze["manifest_hash"],
        "dependency_graph_hash": candidate["input_references"]["r2a_dependency_graph_hash"],
        "scope_hash": candidate["input_references"]["r2a_scope_hash"],
        "creation_commit": CREATION_COMMIT,
        "artifact_sequence_index": 4,
        "parent_artifact_hash": compatibility["closure_hash"],
        "candidate_immutable_after_freeze": True,
    }
    body["freeze_hash"] = sha256_json(body)
    return body


def validate_candidate_freeze(root: Path, value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    candidate_path = root / CANDIDATE_PATH
    if not candidate_path.is_file():
        return ["C1_CANDIDATE_FILE_MISSING"]
    candidate = _read_json(candidate_path)
    errors.extend(validate_candidate(root, candidate))
    body = dict(value)
    recorded = body.pop("freeze_hash", None)
    if sha256_json(body) != recorded:
        errors.append("C1_CANDIDATE_FREEZE_HASH_MISMATCH")
    if value.get("candidate_file_sha256") != file_sha256(candidate_path):
        errors.append("C1_CANDIDATE_FILE_SHA256_MISMATCH")
    try:
        canonical = canonical_candidate_hash(candidate)
    except ValueError as exc:
        errors.append(str(exc))
        canonical = None
    if value.get("canonical_candidate_hash") != canonical:
        errors.append("C1_CANDIDATE_CANONICAL_HASH_MISMATCH")
    expected = build_candidate_freeze(root, candidate)
    if value != expected:
        errors.append("C1_CANDIDATE_FREEZE_CONTENT_MISMATCH")
    return sorted(set(errors))


def check_or_write_candidate_freeze(root: Path, *, check: bool) -> dict[str, Any]:
    candidate = build_candidate(root)
    errors = check_or_write_json(root / CANDIDATE_PATH, candidate, check=check)
    if not errors:
        errors.extend(validate_candidate(root, _read_json(root / CANDIDATE_PATH)))
        manifest = build_candidate_freeze(root, candidate)
        errors.extend(check_or_write_json(root / FREEZE_PATH, manifest, check=check))
        if not errors:
            errors.extend(validate_candidate_freeze(root, _read_json(root / FREEZE_PATH)))
    else:
        manifest = None
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "candidate_id": CANDIDATE_ID,
        "candidate_file_sha256": manifest["candidate_file_sha256"] if manifest else None,
        "canonical_candidate_hash": manifest["canonical_candidate_hash"] if manifest else None,
        "freeze_hash": manifest["freeze_hash"] if manifest else None,
        "decision": candidate["decision"],
    }


__all__ = [
    "CANDIDATE_ID",
    "CANDIDATE_PATH",
    "FREEZE_PATH",
    "RESERVED_SELF_HASH_FIELDS",
    "build_candidate",
    "build_candidate_freeze",
    "canonical_candidate_hash",
    "check_or_write_candidate_freeze",
    "validate_candidate",
    "validate_candidate_freeze",
]
