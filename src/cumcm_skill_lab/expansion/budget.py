"""Freeze an evidence-based, non-monetary Phase 002D execution budget."""

from __future__ import annotations

import math
import statistics
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .cohort import COHORT_PATH
from .models import (
    RESULT_ROOT,
    check_or_write,
    file_sha256,
    hashed_body,
    read_json,
    sha256_json,
)
from .pilot import PILOT_PATH

BUDGET_PATH = RESULT_ROOT / "budget/frozen_budget.json"
BUDGET_SCHEMA_PATH = Path("contracts/expansion_budget.schema.json")


def _percentiles(values: list[float | int]) -> dict[str, float]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise RuntimeError("BUDGET_DISTRIBUTION_EMPTY")
    return {
        "minimum": round(ordered[0], 6),
        "median": round(statistics.median(ordered), 6),
        "maximum": round(ordered[-1], 6),
    }


def historical_metrics(root: Path) -> dict[str, Any]:
    paths = sorted((root / "evals/results/phase-002/runs").glob("*/*/*.json"))
    runs = [read_json(path) for path in paths]
    completed = sum(run["completion_status"] == "COMPLETED" for run in runs)
    input_tokens = [
        run["token_usage"]["input_tokens"]
        for run in runs
        if run.get("token_usage") and isinstance(run["token_usage"].get("input_tokens"), int)
    ]
    output_tokens = [
        run["token_usage"]["output_tokens"]
        for run in runs
        if run.get("token_usage") and isinstance(run["token_usage"].get("output_tokens"), int)
    ]
    return {
        "attempts": len(runs),
        "successful_primary_records": completed,
        "observed_success_rate": completed / len(runs),
        "input_tokens": _percentiles(input_tokens),
        "output_tokens": _percentiles(output_tokens),
        "elapsed_seconds": _percentiles([run["duration_seconds"] for run in runs]),
        "run_record_set_hash": sha256_json(
            {path.relative_to(root).as_posix(): file_sha256(path) for path in paths}
        ),
    }


