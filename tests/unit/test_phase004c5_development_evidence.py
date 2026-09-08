"""Neutral evidence-semantics cases for Development versus Final evaluation access."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture
def case_cli(repo_root: Path):
    path = repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
    spec = importlib.util.spec_from_file_location("cumcm_case_phase004c5_evidence", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def development_route(repo_root: Path):
    path = repo_root / "scripts/run_c_target_rc7_development_regressions.py"
    spec = importlib.util.spec_from_file_location("phase004c5_development_route", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _comparison(case_cli) -> tuple[dict, dict]:
    candidates = ["BASE", "CAND"]
    metric = "MAE"
    direction = "MIN"
    aggregation_rule = "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID"
    selection_rule = "ARGMIN_THEN_ID"
    seeds = [7]
    splits = {"train": [1], "validation": [2], "test": [3]}
    required_inputs = {"data/raw/input.csv": "a" * 64}
    required_code_files = [
        {
            "scope": "SKILL_ROOT",
            "path": "scripts/cumcm_case.py",
            "repository_path": ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
            "sha256": "b" * 64,
        }
    ]
    code_commit = "c" * 40
    stop_rule = "one preregistered Development attempt per candidate"
    handoff_generated_at = "2026-09-08T02:00:00Z"
    freezes = {
        "candidate_set": case_cli.canonical_hash(candidates),
        "metric": case_cli.canonical_hash(
            {
                "name": metric,
                "direction": direction,
                "aggregation_rule": aggregation_rule,
                "selection_rule": selection_rule,
            }
        ),
        "seed_schedule": case_cli.canonical_hash(seeds),
        "split_assignment": case_cli.canonical_hash(splits),
        "baseline": case_cli.canonical_hash("BASE"),
        "input_set": case_cli.canonical_hash(required_inputs),
        "execution_policy": case_cli.canonical_hash(
            {"stop_rule": stop_rule, "handoff_generated_at": handoff_generated_at}
        ),
        "code_set": case_cli.canonical_hash(required_code_files),
        "code_commit": case_cli.canonical_hash(code_commit),
    }
    comparison = {
        "candidate_ids": candidates,
        "baseline_id": "BASE",
        "splits": splits,
        "metric": metric,
        "metric_direction": direction,
        "random_seeds": seeds,
        "attempts": [
            {
                "candidate_id": "BASE",
                "run_id": "RUN-BASE",
                "random_seed": 7,
                "outcome": "SUCCESS",
                "validation_score": 2.0,
            },
            {
                "candidate_id": "CAND",
                "run_id": "RUN-CAND",
                "random_seed": 7,
                "outcome": "SUCCESS",
                "validation_score": 1.0,
            },
        ],
        "selected_candidate_id": "CAND",
        "selection_decision_hash": case_cli.canonical_hash(
            {
                "selected_candidate_id": "CAND",
                "validation_scores": {"BASE": 2.0, "CAND": 1.0},
                "metric": metric,
                "rule": selection_rule,
                "aggregation_rule": aggregation_rule,
            }
        ),
        "freeze_bindings": freezes,
        "leakage_checks": {
            "test_used_for_candidate_generation": False,
            "test_used_for_feature_selection": False,
            "test_used_for_threshold_selection": False,
            "future_information": False,
            "group_overlap": False,
            "target_in_features": False,
            "time_order_valid": True,
        },
        "reliability": {"attempts": 2, "successful": 2, "failed_or_infeasible": 0},
        "required_input_hashes": required_inputs,
        "required_code_files": required_code_files,
        "code_commit": code_commit,
        "aggregation_rule": aggregation_rule,
        "selection_rule": selection_rule,
        "stop_rule": stop_rule,
        "handoff_generated_at": handoff_generated_at,
    }
    return comparison, freezes


def test_development_without_final_evaluation_has_explicit_zero_access(
    case_cli, tmp_path: Path
) -> None:
    comparison, freezes = _comparison(case_cli)
    comparison["test_access"] = {
        "mode": "DEVELOPMENT_NO_FINAL_EVALUATION",
        "authorized": False,
        "count": 0,
        "used_for_selection": False,
        "evaluator_invoked": False,
        "ledger_status": "NOT_ACCESSED",
    }

    result = case_cli.validate_comparison(comparison, freezes)

    assert result.accepted is True, result.as_dict()


def test_development_count_one_without_real_evaluator_is_rejected(case_cli, tmp_path: Path) -> None:
    comparison, freezes = _comparison(case_cli)
    comparison["test_access"] = {
        "mode": "DEVELOPMENT_NO_FINAL_EVALUATION",
        "authorized": False,
        "count": 1,
        "used_for_selection": False,
        "evaluator_invoked": False,
        "ledger_status": "NOT_ACCESSED",
    }

    result = case_cli.validate_comparison(comparison, freezes)

    assert result.accepted is False
    assert "RC_DEVELOPMENT_TEST_ACCESS_COUNT_INVALID" in result.reason_codes


def test_implicit_or_formal_zero_access_cannot_default_to_pass(case_cli, tmp_path: Path) -> None:
    comparison, freezes = _comparison(case_cli)
    comparison["test_access"] = {
        "authorized": False,
        "count": 0,
        "used_for_selection": False,
    }

    result = case_cli.validate_comparison(comparison, freezes)

    assert result.accepted is False
    assert "RC_COMPARISON_UNAUTHORIZED_TEST_ACCESS" in result.reason_codes


def test_existing_comparison_is_not_mutated_by_development_validation(
    case_cli, tmp_path: Path
) -> None:
    comparison, freezes = _comparison(case_cli)
    original = copy.deepcopy(comparison)
    case_cli.validate_comparison(comparison, freezes)
    assert comparison == original


def test_development_claim_semantics_are_explicit_and_not_all_descriptive(
    development_route,
) -> None:
    for config in development_route.CASES.values():
        specs = development_route.CLAIM_SEMANTIC_SPECS[config.key]
        assert set(specs) == set(config.requirement_ids)
        assert all(
            item.get("claim_type") in development_route.SEMANTIC_CLAIM_TYPES
            for item in specs.values()
        )
        assert any(item.get("claim_type") != "DESCRIPTIVE" for item in specs.values())
        assert all(item.get("claim_type") != "PREDICTIVE" for item in specs.values())
