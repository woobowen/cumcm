import pytest

from cumcm_skill_lab.specification.authorization.terminal_gates import evaluate_terminal_gate


@pytest.mark.parametrize("action", ["SEAL", "REPLAY", "STATE_TRANSITION"])
def test_terminal_actions_fail_closed_after_retest_required(repo_root, action):
    result = evaluate_terminal_gate(repo_root, action)
    assert result["status"] == "BLOCKED"
    assert result["audit_result"] == "RETEST_REQUIRED"
    assert result["blockers"] == ["R2A-FINAL-002"]
    assert "R2A_FINAL_AUTHORIZATION_AUDIT_NOT_PASS" in result["errors"]
    assert "R2A_FINAL_AUTHORIZATION_AUDIT_BLOCKERS_PRESENT" in result["errors"]
    assert result["artifact_created"] is False
    assert result["formal_state_transition_performed"] is False
    assert result["next_phase_allowed"] is None


def test_unknown_terminal_action_is_rejected(repo_root):
    with pytest.raises(ValueError, match="UNKNOWN_R2A_TERMINAL_ACTION"):
        evaluate_terminal_gate(repo_root, "PHASE_003")
