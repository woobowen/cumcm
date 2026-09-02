"""Cross-artifact identity, supersession, replay, and state binding checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import file_sha256, read_json, sha256_json

from .models import FREEZE_PATH

ACTIVE_AUTHORIZATION_ID = "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A"
ACTIVE_AUTHORIZATION_PATH = "evals/results/phase-002d-r2a/authorization_decision/authorization.json"
CANDIDATE_ID = "CANDIDATE-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A"


def build_synthetic_seal(root: Path) -> dict[str, Any]:
    """Build a non-persisted valid seal fixture for mutation and contract tests."""
    freeze = read_json(root / FREEZE_PATH)
    old = freeze["old_shadow_authorization"]
    value: dict[str, Any] = {
        "schema_version": "1.0.0",
        "authorization_id": ACTIVE_AUTHORIZATION_ID,
        "artifact_path": ACTIVE_AUTHORIZATION_PATH,
        "decision": "AUTOMATED_ACCEPTED",
        "accepted_scope": "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY",
        "candidate_id": CANDIDATE_ID,
        "candidate_hash": "1" * 64,
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["manifest_hash"],
        "dependency_graph_hash": "2" * 64,
        "preconditions_hash": "3" * 64,
        "scope_hash": "4" * 64,
        "final_audit_id": "R2A-AUDIT-FINAL-SHADOW-AUTHORIZATION-001",
        "final_audit_result": "PASS",
        "final_audit_checkpoint_hash": "5" * 64,
        "supersedes": {
            "decision_id": old["decision_id"],
            "artifact_path": old["path"],
            "decision_hash": old["decision_hash"],
            "file_sha256": old["file_sha256"],
            "historical_decision": old["decision"],
        },
        "supersession_reason": "POST_AUDIT_AND_REPLAY_CLOSURE",
        "selected_architecture": None,
        "base_selected": False,
        "third_party_integrated": False,
        "restrictions": [
            "NO_ARCHITECTURE_SELECTION",
            "NO_FORMAL_SKILL_INTEGRATION",
            "NO_PHASE_003",
            "NO_MODEL_STAGE2_WITHOUT_NEW_FROZEN_AUTHORIZATION",
        ],
        "next_phase_allowed": "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION",
        "phase003_prohibited": True,
    }
    value["authorization_hash"] = sha256_json(value)
    return value


def validate_supersession_binding(root: Path, value: dict[str, Any]) -> list[str]:
    errors = [
        f"R2A_SEAL_SCHEMA:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(
            read_json(root / "contracts/authorization_seal.schema.json")
        ).iter_errors(value)
    ]
    body = dict(value)
    recorded_hash = body.pop("authorization_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("R2A_SEAL_HASH_MISMATCH")
    freeze = read_json(root / FREEZE_PATH)
    old = freeze["old_shadow_authorization"]
    supersedes = value.get("supersedes", {})
    for field, expected in (
        ("decision_id", old["decision_id"]),
        ("artifact_path", old["path"]),
        ("decision_hash", old["decision_hash"]),
        ("file_sha256", old["file_sha256"]),
        ("historical_decision", old["decision"]),
    ):
        if supersedes.get(field) != expected:
            errors.append(f"R2A_SEAL_SUPERSESSION_{field.upper()}_MISMATCH")
    if value.get("authorization_id") == old["decision_id"]:
        errors.append("R2A_SEAL_REUSES_HISTORICAL_DECISION_ID")
    if value.get("artifact_path") == old["path"]:
        errors.append("R2A_SEAL_OVERWRITES_HISTORICAL_ARTIFACT")
    old_path = root / old["path"]
    if not old_path.is_file() or file_sha256(old_path) != old["file_sha256"]:
        errors.append("R2A_SEAL_HISTORICAL_ARTIFACT_BYTES_CHANGED")
    return sorted(set(errors))


def build_synthetic_replay(root: Path, seal: dict[str, Any]) -> dict[str, Any]:
    freeze = read_json(root / FREEZE_PATH)
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "replay_id": "PHASE-002D-R2A-SHADOW-AUTHORIZATION-REPLAY-001",
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["manifest_hash"],
        "active_decision_id": seal["authorization_id"],
        "active_decision_hash": seal["authorization_hash"],
        "final_audit_checkpoint_hash": seal["final_audit_checkpoint_hash"],
        "stable": True,
        "variant_count": 5,
    }
    body["replay_hash"] = sha256_json(body)
    return body


def validate_replay_binding(root: Path, replay: dict[str, Any], seal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    body = dict(replay)
    recorded_hash = body.pop("replay_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("R2A_REPLAY_HASH_MISMATCH")
    freeze = read_json(root / FREEZE_PATH)
    expected = {
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["manifest_hash"],
        "active_decision_id": seal.get("authorization_id"),
        "active_decision_hash": seal.get("authorization_hash"),
        "final_audit_checkpoint_hash": seal.get("final_audit_checkpoint_hash"),
    }
    for field, expected_value in expected.items():
        if replay.get(field) != expected_value:
            errors.append(f"R2A_REPLAY_{field.upper()}_MISMATCH")
    if replay.get("stable") is not True:
        errors.append("R2A_REPLAY_UNSTABLE")
    if replay.get("variant_count") != 5:
        errors.append("R2A_REPLAY_VARIANT_COUNT_MISMATCH")
    return sorted(set(errors))


def validate_complete_state_bindings(state: dict[str, Any]) -> list[str]:
    """Enforce equal hashes that JSON Schema cannot express across state fields."""
    if state.get("technical_adjudication_status") != "SHADOW_PROTOTYPE_AUTHORIZATION_COMPLETE":
        return []
    binding = state.get("shadow_authorization", {})
    errors: list[str] = []
    if binding.get("replay_input_freeze_hash") != binding.get("input_freeze_hash"):
        errors.append("R2A_STATE_REPLAY_INPUT_FREEZE_MISMATCH")
    if binding.get("replay_decision_hash") != binding.get("active_decision_hash"):
        errors.append("R2A_STATE_REPLAY_DECISION_MISMATCH")
    if binding.get("replay_audit_checkpoint_hash") != binding.get("final_audit_checkpoint_hash"):
        errors.append("R2A_STATE_REPLAY_AUDIT_CHECKPOINT_MISMATCH")
    if binding.get("active_decision_id") not in state.get("automated_decision_ids", []):
        errors.append("R2A_STATE_ACTIVE_DECISION_ID_NOT_REGISTERED")
    return errors


__all__ = [
    "ACTIVE_AUTHORIZATION_ID",
    "ACTIVE_AUTHORIZATION_PATH",
    "CANDIDATE_ID",
    "build_synthetic_replay",
    "build_synthetic_seal",
    "validate_complete_state_bindings",
    "validate_replay_binding",
    "validate_supersession_binding",
]
