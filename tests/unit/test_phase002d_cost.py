from copy import deepcopy

from cumcm_skill_lab.expansion.cost import build_cost, validate_cost
from cumcm_skill_lab.expansion.models import read_json


def _batch_one(repo_root):
    return read_json(repo_root / "evals/results/phase-002d/cost/batches/batch-001.json")


def test_batch_one_cost_is_truthful_and_contract_valid(repo_root):
    cost = _batch_one(repo_root)
    assert validate_cost(repo_root, cost) == []
    assert cost["attempts"] == 3
    assert cost["successful_primary_records"] == 3
    assert cost["failed_attempts"] == 0
    assert cost["oracle_passes"] == 1
    assert cost["oracle_failures"] == 2


def test_observable_tokens_sum_exactly(repo_root):
    cost = _batch_one(repo_root)
    assert cost["tokens"]["input_tokens"] == {
        "status": "OBSERVED",
        "total": 532989,
        "average_per_record": 177663,
        "observed_records": 3,
        "total_records": 3,
    }
    assert cost["tokens"]["output_tokens"]["total"] == 27845


def test_unobservable_tokens_remain_unknown_not_zero(repo_root):
    cost = _batch_one(repo_root)
    for field in ("cached_input_tokens", "reasoning_tokens"):
        assert cost["tokens"][field]["status"] == "UNKNOWN"
        assert cost["tokens"][field]["total"] == "UNKNOWN"
        assert cost["tokens"][field]["average_per_record"] == "UNKNOWN"
    assert cost["unknown_checkpoint_token_totals_not_treated_as_zero"] is True


def test_cost_keeps_oracle_outcomes_separate_from_primary_eligibility(repo_root):
    cost = _batch_one(repo_root)
    assert cost["successful_primary_records"] == 3
    assert cost["oracle_passes"] == 1
    assert sum(arm["primary_eligible"] for arm in cost["average_run_cost_by_arm"].values()) == 3
    assert sum(arm["oracle_passes"] for arm in cost["average_run_cost_by_arm"].values()) == 1


def test_batch_one_has_one_balanced_case_but_no_complete_repeat_depth(repo_root):
    cost = _batch_one(repo_root)
    assert list(cost["marginal_balanced_case_costs"]) == ["CASE-001"]
    assert cost["independent_repeat_marginal_cost"] == {
        "status": "NOT_YET_OBSERVED",
        "cases": [],
    }


def test_cost_does_not_infer_currency_or_api_billing(repo_root):
    cost = _batch_one(repo_root)
    assert cost["monetary_cost"] == "UNKNOWN"
    assert cost["api_key_used"] is False
    assert cost["api_billing_used"] is False
    assert cost["correctness_and_hard_gates_dominate_cost"] is True


def test_cost_hash_mutation_fails_closed(repo_root):
    cost = _batch_one(repo_root)
    mutated = deepcopy(cost)
    mutated["cost_hash"] = "0" * 64
    assert "COST_HASH_MISMATCH" in validate_cost(repo_root, mutated)


def test_maintenance_surface_is_explicit(repo_root):
    cost = _batch_one(repo_root)
    surface = cost["maintenance_surface"]
    assert surface["tracked_file_count"] == len(surface["paths"])
    assert surface["lines_of_code"] > 0
    assert "src/cumcm_skill_lab/expansion/runner.py" in surface["paths"]


def test_current_cost_rebuilds_from_all_append_only_attempts(repo_root):
    current = read_json(repo_root / "evals/results/phase-002d/cost/cost.json")
    rebuilt = build_cost(
        repo_root,
        batch_id=current["batch_id"],
        calculated_at=current["calculated_at"],
    )
    assert rebuilt == current
