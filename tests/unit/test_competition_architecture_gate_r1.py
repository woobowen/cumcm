from __future__ import annotations

from cumcm_skill_lab.shadow_validation.competition_gate import GATE_IDS, K1, W1
from cumcm_skill_lab.shadow_validation.competition_gate_r1 import (
    DECISION_ID,
    evaluate_competition_gate_r1,
)


def test_r1_gate_preserves_policy_and_selects_by_frozen_order(repo_root) -> None:
    result = evaluate_competition_gate_r1(repo_root)

    assert result["decision_id"] == DECISION_ID
    assert result["preserves_old_decision_id"] == "DECISION-COMPETITION-MVP-ARCHITECTURE-003F"
    assert result["selection_rule"][0].startswith("If K1 passes all eight gates")
    assert tuple(result["architecture_results"]) == (K1, W1)
    assert result["selected_architecture"] in {K1, W1}
    assert result["real_model_starts"] == 0
    assert result["hidden_benchmark_accesses"] == 0
    assert result["third_party_executions"] == 0
    assert result["majority_vote_used"] is False


def test_r1_gate_records_complete_noncompensatory_case_evidence(repo_root) -> None:
    result = evaluate_competition_gate_r1(repo_root)
    for architecture in result["architecture_results"].values():
        assert tuple(architecture["gates"]) == GATE_IDS
        for gate in architecture["gates"].values():
            assert gate["case_count"] == len(gate["cases"])
            assert gate["input_immutability"] is True
            assert gate["unhandled_exceptions"] == 0
            assert len(gate["output_hash"]) == 64


def test_k1_reaches_eight_of_eight_and_is_selected_first(repo_root) -> None:
    first = evaluate_competition_gate_r1(repo_root)
    second = evaluate_competition_gate_r1(repo_root)

    assert first == second
    assert first["decision_hash"] == second["decision_hash"]
    assert first["architecture_results"][K1]["all_gates_pass"] is True
    assert all(
        gate["status"] == "PASS" for gate in first["architecture_results"][K1]["gates"].values()
    )
    assert first["selected_architecture"] == K1
