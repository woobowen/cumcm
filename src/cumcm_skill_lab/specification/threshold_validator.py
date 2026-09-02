"""Freeze and validate prospective thresholds from isolated designer outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import (
    file_sha256,
    read_json,
    read_yaml,
    sha256_json,
    write_json,
)

from .benchmark_generator import BENCHMARK_ROOT
from .metric_registry import build_metric_registry

METRIC_PATH = BENCHMARK_ROOT / "metric_registry.yaml"
THRESHOLD_PATH = BENCHMARK_ROOT / "threshold_policy.yaml"
METRIC_CONTRACT = Path("contracts/metric_registry.schema.json")
THRESHOLD_CONTRACT = Path("contracts/threshold_policy.schema.json")
AUDIT_CONTRACT = Path("contracts/specification_audit.schema.json")
AUDIT_PATHS = (
    Path("evals/results/phase-002d-r2/threshold_outputs/effectiveness_threshold_designer.json"),
    Path("evals/results/phase-002d-r2/threshold_outputs/false_block_threshold_designer.json"),
    Path("evals/results/phase-002d-r2/threshold_outputs/cost_maintenance_threshold_designer.json"),
)

HARD_ZERO_METRICS = (
    "critical_violation_count",
    "raw_input_mutation_count",
    "stale_false_accept_count",
    "unsupported_claim_false_accept_count",
    "test_leakage_false_accept_count",
    "manifest_mismatch_missed_count",
    "second_formal_skill_count",
    "second_state_truth_source_count",
    "hidden_vault_access_count",
    "third_party_execution_count",
    "unauthorized_state_write_count",
    "premature_test_access_count",
)


def _absolute(metric_id: str, comparator: str, value: float, source: list[str], *, hard: bool):
    return {
        "metric_id": metric_id,
        "rule_kind": "ABSOLUTE",
        "comparator": comparator,
        "value": value,
        "formula": None,
        "noncompensatory": hard,
        "candidate_results_used": False,
        "rationale_source": source,
    }


def _baseline(metric_id: str, comparator: str, formula: str, source: list[str], *, hard: bool):
    return {
        "metric_id": metric_id,
        "rule_kind": "BASELINE_DERIVED",
        "comparator": comparator,
        "value": None,
        "formula": formula,
        "noncompensatory": hard,
        "candidate_results_used": False,
        "rationale_source": source,
    }


def build_threshold_policy() -> dict[str, Any]:
    effectiveness = [AUDIT_PATHS[0].as_posix()]
    false_block = [AUDIT_PATHS[1].as_posix()]
    cost = [AUDIT_PATHS[2].as_posix()]
    hard = ["rules/phase002d_r2_workflow_rules.yaml"]
    thresholds = [_absolute(metric, "EQ", 0, hard, hard=True) for metric in HARD_ZERO_METRICS]
    thresholds.extend(
        [
            _absolute("final_test_access_count", "EQ", 1, effectiveness, hard=True),
            _baseline(
                "targeted_detection_recall",
                "GE",
                "candidate_overall - baseline_overall >= 0.10 and candidate_each_family >= "
                "baseline_each_family",
                effectiveness,
                hard=False,
            ),
            _baseline(
                "valid_control_false_block_rate",
                "LE",
                "paired false_block_count <= baseline_count + 1 and exact one-sided "
                "noninferiority rejects delta >= max(0.05, 1/N_valid)",
                false_block,
                hard=True,
            ),
            _absolute("state_transition_precision", "EQ", 1, effectiveness, hard=True),
            _absolute("state_transition_recall", "EQ", 1, effectiveness, hard=True),
            _absolute("stale_propagation_recall", "EQ", 1, effectiveness, hard=True),
            _baseline(
                "claim_support_precision",
                "GE",
                "candidate >= max(0.95, baseline + 0.10)",
                effectiveness,
                hard=True,
            ),
            _baseline(
                "claim_support_recall",
                "GE",
                "candidate >= max(0.95, baseline + 0.10)",
                effectiveness,
                hard=False,
            ),
            _absolute("leakage_detection_recall", "EQ", 1, effectiveness, hard=True),
            _baseline(
                "reproduction_success_rate",
                "GE",
                "candidate >= max(0.95, baseline)",
                effectiveness,
                hard=False,
            ),
            _baseline(
                "completion_rate",
                "GE",
                "candidate >= max(0.95, baseline); all planned attempts remain in denominator",
                effectiveness,
                hard=False,
            ),
            _baseline(
                "terminal_failure_rate",
                "LE",
                "candidate <= baseline; terminal and censored outcomes are not zero",
                effectiveness,
                hard=False,
            ),
            _absolute("retry_burden", "LE", 0.10, cost, hard=False),
            _baseline(
                "input_token_overhead",
                "LE",
                "aggregate candidate/baseline <= 1.50 and maximum case ratio <= 2.00",
                cost,
                hard=False,
            ),
            _baseline(
                "output_token_overhead",
                "LE",
                "aggregate candidate/baseline <= 1.50 and maximum case ratio <= 2.00",
                cost,
                hard=False,
            ),
            _baseline(
                "elapsed_time_overhead",
                "LE",
                "same-runner aggregate candidate/baseline <= 2.00 and maximum case ratio <= 3.00",
                cost,
                hard=False,
            ),
            _absolute("tracked_code_surface", "LE", 24, cost, hard=False),
            _absolute("maintenance_score", "LE", 24, cost, hard=False),
            _absolute("state_source_count", "EQ", 1, cost, hard=True),
            _absolute("formal_skill_count", "EQ", 1, cost, hard=True),
        ]
    )
    body = {
        "schema_version": "1.0.0",
        "policy_id": "PHASE-002D-R2-THRESHOLDS-001",
        "status": "POLICY_FROZEN",
        "frozen_before_prototype": True,
        "candidate_metrics_present_at_freeze": False,
        "thresholds": thresholds,
        "evidence_sufficiency": [
            "Every sealed case hash maps before execution to an oracle class, frozen strata, seed "
            "identity and inclusion reason.",
            "N_valid >= 20 paired valid controls; each reported stratum and transformation has "
            "at least 10 paired observations; block precision has at least 10 blocked labeled "
            "controls.",
            "Baseline and candidate receive identical cases, derived variants, seeds, model "
            "cohort, Prompt, environment and budgets with complete hash-bound terminal outcomes.",
            "Recovery-affected, leaked, censored, missing, post-freeze or hash-mismatched evidence "
            "is excluded from ranking and never scored zero.",
        ],
        "abstention_conditions": [
            "Any evidence-sufficiency denominator is unmet or precision is undefined.",
            "Any threshold, evaluator, oracle class, stratum, exclusion or candidate-set hash "
            "changed after freeze.",
            "Any critical outcome is missing, unknown, recovery-affected, censored or disputed by "
            "non-replayable evidence.",
            "Material independent-designer disagreement has not been resolved by a deterministic "
            "test.",
        ],
        "disagreement_routing": "RETEST_REQUIRED",
        "mutation_effect": "STALE_ALL_DEPENDENT_RESULTS",
    }
    return {**body, "policy_hash": sha256_json(body)}


def _schema_errors(schema: dict[str, Any], value: Any, prefix: str) -> list[str]:
    return [
        f"{prefix}:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(schema).iter_errors(value)
    ]


def freeze_thresholds(root: Path) -> dict[str, Any]:
    write_json(root / METRIC_PATH, build_metric_registry())
    write_json(root / THRESHOLD_PATH, build_threshold_policy())
    return validate_thresholds(root)


def validate_thresholds(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    metric = read_yaml(root / METRIC_PATH)
    policy = read_yaml(root / THRESHOLD_PATH)
    errors.extend(_schema_errors(read_json(root / METRIC_CONTRACT), metric, "METRIC"))
    errors.extend(_schema_errors(read_json(root / THRESHOLD_CONTRACT), policy, "THRESHOLD"))
    audit_schema = read_json(root / AUDIT_CONTRACT)
    for path in AUDIT_PATHS:
        audit = read_json(root / path)
        errors.extend(_schema_errors(audit_schema, audit, f"DESIGNER:{path.name}"))
        if audit.get("read_only") is not True or audit.get("peer_outputs_visible") is not False:
            errors.append(f"DESIGNER_ISOLATION_INVALID:{path.name}")
    metric_body = dict(metric)
    metric_hash = metric_body.pop("registry_hash", None)
    if sha256_json(metric_body) != metric_hash:
        errors.append("METRIC_REGISTRY_HASH_MISMATCH")
    policy_body = dict(policy)
    policy_hash = policy_body.pop("policy_hash", None)
    if sha256_json(policy_body) != policy_hash:
        errors.append("THRESHOLD_POLICY_HASH_MISMATCH")
    metric_ids = {item["metric_id"] for item in metric.get("metrics", [])}
    threshold_ids = [item.get("metric_id") for item in policy.get("thresholds", [])]
    if len(threshold_ids) != len(set(threshold_ids)) or not set(threshold_ids) <= metric_ids:
        errors.append("THRESHOLD_METRIC_BINDING_INVALID")
    by_id = {item["metric_id"]: item for item in policy.get("thresholds", [])}
    for metric_id in HARD_ZERO_METRICS:
        threshold = by_id.get(metric_id, {})
        if not (
            threshold.get("rule_kind") == "ABSOLUTE"
            and threshold.get("comparator") == "EQ"
            and threshold.get("value") == 0
            and threshold.get("noncompensatory") is True
        ):
            errors.append(f"HARD_ZERO_THRESHOLD_INVALID:{metric_id}")
    if any(
        item.get("candidate_results_used") is not False for item in policy.get("thresholds", [])
    ):
        errors.append("CANDIDATE_RESULT_THRESHOLD_HINDSIGHT")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "metric_count": len(metric.get("metrics", [])),
        "threshold_count": len(policy.get("thresholds", [])),
        "designer_output_hashes": {
            path.name: file_sha256(root / path) for path in AUDIT_PATHS if (root / path).is_file()
        },
        "policy_hash": policy.get("policy_hash"),
        "candidate_metrics_present_at_freeze": policy.get("candidate_metrics_present_at_freeze"),
    }


__all__ = [
    "AUDIT_PATHS",
    "HARD_ZERO_METRICS",
    "METRIC_PATH",
    "THRESHOLD_PATH",
    "build_threshold_policy",
    "freeze_thresholds",
    "validate_thresholds",
]
