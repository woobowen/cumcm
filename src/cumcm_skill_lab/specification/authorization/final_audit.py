"""Prepare the frozen, allowlisted input bundle for the final R2A auditor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    file_sha256,
    read_json,
    sha256_json,
)

from .adversarial_closure import CLOSURE_PATH, EVIDENCE_PATH, REQUESTS_PATH
from .candidate import CANDIDATE_PATH, build_authorization_candidate
from .models import DEPENDENCY_PATH, FREEZE_PATH, RESULT_ROOT
from .native_audits import (
    FINAL_ROLE,
    FIRST_ROUND_ROLES,
    INPUT_ROOT,
    OUTPUT_ROOT,
)
from .preconditions import PRECONDITIONS_PATH
from .scope import SCOPE_PATH

CREATED_AT = "2026-09-03T05:20:00+08:00"
STATE_PROPOSAL_PATH = RESULT_ROOT / "authorization_candidate/state_proposal.json"
REPLAY_INPUTS_PATH = RESULT_ROOT / "authorization_candidate/replay_inputs.json"
FINAL_BUNDLE_PATH = INPUT_ROOT / f"{FINAL_ROLE}.json"

FINAL_ALLOWED_PATHS = (
    FREEZE_PATH.as_posix(),
    DEPENDENCY_PATH.as_posix(),
    PRECONDITIONS_PATH.as_posix(),
    SCOPE_PATH.as_posix(),
    CLOSURE_PATH.as_posix(),
    REQUESTS_PATH.as_posix(),
    EVIDENCE_PATH.as_posix(),
    CANDIDATE_PATH.as_posix(),
    STATE_PROPOSAL_PATH.as_posix(),
    REPLAY_INPUTS_PATH.as_posix(),
    *((OUTPUT_ROOT / f"{role}.json").as_posix() for role in FIRST_ROUND_ROLES),
    "evals/results/phase-002d-r2/automated_decisions/shadow_prototype_authorization.json",
    "evals/results/phase-002d-r2/decision_audit/audit.json",
    "evals/results/phase-002d-r2/replay/replay.json",
    "evals/results/phase-002d-r2/implementation_embargo.json",
    "evals/prospective/phase-002d-r2/sealed_manifest.json",
    "evals/prospective/phase-002d-r2/manifests/candidate_visible_manifest.json",
    "evals/prospective/phase-002d-r2/access_policy.yaml",
    "evals/prospective/phase-002d-r2/threshold_policy.yaml",
    "evals/prospective/phase-002d-r2/prospective_experiment_protocol.yaml",
    "contracts/automated_decision.schema.json",
    "contracts/authorization_seal.schema.json",
    "contracts/project_state.schema.json",
    "contracts/subagent_audit.schema.json",
    "rules/phase002d_r2a_workflow_rules.yaml",
    "state/project_state.json",
)


def _hashed(value: dict[str, Any], field: str) -> dict[str, Any]:
    body = dict(value)
    body[field] = sha256_json(body)
    return body


def build_state_proposal(root: Path) -> dict[str, Any]:
    """Build a non-active transition proposal; never mutate formal state here."""
    state = read_json(root / "state/project_state.json")
    candidate = build_authorization_candidate(root)
    accepted = candidate["proposed_automated_decision"]["decision"] == "AUTOMATED_ACCEPTED"
    return _hashed(
        {
            "schema_version": "1.0.0",
            "proposal_id": "PHASE-002D-R2A-FORMAL-STATE-PROPOSAL-001",
            "created_at": CREATED_AT,
            "active": False,
            "current_state_path": "state/project_state.json",
            "current_state_file_sha256": file_sha256(root / "state/project_state.json"),
            "candidate_id": candidate["candidate_id"],
            "candidate_hash": candidate["candidate_hash"],
            "proposed_transition": {
                "technical_adjudication_status": (
                    "SHADOW_PROTOTYPE_AUTHORIZATION_COMPLETE"
                    if accepted
                    else "SHADOW_PROTOTYPE_AUTHORIZATION_INCOMPLETE"
                ),
                "decision_id_to_append": candidate["proposed_authorization_id"],
                "next_phase_allowed": candidate["proposed_next_phase_allowed"],
                "selected_architecture": None,
                "base_selected": False,
                "third_party_integrated": False,
                "skill_capability_status": "SCAFFOLD_ONLY",
                "phase003_prohibited": True,
            },
            "pending_hard_gates": {
                "final_authorization_auditor": "PENDING",
                "active_authorization_seal": "NOT_CREATED",
                "final_replay": "NOT_RUN",
            },
            "formal_state_transition_performed": False,
            "current_technical_adjudication_status": state["technical_adjudication_status"],
            "current_next_phase_allowed": state["next_phase_allowed"],
        },
        "proposal_hash",
    )


def build_replay_inputs(root: Path) -> dict[str, Any]:
    """Freeze candidate-era replay inputs without claiming a replay result."""
    candidate = build_authorization_candidate(root)
    freeze = read_json(root / FREEZE_PATH)
    graph = read_json(root / DEPENDENCY_PATH)
    preconditions = read_json(root / PRECONDITIONS_PATH)
    closure = read_json(root / CLOSURE_PATH)
    return _hashed(
        {
            "schema_version": "1.0.0",
            "replay_input_id": "PHASE-002D-R2A-AUTHORIZATION-REPLAY-INPUTS-001",
            "created_at": CREATED_AT,
            "input_freeze_id": freeze["freeze_id"],
            "input_freeze_hash": freeze["manifest_hash"],
            "dependency_graph_hash": graph["graph_hash"],
            "preconditions_hash": preconditions["preconditions_hash"],
            "finding_closure_hash": closure["closure_hash"],
            "candidate_id": candidate["candidate_id"],
            "candidate_hash": candidate["candidate_hash"],
            "candidate_decision": candidate["proposed_automated_decision"]["decision"],
            "final_audit_id": "R2A-AUDIT-FINAL-SHADOW-AUTHORIZATION-001",
            "final_audit_status": "PENDING",
            "active_decision_available": False,
            "permutation_plan": [
                "EVIDENCE_ORDER_REVERSED",
                "DECISION_INPUT_ORDER_REVERSED",
                "TARGET_LABELS_PERMUTED",
            ],
            "required_invariants": [
                "DECISION_STABLE",
                "ACCEPTED_SCOPE_STABLE",
                "NEXT_ROUTE_STABLE",
                "NO_ARCHITECTURE_SELECTION",
                "NO_PHASE_003",
                "EXACT_INPUT_AUDIT_DECISION_BINDINGS",
            ],
            "replay_performed": False,
        },
        "replay_inputs_hash",
    )


def build_final_audit_bundle(root: Path) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "bundle_id": "PHASE-002D-R2A-FINAL-SHADOW-AUTHORIZATION-AUDITOR-003",
        "role": FINAL_ROLE,
        "round": "POST_DECISION",
        "created_at": CREATED_AT,
        "allowed_paths": list(FINAL_ALLOWED_PATHS),
        "path_hashes": {path: file_sha256(root / path) for path in FINAL_ALLOWED_PATHS},
        "review_requirements": [
            "DEPENDENCY_CYCLE",
            "HISTORY_MUTATION",
            "UNRESOLVED_BLOCKER",
            "SCOPE_CREEP",
            "HIDDEN_VAULT_LEAKAGE",
            "IMPLEMENTATION_LEAKAGE",
            "ARCHITECTURE_SELECTION",
            "PHASE_003_LEAKAGE",
            "THRESHOLD_MUTATION",
            "BENCHMARK_MUTATION",
            "MAJORITY_VOTING",
            "HARDCODING",
            "SUPERSESSION",
            "NEXT_ROUTE",
            "REPLAYABILITY",
        ],
        "constraints": {
            "read_only": True,
            "peer_output_access": "FROZEN_PREDECESSORS_ONLY",
            "writes_allowed": False,
            "nested_codex_allowed": False,
            "web_allowed": False,
            "mcp_allowed": False,
            "api_allowed": False,
            "majority_vote_allowed": False,
            "expected_conclusion_visible": False,
            "abstention_allowed": True,
            "fabricated_evidence_allowed": False,
        },
    }
    body["bundle_hash"] = sha256_json(body)
    return body


def check_or_write_final_audit_inputs(root: Path, *, check: bool) -> dict[str, Any]:
    errors: list[str] = []
    state_proposal = build_state_proposal(root)
    replay_inputs = build_replay_inputs(root)
    errors.extend(check_or_write(root / STATE_PROPOSAL_PATH, state_proposal, check=check))
    errors.extend(check_or_write(root / REPLAY_INPUTS_PATH, replay_inputs, check=check))
    bundle = build_final_audit_bundle(root)
    errors.extend(check_or_write(root / FINAL_BUNDLE_PATH, bundle, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "bundle_id": bundle["bundle_id"],
        "bundle_hash": bundle["bundle_hash"],
        "allowed_path_count": len(bundle["allowed_paths"]),
        "state_proposal_hash": state_proposal["proposal_hash"],
        "replay_inputs_hash": replay_inputs["replay_inputs_hash"],
    }


def recorded_final_audit_bundle(root: Path) -> dict[str, Any]:
    bundle = read_json(root / FINAL_BUNDLE_PATH)
    body = dict(bundle)
    recorded = body.pop("bundle_hash", None)
    if sha256_json(body) != recorded:
        raise ValueError("R2A_RECORDED_FINAL_AUDIT_BUNDLE_HASH_MISMATCH")
    return bundle


__all__ = [
    "FINAL_ALLOWED_PATHS",
    "FINAL_BUNDLE_PATH",
    "REPLAY_INPUTS_PATH",
    "STATE_PROPOSAL_PATH",
    "build_final_audit_bundle",
    "build_replay_inputs",
    "build_state_proposal",
    "check_or_write_final_audit_inputs",
    "recorded_final_audit_bundle",
]
