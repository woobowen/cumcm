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
POLICY_FREEZE_PATH = BENCHMARK_ROOT / "manifests/policy_freeze_manifest.json"
AUDIT_CONTRACT = Path("contracts/specification_audit.schema.json")
AUDIT_PATHS = (
    Path("evals/results/phase-002d-r2/threshold_outputs/effectiveness_threshold_designer.json"),
    Path("evals/results/phase-002d-r2/threshold_outputs/false_block_threshold_designer.json"),
    Path("evals/results/phase-002d-r2/threshold_outputs/cost_maintenance_threshold_designer.json"),
)
POLICY_DEPENDENCIES = (
    METRIC_PATH,
    THRESHOLD_PATH,
    BENCHMARK_ROOT / "prospective_experiment_protocol.yaml",
    BENCHMARK_ROOT / "budget_policy.yaml",
    BENCHMARK_ROOT / "ablation_policy.yaml",
    Path("specifications/architectures/architecture_candidate_set.yaml"),
    BENCHMARK_ROOT / "sealed_manifest.json",
    BENCHMARK_ROOT / "manifests/oracle_interface_registry.json",
    BENCHMARK_ROOT / "access_policy.yaml",
    *AUDIT_PATHS,
    Path("evals/results/phase-002d-r2/audit_outputs/threshold_and_metric_prosecutor.json"),
    Path("evals/results/phase-002d-r2/audit_outputs/cost_complexity_dissent_auditor.json"),
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


def _absolute(
    metric_id: str,
    comparator: str,
    value: float,
    source: list[str],
    *,
    hard: bool,
    formula: str | None = None,
):
    return {
        "metric_id": metric_id,
        "rule_kind": "ABSOLUTE",
        "comparator": comparator,
        "value": value,
        "formula": formula,
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
                hard=True,
            ),
            _baseline(
                "valid_control_false_block_rate",
                "LE",
                "N_valid=number of complete paired valid controls >=20; candidate_blocks and "
                "baseline_blocks are paired binary outcomes; n10=count(candidate=1,baseline=0), "
                "n01=count(candidate=0,baseline=1); alpha=0.05; exact one-sided paired binomial "
                "noninferiority test on discordant pairs rejects H0:(candidate_rate-baseline_rate) "
                ">= delta where delta=max(0.05,1/N_valid); zero discordance passes only when "
                "candidate_blocks<=baseline_blocks; missing/mismatched pairs ABSTAIN",
                false_block,
                hard=True,
            ),
            _absolute("state_transition_precision", "EQ", 1, effectiveness, hard=True),
            _absolute("state_transition_recall", "EQ", 1, effectiveness, hard=True),
            _absolute("stale_propagation_recall", "EQ", 1, effectiveness, hard=True),
            _baseline(
                "claim_support_precision",
                "GE",
                "candidate >= min(1.0, max(0.95, baseline + 0.10)); baseline missing ABSTAIN",
                effectiveness,
                hard=True,
            ),
            _baseline(
                "claim_support_recall",
                "GE",
                "candidate >= min(1.0, max(0.95, baseline + 0.10)); baseline missing ABSTAIN",
                effectiveness,
                hard=True,
            ),
            _absolute("leakage_detection_recall", "EQ", 1, effectiveness, hard=True),
            _baseline(
                "reproduction_success_rate",
                "GE",
                "candidate >= max(0.95, baseline)",
                effectiveness,
                hard=True,
            ),
            _baseline(
                "completion_rate",
                "GE",
                "candidate >= max(0.95, baseline); all planned attempts remain in denominator",
                effectiveness,
                hard=True,
            ),
            _baseline(
                "terminal_failure_rate",
                "LE",
                "candidate <= baseline; terminal and censored outcomes are not zero",
                effectiveness,
                hard=True,
            ),
            _absolute(
                "retry_burden",
                "LE",
                0.25,
                cost,
                hard=True,
                formula="retry_burden=retry_attempt_count/max(1,planned_primary_slot_count); "
                "all infrastructure retries count once; permission cap and acceptance cap are "
                "both 0.25; missing ledger or zero planned slots ABSTAIN",
            ),
            _baseline(
                "input_token_overhead",
                "LE",
                "aggregate candidate/max(1,baseline) <= 1.50 and maximum case ratio using "
                "max(1,baseline_case) <= 2.00; missing baseline ABSTAIN",
                cost,
                hard=True,
            ),
            _baseline(
                "output_token_overhead",
                "LE",
                "aggregate candidate/max(1,baseline) <= 1.50 and maximum case ratio using "
                "max(1,baseline_case) <= 2.00; missing baseline ABSTAIN",
                cost,
                hard=True,
            ),
            _baseline(
                "elapsed_time_overhead",
                "LE",
                "same-runner aggregate candidate/max(0.001,baseline) <= 2.00 and maximum case "
                "ratio using max(0.001,baseline_case) <= 3.00; missing baseline ABSTAIN",
                cost,
                hard=True,
            ),
            _absolute(
                "tracked_code_surface",
                "LE",
                24,
                cost,
                hard=True,
                formula="count unique maintained logical units across runtime code, contracts, "
                "prompts, validators, adapters, tests and configuration; file split/merge or "
                "rename does not change logical-unit identity; generated files excluded only "
                "when reproducibly generated from a counted source",
            ),
            _absolute(
                "maintenance_score",
                "LE",
                24,
                cost,
                hard=True,
                formula="sum one point per maintained logical unit plus one per independent "
                "migration adapter, reason-code registry and retained-artifact policy; use the "
                "same logical-unit manifest as tracked_code_surface",
            ),
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
            "Every opaque sealed case maps inside the isolated adjudicator before execution to "
            "an oracle class, frozen strata, domain-separated seed commitment and inclusion "
            "reason; none of that per-case metadata is candidate-visible.",
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
        "decision_table": [
            {
                "rank": 1,
                "condition": (
                    "any policy hash, freeze-order, oracle, evaluator or access-integrity failure"
                ),
                "disposition": "STALE",
            },
            {
                "rank": 2,
                "condition": (
                    "any missing, unknown, censored, mismatched or insufficient denominator"
                ),
                "disposition": "EVIDENCE_INSUFFICIENT",
            },
            {
                "rank": 3,
                "condition": "any individual threshold fails",
                "disposition": "AUTOMATED_REJECTED",
            },
            {
                "rank": 4,
                "condition": "all individual thresholds pass",
                "disposition": "ELIGIBLE_FOR_FUTURE_AUTOMATED_COMPARISON",
            },
        ],
        "policy_dependency_classes": [
            "metric_registry",
            "threshold_policy",
            "experiment_protocol",
            "budget_and_ablation_policy",
            "candidate_set",
            "benchmark_and_oracle_interfaces",
            "designer_and_prosecutor_rationales",
            "evaluator_and_access_policy",
        ],
        "baseline_rule": (
            "ARCH-S0 is comparator and fallback; it is never required to improve over itself "
            "and is not selected in Phase 002D-R2."
        ),
        "cost_accounting": {
            "manifest_required": True,
            "unknown_cost_disposition": "EVIDENCE_INSUFFICIENT",
            "strict_dominance_rule": (
                "an otherwise eligible arm strictly dominated on every frozen cost by a simpler "
                "eligible arm is AUTOMATED_REJECTED unless a predeclared non-cost threshold is "
                "measurably superior"
            ),
        },
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
    dependency_hashes = {path.as_posix(): file_sha256(root / path) for path in POLICY_DEPENDENCIES}
    body = {
        "schema_version": "1.0.0",
        "manifest_id": "PHASE-002D-R2-JOINT-POLICY-FREEZE-001",
        "status": "POLICY_FROZEN_BEFORE_PROTOTYPE",
        "subject_commit": "f96d353923d75675a6c9900547fc477d91ae538b",
        "freeze_order": "BEFORE_ANY_PROTOTYPE_OR_MODEL_ATTEMPT",
        "prototype_attempt_count_at_freeze": 0,
        "model_start_count_at_freeze": 0,
        "candidate_results_present": False,
        "dependency_hashes": dependency_hashes,
        "mutation_effect": "TRANSITIVE_STALE_TO_ATTEMPTS_METRICS_AUDITS_DECISIONS_AND_REPORTS",
    }
    write_json(root / POLICY_FREEZE_PATH, {**body, "manifest_hash": sha256_json(body)})
    return validate_thresholds(root)


def validate_thresholds(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    metric = read_yaml(root / METRIC_PATH)
    policy = read_yaml(root / THRESHOLD_PATH)
    freeze = read_json(root / POLICY_FREEZE_PATH)
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
    if any(item.get("noncompensatory") is not True for item in policy.get("thresholds", [])):
        errors.append("COMPENSATORY_THRESHOLD_PROHIBITED")
    table = policy.get("decision_table", [])
    if [item.get("rank") for item in table] != [1, 2, 3, 4]:
        errors.append("THRESHOLD_DECISION_TABLE_INVALID")
    freeze_body = dict(freeze)
    freeze_hash = freeze_body.pop("manifest_hash", None)
    if sha256_json(freeze_body) != freeze_hash:
        errors.append("POLICY_FREEZE_MANIFEST_HASH_MISMATCH")
    if (
        freeze.get("prototype_attempt_count_at_freeze") != 0
        or freeze.get("model_start_count_at_freeze") != 0
    ):
        errors.append("POLICY_FROZEN_AFTER_ATTEMPT")
    for relative, expected in freeze.get("dependency_hashes", {}).items():
        path = root / relative
        if not path.is_file() or file_sha256(path) != expected:
            errors.append(f"POLICY_FREEZE_DEPENDENCY_DRIFT:{relative}")
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
    "POLICY_DEPENDENCIES",
    "POLICY_FREEZE_PATH",
    "THRESHOLD_PATH",
    "build_threshold_policy",
    "freeze_thresholds",
    "validate_thresholds",
]
