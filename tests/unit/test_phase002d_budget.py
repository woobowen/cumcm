from copy import deepcopy
from pathlib import Path

import pytest

from cumcm_skill_lab.expansion.budget import (
    build_budget,
    historical_metrics,
    validate_budget,
)


@pytest.fixture
def root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_historical_metrics_are_observed_not_assumed(root: Path):
    metrics = historical_metrics(root)
    assert metrics["attempts"] == 20
    assert metrics["successful_primary_records"] == 13
    assert metrics["observed_success_rate"] == pytest.approx(0.65)


def test_mode_b_budget_formula_and_absolute_caps(root: Path):
    budget = build_budget(root)
    assert budget["target_successes"] == 24
    assert budget["formula_values"]["base_attempts"] == 37
    assert budget["maximum_total_attempts"] == 40
    assert budget["absolute_attempt_cap"] == 48
    assert budget["maximum_attempts_per_cell"] == 3
    assert budget["concurrency"] == 1
    assert budget["monetary_cost"] == "UNKNOWN"
    assert validate_budget(root, budget) == []


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("maximum_total_attempts", 49, "ATTEMPT_CAP_EXCEEDED"),
        ("concurrency", 2, "UNPROVEN_CONCURRENCY"),
        ("budget_hash", "0" * 64, "BUDGET_HASH_MISMATCH"),
    ],
)
def test_budget_faults_fail_closed(root: Path, field: str, value: object, expected: str):
    budget = build_budget(root)
    mutated = deepcopy(budget)
    mutated[field] = value
    assert expected in validate_budget(root, mutated)


@pytest.mark.parametrize("field", ["api_key_used", "api_billing_used"])
def test_api_cost_paths_are_forbidden(root: Path, field: str):
    budget = build_budget(root)
    assert budget[field] is False


def test_budget_cannot_expand_after_results(root: Path):
    assert build_budget(root)["budget_may_expand_after_results"] is False
