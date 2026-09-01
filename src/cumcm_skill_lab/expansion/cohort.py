"""Fail-closed model-cohort selection and target calculation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import (
    ANONYMOUS_ARMS,
    CONFIG_PATH,
    PRIMARY_CASES,
    RESULT_ROOT,
    check_or_write,
    file_sha256,
    hashed_body,
    read_json,
    read_yaml,
    sha256_json,
)

COHORT_PATH = RESULT_ROOT / "cohort/cohort.json"
MODEL_AVAILABILITY_PATH = RESULT_ROOT / "cohort/model_availability.json"
SCHEMA_PATH = Path("contracts/experiment_cohort.schema.json")


def continuation_shortfall(root: Path, minimum_repeats: int = 2) -> dict[str, Any]:
    classification = read_json(root / "evals/results/phase-002a/eligibility/classification.json")
    counts: Counter[tuple[str, str]] = Counter()
    for cell in classification["cells"]:
        key = (cell["case_id"], cell["anonymous_arm_id"])
        if (
            cell["case_id"] in PRIMARY_CASES
            and cell["anonymous_arm_id"] in ANONYMOUS_ARMS
            and cell["classification"] == "PRIMARY_COMPLETE"
            and cell["ranking_eligible"] is True
        ):
            counts[key] += 1
    cells = []
    for case_id in PRIMARY_CASES:
        for arm_id in ANONYMOUS_ARMS:
            historical = counts[(case_id, arm_id)]
            needed = max(0, minimum_repeats - historical)
            cells.append(
                {
                    "case_id": case_id,
                    "anonymous_arm_id": arm_id,
                    "historical_eligible_repeats": historical,
                    "additional_successes_needed": needed,
                }
            )
    return {
        "minimum_repeats": minimum_repeats,
        "cells": cells,
        "target_successes": sum(cell["additional_successes_needed"] for cell in cells),
    }


def _efforts(model: dict[str, Any]) -> set[str]:
    values = model.get("reasoning", [])
    return {item.get("reasoningEffort") if isinstance(item, dict) else item for item in values}


def build_cohort(root: Path, availability: dict[str, Any]) -> dict[str, Any]:
    config = read_yaml(root / CONFIG_PATH)
    historical = read_yaml(root / "evals/configs/phase-002.yaml")
    models = {item["id"]: item for item in availability["models"]}
    historical_model = historical["model"]
    reasoning = config["reasoning_setting"]
    continuation_checks = {
        "historical_model_visible": historical_model in models,
        "model_id_exact": historical_model == config["preferred_historical_model"],
        "reasoning_exact": historical["reasoning_setting"] == reasoning,
        "frozen_prompt_schema_fixture_package_scorer_oracle": True,
        "sandbox_network_mcp_exact": all(
            (
                historical["sandbox"] == config["sandbox"],
                historical["network_policy"] == config["network_policy"],
                historical["mcp_policy"] == config["mcp_policy"],
            )
        ),
        "compatibility_pilot_pass": False,
        "transport_profile_frozen": False,
    }
    mode = "CONTINUATION_COHORT" if all(continuation_checks.values()) else "NEW_MODEL_COHORT"
    if mode == "CONTINUATION_COHORT":
        selected_model = historical_model
        target = continuation_shortfall(root)["target_successes"]
        historical_use = "PRIMARY_ELIGIBLE_IF_EXACT_MATCH"
    else:
        candidates = config["allowed_replacement_models"]
        selected_model = next(
            (
                candidate
                for candidate in candidates
                if candidate in models and reasoning in _efforts(models[candidate])
            ),
            None,
        )
        if selected_model is None:
            raise RuntimeError("NO_ALLOWED_MODEL_WITH_REQUIRED_REASONING")
        target = len(PRIMARY_CASES) * len(ANONYMOUS_ARMS) * config["minimum_repeats"]
        historical_use = "CROSS_MODEL_EXPLORATORY_GAP_EVIDENCE_ONLY"
    selected = models[selected_model]
    body = {
        "schema_version": "1.0.0",
        "cohort_id": f"PHASE-002D-{mode}-{selected_model.upper().replace('.', '-')}-MEDIUM",
        "mode": mode,
        "model": selected_model,
        "reasoning_setting": reasoning,
        "auth_mode": "CHATGPT_MANAGED_CODEX",
        "transport_profile": "PENDING_PILOT",
        "codex_cli_version": availability["codex_cli_version"],
        "sandbox": config["sandbox"],
        "network_policy": config["network_policy"],
        "mcp_policy": config["mcp_policy"],
        "primary_cases": list(PRIMARY_CASES),
        "anonymous_arms": list(ANONYMOUS_ARMS),
        "minimum_repeats": config["minimum_repeats"],
        "target_successes": target,
        "historical_phase002_use": historical_use,
        "historical_model": historical_model,
        "historical_model_visible": historical_model in models,
        "selected_model_supports_reasoning": reasoning in _efforts(selected),
        "continuation_checks": continuation_checks,
        "continuation_shortfall": continuation_shortfall(root),
        "selection_reason_codes": (
            ["ALL_CONTINUATION_HARD_CONDITIONS_PASS"]
            if mode == "CONTINUATION_COHORT"
            else [
                f"{key.upper()}_FAILED" for key, passed in continuation_checks.items() if not passed
            ]
        ),
        "candidate_model_ids": sorted(models),
        "pilot_status": "PENDING",
        "scored_runs_started": False,
        "model_switch_allowed": False,
    }
    return hashed_body(body, "cohort_hash")


def validate_cohort(root: Path, cohort: dict[str, Any]) -> list[str]:
    schema = read_json(root / SCHEMA_PATH)
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(cohort)]
    body = dict(cohort)
    recorded = body.pop("cohort_hash", None)
    if sha256_json(body) != recorded:
        errors.append("COHORT_HASH_MISMATCH")
    if cohort["mode"] == "NEW_MODEL_COHORT" and cohort["target_successes"] != 24:
        errors.append("NEW_MODEL_COHORT_TARGET_NOT_24")
    if cohort["mode"] == "CONTINUATION_COHORT" and cohort["target_successes"] != 14:
        errors.append("CONTINUATION_TARGET_NOT_RECOMPUTED_14")
    if cohort["historical_model"] != cohort["model"] and cohort["mode"] != "NEW_MODEL_COHORT":
        errors.append("CROSS_MODEL_PRIMARY_MIX")
    return sorted(errors)


def record_availability(
    *,
    checked_at: str,
    codex_cli_version: str,
    models: list[dict[str, Any]],
    raw_catalog_hash: str,
) -> dict[str, Any]:
    body = {
        "schema_version": "1.0.0",
        "checked_at": checked_at,
        "check_kind": "READ_ONLY_CODEX_APP_SERVER_MODEL_LIST",
        "codex_cli_version": codex_cli_version,
        "auth_mode": "CHATGPT_MANAGED_CODEX",
        "model_start_count": 0,
        "api_key_used": False,
        "api_billing_used": False,
        "raw_catalog_hash": raw_catalog_hash,
        "models": models,
    }
    return hashed_body(body, "availability_hash")


def check_or_write_cohort(root: Path, *, check: bool) -> dict[str, Any]:
    availability = read_json(root / MODEL_AVAILABILITY_PATH)
    expected = build_cohort(root, availability)
    errors = validate_cohort(root, expected)
    errors.extend(check_or_write(root / COHORT_PATH, expected, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "mode": expected["mode"],
        "model": expected["model"],
        "target_successes": expected["target_successes"],
        "cohort_hash": expected["cohort_hash"],
        "model_availability_hash": file_sha256(root / MODEL_AVAILABILITY_PATH),
    }
