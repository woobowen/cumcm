"""State-transition gates and terminal invariants for C2."""

from __future__ import annotations

from copy import deepcopy

from cumcm_skill_lab.authorization_c1.models import sha256_json
from cumcm_skill_lab.authorization_c2.terminal import (
    build_final_project_state,
    build_state_transition,
    validate_authorization_replay,
    validate_final_project_state,
    validate_state_transition,
)


def test_c2_final_state_binds_authorization_audit_and_replay(repo_root):
    state = build_final_project_state(repo_root)
    assert validate_final_project_state(repo_root, state) == []
    shadow = state["shadow_authorization"]
    assert shadow["active_decision_id"] == ("DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C2")
    assert shadow["final_audit_result"] == "PASS"
    assert shadow["final_replay_stable"] is True


def test_c2_final_state_preserves_all_scope_boundaries(repo_root):
    state = build_final_project_state(repo_root)
    assert state["phase"] == "PHASE-EVIDENCE-EXPANSION-002D"
    assert state["status"] == "IN_PROGRESS"
    assert state["selected_architecture"] is None
    assert state["base_selected"] is False
    assert state["third_party_integrated"] is False
    assert state["skill_capability_status"] == "SCAFFOLD_ONLY"
    assert state["next_phase_allowed"] == "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION"


def test_c2_transition_is_sequence_21_and_reproducible(repo_root):
    value = build_state_transition(repo_root)
    assert validate_state_transition(repo_root, value) == []
    assert value["artifact_sequence_index"] == 21
    assert value["full_ci_before_transition"]["status"] == "PASS"
    assert value["full_ci_before_transition"]["failed"] == 0


def test_c2_state_rejects_unstable_replay(repo_root):
    replay = __import__("json").loads(
        (repo_root / "evals/results/phase-002d-r2a-c1/replay/replay-c2.json").read_text()
    )
    replay["stable"] = False
    body = deepcopy(replay)
    body.pop("replay_hash")
    replay["replay_hash"] = sha256_json(body)
    assert "C2_AUTHORIZATION_REPLAY_NOT_STABLE" in validate_authorization_replay(repo_root, replay)


def test_c2_state_rejects_phase003_and_architecture_selection(repo_root):
    state = build_final_project_state(repo_root)
    state["selected_architecture"] = "ARCH-W1-WORKFLOW-ONLY-GUARDS"
    state["next_phase_allowed"] = "PHASE-003"
    errors = validate_final_project_state(repo_root, state)
    assert "C2_FINAL_PROJECT_STATE_SELECTED_ARCHITECTURE_MISMATCH" in errors
    assert "C2_FINAL_PROJECT_STATE_NEXT_PHASE_ALLOWED_MISMATCH" in errors


def test_c2_state_transition_rejects_wrong_replay_parent(repo_root):
    value = build_state_transition(repo_root)
    value["parent_artifact_hash"] = "0" * 64
    body = deepcopy(value)
    body.pop("transition_hash")
    value["transition_hash"] = sha256_json(body)
    assert "C2_STATE_TRANSITION_PARENT_REPLAY_HASH_MISMATCH" in validate_state_transition(
        repo_root, value
    )
