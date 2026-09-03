from __future__ import annotations

from cumcm_skill_lab.shadow_validation.competition_gate import (
    ARCHITECTURE_ORDER,
    GATE_IDS,
    evaluate_competition_gate,
)


def test_frozen_competition_gate_blocks_when_neither_candidate_passes_all_gates(
    repo_root,
) -> None:
    result = evaluate_competition_gate(repo_root)
    assert result["selection_rule"][0].startswith("If K1 passes all eight gates")
    assert result["selected_architecture"] is None
    assert result["decision"] == "FAST_TRACK_IMPLEMENTATION_BLOCKED"
    assert result["real_model_starts"] == 0
    assert result["hidden_benchmark_accesses"] == 0
    assert result["third_party_executions"] == 0
    assert result["majority_vote_used"] is False


def test_both_implementations_have_explicit_results_for_all_eight_gates(repo_root) -> None:
    result = evaluate_competition_gate(repo_root)
    for architecture_id in ARCHITECTURE_ORDER:
        architecture = result["architecture_results"][architecture_id]
        assert tuple(architecture["gates"]) == GATE_IDS
        assert architecture["all_gates_pass"] is False
        assert "FAIL" in {item["status"] for item in architecture["gates"].values()}
        assert all(item["evidence"] for item in architecture["gates"].values())
        assert all(
            item["reason_codes"]
            for item in architecture["gates"].values()
            if item["status"] == "FAIL"
        )


def test_gate_exposes_candidate_specific_blockers_and_is_deterministic(repo_root) -> None:
    first = evaluate_competition_gate(repo_root)
    second = evaluate_competition_gate(repo_root)
    assert first == second
    assert first["decision_hash"] == second["decision_hash"]
    k1 = first["architecture_results"][ARCHITECTURE_ORDER[0]]["gates"]
    w1 = first["architecture_results"][ARCHITECTURE_ORDER[1]]["gates"]
    assert "K1_COMPOSITION_RUN_BINDING_MISMATCH" in k1[GATE_IDS[7]]["reason_codes"]
    assert "K1_COMPOSITION_STALE_PROPAGATION_REQUIRED" in k1[GATE_IDS[7]]["reason_codes"]
    assert "CANDIDATE_COMPOSER_ABSENT" in w1[GATE_IDS[7]]["reason_codes"]
    assert "FAILED_ATTEMPT_SCORED:NOT_REJECTED" in w1[GATE_IDS[4]]["reason_codes"]