def build_budget(root: Path) -> dict[str, Any]:
    cohort = read_json(root / COHORT_PATH)
    pilot = read_json(root / PILOT_PATH)
    if pilot["status"] != "PASS":
        raise RuntimeError("PILOT_NOT_PASS")
    if cohort["pilot_status"] != "PASS" or cohort["transport_profile"] == "PENDING_PILOT":
        raise RuntimeError("COHORT_TRANSPORT_NOT_FROZEN")
    history = historical_metrics(root)
    successful_pilot = next(
        attempt for attempt in pilot["attempts"] if attempt["completion_status"] == "PASS"
    )
    target = cohort["target_successes"]
    base_attempts = math.ceil(target / history["observed_success_rate"])
    absolute_attempt_cap = 28 if cohort["mode"] == "CONTINUATION_COHORT" else 48
    maximum_attempts = min(absolute_attempt_cap, base_attempts + 3)
    expected_input = math.ceil(history["input_tokens"]["median"] * base_attempts)
    expected_output = math.ceil(history["output_tokens"]["median"] * base_attempts)
    expected_elapsed = math.ceil(history["elapsed_seconds"]["median"] * base_attempts)
    if expected_input > 10_000_000 or expected_elapsed > 14_400:
        raise RuntimeError("COST_BUDGET_EXCEEDED")
    maximum_elapsed = min(14_400, math.ceil(expected_elapsed * 1.35))
    maximum_output = math.ceil(expected_output * 1.5)
    body = {
        "schema_version": "1.0.0",
        "budget_id": "PHASE-002D-FROZEN-BUDGET-001",
        "cohort_id": cohort["cohort_id"],
        "cohort_hash": cohort["cohort_hash"],
        "cohort_mode": cohort["mode"],
        "model": cohort["model"],
        "reasoning_setting": cohort["reasoning_setting"],
        "transport_profile": cohort["transport_profile"],
        "pilot_result_hash": pilot["result_hash"],
        "target_successes": target,
        "maximum_total_attempts": maximum_attempts,
        "absolute_attempt_cap": absolute_attempt_cap,
        "maximum_attempts_per_cell": 3,
        "maximum_fresh_retries_per_cell": 2,
        "maximum_consecutive_infrastructure_failures": 3,
        "maximum_consecutive_infrastructure_failures_per_cell": 2,
        "maximum_total_input_tokens": 10_000_000,
        "maximum_total_output_tokens": maximum_output,
        "maximum_total_elapsed_seconds": maximum_elapsed,
        "maximum_failed_cells": 8,
        "batch_size": 3,
        "maximum_later_batch_size": 6,
        "concurrency": 1,
        "historical_metrics": history,
        "pilot_metrics": {
            "attempts": pilot["model_start_count"],
            "successful_attempt_duration_seconds": successful_pilot["duration_seconds"],
            "input_tokens": successful_pilot["token_usage"]["input_tokens"],
            "cached_input_tokens": successful_pilot["token_usage"]["cached_input_tokens"]
            if successful_pilot["token_usage"]["cached_input_tokens"] is not None
            else "UNKNOWN",
            "output_tokens": successful_pilot["token_usage"]["output_tokens"],
            "reasoning_tokens": successful_pilot["token_usage"]["reasoning_tokens"]
            if successful_pilot["token_usage"]["reasoning_tokens"] is not None
            else "UNKNOWN",
        },
        "formula": {
            "base_attempts": "ceil(target_successes / historical_observed_success_rate)",
            "maximum_total_attempts": "min(mode_absolute_cap, base_attempts + 3)",
            "expected_total_input_tokens": "historical_median_input_tokens * base_attempts",
            "expected_total_output_tokens": "historical_median_output_tokens * base_attempts",
            "expected_total_elapsed_seconds": "historical_median_elapsed_seconds * base_attempts",
        },
        "formula_values": {
            "base_attempts": base_attempts,
            "expected_total_input_tokens": expected_input,
            "expected_total_output_tokens": expected_output,
            "expected_total_elapsed_seconds": expected_elapsed,
        },
        "token_observability": {
            "input_tokens": "OBSERVED",
            "output_tokens": "OBSERVED",
            "cached_input_tokens": "UNKNOWN",
            "reasoning_tokens": "UNKNOWN",
        },
        "monetary_cost": "UNKNOWN",
        "monetary_cost_reason": "CHATGPT_MANAGED_CODEX_NOT_API_BILLING",
        "api_key_used": False,
        "api_billing_used": False,
        "budget_may_expand_after_results": False,
        "scored_runs_started_at_freeze": False,
        "stop_conditions": [
            "MINIMA_SATISFIED",
            "INPUT_FREEZE_BROKEN",
            "COHORT_MISMATCH",
            "MODEL_OR_REASONING_CHANGED",
            "TRANSPORT_PROFILE_CHANGED",
            "SCHEDULE_OR_POLICY_HASH_MISMATCH",
            "NETWORK_OR_MCP_VIOLATION",
            "INPUT_MUTATION_OR_CONTAMINATION",
            "SCHEMA_OR_ORACLE_INVARIANT_BROKEN",
            "MAXIMUM_TOTAL_ATTEMPTS_REACHED",
            "MAXIMUM_CELL_ATTEMPTS_REACHED",
            "THREE_CONSECUTIVE_INFRASTRUCTURE_FAILURES",
            "TOKEN_OR_ELAPSED_BUDGET_REACHED",
            "AUTH_QUOTA_OR_MODEL_UNAVAILABLE",
        ],
    }
    return hashed_body(body, "budget_hash")


def validate_budget(root: Path, budget: dict[str, Any]) -> list[str]:
    schema = read_json(root / BUDGET_SCHEMA_PATH)
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(budget)]
    body = dict(budget)
    recorded = body.pop("budget_hash", None)
    if sha256_json(body) != recorded:
        errors.append("BUDGET_HASH_MISMATCH")
    if budget["maximum_total_attempts"] > budget["absolute_attempt_cap"]:
        errors.append("ATTEMPT_CAP_EXCEEDED")
    if budget["formula_values"]["expected_total_input_tokens"] > 10_000_000:
        errors.append("EXPECTED_INPUT_COST_EXCEEDED")
    if budget["formula_values"]["expected_total_elapsed_seconds"] > 14_400:
        errors.append("EXPECTED_ELAPSED_COST_EXCEEDED")
    if budget["concurrency"] != 1:
        errors.append("UNPROVEN_CONCURRENCY")
    return sorted(errors)


def check_or_write_budget(root: Path, *, check: bool) -> dict[str, Any]:
    expected = build_budget(root)
    errors = validate_budget(root, expected)
    errors.extend(check_or_write(root / BUDGET_PATH, expected, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "target_successes": expected["target_successes"],
        "maximum_total_attempts": expected["maximum_total_attempts"],
        "expected_total_input_tokens": expected["formula_values"]["expected_total_input_tokens"],
        "expected_total_elapsed_seconds": expected["formula_values"][
            "expected_total_elapsed_seconds"
        ],
        "budget_hash": expected["budget_hash"],
    }
