from copy import deepcopy

from cumcm_skill_lab.failure_aware.evidence_freeze import verify_input_freeze
from cumcm_skill_lab.failure_aware.models import read_json
from cumcm_skill_lab.failure_aware.retry_bias import (
    _cost_reconciliation,
    build_retry_bias_audit,
)


def _attempts_and_cost(repo_root):
    ledger = read_json(repo_root / "evals/results/phase-002d/attempt_ledger.json")
    attempts = [
        read_json(repo_root / f"evals/results/phase-002d/attempts/{attempt_id}.json")
        for attempt_id in ledger["attempt_ids"]
    ]
    cost = read_json(repo_root / "evals/results/phase-002d/cost/cost.json")
    return attempts, cost


def test_all_historical_tree_hashes_replay(repo_root):
    assert verify_input_freeze(repo_root) == []


def test_historical_retry_protocol_deviations_are_explicit(repo_root):
    audit = build_retry_bias_audit(repo_root)
    assert [item["queue_position"] for item in audit["retry_queue_positions"]] == [
        7,
        35,
        37,
        8,
    ]
    assert audit["retry_queue_monotonic"] is False
    assert "RETRY_QUEUE_EXECUTION_ORDER_NON_MONOTONIC" in audit["historical_protocol_deviations"]
    assert audit["retry_after_terminal"] == [
        "EXP-CASE-004-ARM-A-R2-A02",
        "EXP-CASE-006-ARM-A-R1-A02",
    ]


def test_retry_after_terminal_is_retained_as_protocol_deviation(repo_root):
    audit = build_retry_bias_audit(repo_root)
    assert audit["retry_after_terminal"] == [
        "EXP-CASE-004-ARM-A-R2-A02",
        "EXP-CASE-006-ARM-A-R1-A02",
    ]
    assert all(
        not item["allowed_after_predecessor"]
        for item in audit["retry_queue_positions"]
        if item["attempt_id"] in audit["retry_after_terminal"]
    )


def test_cost_reconciliation_checks_exact_totals(repo_root):
    attempts, cost = _attempts_and_cost(repo_root)
    reconciliation = _cost_reconciliation(attempts, cost)
    assert reconciliation["exact_match"] is True
    assert reconciliation["recomputed"] == reconciliation["recorded"]


def test_unknown_costs_remain_unknown(repo_root):
    attempts, cost = _attempts_and_cost(repo_root)
    assert _cost_reconciliation(attempts, cost)["unknown_costs_preserved"] is True


def test_cost_mutation_with_same_attempt_count_fails_closed(repo_root):
    attempts, cost = _attempts_and_cost(repo_root)
    mutated = deepcopy(cost)
    mutated["duration_seconds"] += 1
    reconciliation = _cost_reconciliation(attempts, mutated)
    assert reconciliation["recomputed"]["attempts"] == 28
    assert reconciliation["exact_match"] is False


def test_elapsed_cap_is_checked_before_start_and_stops_after_finish(repo_root):
    boundary = build_retry_bias_audit(repo_root)["elapsed_budget_boundary"]
    assert boundary == {
        "semantics": "START_ADMISSION_CHECK_THEN_STOP_AFTER_COMPLETION",
        "elapsed_before_last_start": 5988.297082,
        "elapsed_after_last_finish": 6228.480778,
        "maximum_total_elapsed_seconds": 6197,
        "last_start_admitted_below_cap": True,
        "stopped_after_cap_reached": True,
    }


def test_original_budget_boundaries_are_unchanged(repo_root):
    budget = read_json(repo_root / "evals/results/phase-002d/budget/frozen_budget.json")
    freeze = read_json(repo_root / "evals/results/phase-002d-r1/input_freeze_manifest.json")
    audit = build_retry_bias_audit(repo_root)
    assert budget["budget_hash"] == freeze["budget_hash"]
    assert audit["posthoc_budget_expansion"] is False
    assert audit["per_cell_cap_respected"] is True
