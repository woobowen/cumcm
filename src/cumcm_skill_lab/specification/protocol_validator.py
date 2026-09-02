"""Freeze and validate the prospective shadow-evaluation protocol without executing it."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import read_json, read_yaml, sha256_json, write_json

from .architecture_validator import SPECIFICATION as ARCHITECTURE_SPECIFICATION
from .benchmark_generator import BENCHMARK_ROOT

PROTOCOL_PATH = BENCHMARK_ROOT / "prospective_experiment_protocol.yaml"
ABLATION_PATH = BENCHMARK_ROOT / "ablation_policy.yaml"
BUDGET_PATH = BENCHMARK_ROOT / "budget_policy.yaml"
CONTRACT = Path("contracts/prospective_experiment_protocol.schema.json")


def build_protocol(architecture_arms: list[str]) -> dict[str, Any]:
    ablation = {
        "stage1_arms": [
            "baseline",
            "accepted-versus-done-workflow-state-only",
            "claim-evidence-support-gate-only",
            "hash-bound-reproducibility-manifest-only",
            "leakage-safe-model-comparison-gate-only",
            "all-four-components",
            "reproducibility-plus-claim-support-interaction",
        ],
        "stage2_max_component_ablations": 2,
        "selection_rule": (
            "Choose at most two components with the largest deterministic critical-case "
            "contribution, ordered by component ID on ties; never use model results or preference."
        ),
        "candidate_results_used": False,
        "post_hoc_selection": False,
    }
    body = {
        "schema_version": "1.0.0",
        "protocol_id": "PHASE-002D-R2-PROSPECTIVE-PROTOCOL-001",
        "status": "POLICY_FROZEN",
        "executed_in_phase_002d_r2": False,
        "architecture_arms": architecture_arms,
        "stages": [
            {
                "stage": 1,
                "name": "DETERMINISTIC_CONFORMANCE",
                "entry_condition": "specification, Benchmark and thresholds are frozen",
                "model_execution": False,
                "exit_condition": "all public, property and critical hidden hard gates pass",
            },
            {
                "stage": 2,
                "name": "MODEL_IN_LOOP_COMPOSITE_FUTURE",
                "entry_condition": "the architecture passed every Stage 1 hard gate",
                "model_execution": True,
                "exit_condition": "all planned terminal outcomes are preserved or the cap stops",
            },
            {
                "stage": 3,
                "name": "AUTOMATIC_ARCHITECTURE_ADJUDICATION_FUTURE",
                "entry_condition": "Stage 2 evidence is frozen without threshold mutation",
                "model_execution": False,
                "exit_condition": "audited deterministic decision and stable replay exist",
            },
        ],
        "stage2_equalities": [
            "same model cohort",
            "same Prompt",
            "same data",
            "same timeout",
            "same sandbox",
            "same network/MCP policy",
            "same hidden cases",
            "same grader",
        ],
        "composite_family_count": 4,
        "repeats": 2,
        "main_start_formula": "eligible_architecture_count * 4 * 2",
        "retry_allowance_formula": "ceil(main_model_starts * 0.25)",
        "absolute_start_cap": 30,
        "randomization": "BLOCKED_RANDOMIZED_ARM_ORDER",
        "retry_rules": [
            "Only independently classified fresh infrastructure failures may receive a retry.",
            "At most one retry is allowed for a primary slot and all attempts remain in ledgers.",
            "Retry allowance is ceil(main starts * 0.25); no terminal correctness failure is "
            "retried into success.",
        ],
        "stop_conditions": [
            "Stop an architecture before Stage 2 on any Stage 1 hard failure.",
            "Stop when the retry allowance or absolute 30-start cap is exhausted.",
            "Stop with RETEST_REQUIRED or EVIDENCE_INSUFFICIENT on missing, leaked, stale, "
            "censored or non-replayable critical evidence.",
        ],
        "ablation": ablation,
        "prohibited_arms": ["HANDSOMEZR", "YUSHUI", "any third-party whole package"],
    }
    return {**body, "protocol_hash": sha256_json(body)}


def _supporting_policies(protocol: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    ablation_body = {
        "schema_version": "1.0.0",
        "status": "POLICY_FROZEN",
        "executed": False,
        **protocol["ablation"],
    }
    budget_body = {
        "schema_version": "1.0.0",
        "status": "POLICY_FROZEN",
        "main_start_formula": protocol["main_start_formula"],
        "maximum_main_starts_for_three_eligible_arms": 24,
        "retry_allowance_formula": protocol["retry_allowance_formula"],
        "maximum_retry_starts_for_three_eligible_arms": 6,
        "absolute_start_cap": protocol["absolute_start_cap"],
        "real_model_starts_in_phase_002d_r2": 0,
        "api_calls_in_phase_002d_r2": 0,
        "prototype_executions_in_phase_002d_r2": 0,
    }
    return (
        {**ablation_body, "policy_hash": sha256_json(ablation_body)},
        {**budget_body, "policy_hash": sha256_json(budget_body)},
    )


def freeze_protocol(root: Path) -> dict[str, Any]:
    candidates = read_yaml(root / ARCHITECTURE_SPECIFICATION)["candidates"]
    protocol = build_protocol([item["architecture_id"] for item in candidates])
    ablation, budget = _supporting_policies(protocol)
    write_json(root / PROTOCOL_PATH, protocol)
    write_json(root / ABLATION_PATH, ablation)
    write_json(root / BUDGET_PATH, budget)
    return validate_protocol(root)


def _hash_valid(value: dict[str, Any], key: str) -> bool:
    body = dict(value)
    recorded = body.pop(key, None)
    return sha256_json(body) == recorded


def validate_protocol(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    protocol = read_yaml(root / PROTOCOL_PATH)
    ablation = read_yaml(root / ABLATION_PATH)
    budget = read_yaml(root / BUDGET_PATH)
    schema = read_json(root / CONTRACT)
    errors.extend(
        f"PROTOCOL_SCHEMA:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(schema).iter_errors(protocol)
    )
    if [item.get("stage") for item in protocol.get("stages", [])] != [1, 2, 3]:
        errors.append("PROTOCOL_STAGE_ORDER_INVALID")
    if protocol.get("stages", [{}, {}])[0].get("model_execution") is not False:
        errors.append("STAGE1_MODEL_EXECUTION_PROHIBITED")
    if not _hash_valid(protocol, "protocol_hash"):
        errors.append("PROTOCOL_HASH_MISMATCH")
    if not _hash_valid(ablation, "policy_hash"):
        errors.append("ABLATION_HASH_MISMATCH")
    if not _hash_valid(budget, "policy_hash"):
        errors.append("BUDGET_HASH_MISMATCH")
    frozen_ids = [
        item["architecture_id"]
        for item in read_yaml(root / ARCHITECTURE_SPECIFICATION)["candidates"]
    ]
    if protocol.get("architecture_arms") != frozen_ids:
        errors.append("PROTOCOL_ARCHITECTURE_ARM_DRIFT")
    if set(protocol.get("prohibited_arms", [])) & set(protocol.get("architecture_arms", [])):
        errors.append("PROTOCOL_PROHIBITED_ARM_INCLUDED")
    if budget.get("maximum_main_starts_for_three_eligible_arms") != 24:
        errors.append("PROTOCOL_MAIN_START_FORMULA_INVALID")
    if budget.get("maximum_retry_starts_for_three_eligible_arms") != 6:
        errors.append("PROTOCOL_RETRY_FORMULA_INVALID")
    if budget.get("absolute_start_cap") != 30:
        errors.append("PROTOCOL_START_CAP_INVALID")
    if any(
        budget.get(key) != 0
        for key in (
            "real_model_starts_in_phase_002d_r2",
            "api_calls_in_phase_002d_r2",
            "prototype_executions_in_phase_002d_r2",
        )
    ):
        errors.append("PROTOCOL_EXECUTED_DURING_FREEZE")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "architecture_arms": protocol.get("architecture_arms"),
        "absolute_start_cap": protocol.get("absolute_start_cap"),
        "executed_in_phase_002d_r2": protocol.get("executed_in_phase_002d_r2"),
        "protocol_hash": protocol.get("protocol_hash"),
    }


__all__ = [
    "ABLATION_PATH",
    "BUDGET_PATH",
    "PROTOCOL_PATH",
    "build_protocol",
    "freeze_protocol",
    "validate_protocol",
]
