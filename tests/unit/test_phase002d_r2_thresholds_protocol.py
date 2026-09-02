import copy
import json

import pytest
import yaml
from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import sha256_json
from cumcm_skill_lab.specification.benchmark_generator import BENCHMARK_ROOT
from cumcm_skill_lab.specification.protocol_validator import (
    ABLATION_PATH,
    BUDGET_PATH,
    PROTOCOL_PATH,
    validate_protocol,
)
from cumcm_skill_lab.specification.protocol_validator import (
    CONTRACT as PROTOCOL_CONTRACT,
)
from cumcm_skill_lab.specification.threshold_validator import (
    AUDIT_PATHS,
    HARD_ZERO_METRICS,
    METRIC_PATH,
    THRESHOLD_PATH,
    validate_thresholds,
)


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_frozen_metrics_and_thresholds_validate(repo_root):
    result = validate_thresholds(repo_root)
    assert result["status"] == "PASS"
    assert result["candidate_metrics_present_at_freeze"] is False
    assert result["metric_count"] >= 24


def test_frozen_prospective_protocol_validates_without_execution(repo_root):
    result = validate_protocol(repo_root)
    assert result["status"] == "PASS"
    assert result["executed_in_phase_002d_r2"] is False
    assert result["absolute_start_cap"] == 30


@pytest.mark.parametrize("metric_id", HARD_ZERO_METRICS)
def test_each_critical_zero_threshold_is_absolute_and_noncompensatory(repo_root, metric_id):
    policy = _yaml(repo_root / THRESHOLD_PATH)
    threshold = {item["metric_id"]: item for item in policy["thresholds"]}[metric_id]
    assert threshold["rule_kind"] == "ABSOLUTE"
    assert threshold["comparator"] == "EQ"
    assert threshold["value"] == 0
    assert threshold["noncompensatory"] is True
    assert threshold["candidate_results_used"] is False


def test_required_metric_categories_are_separate(repo_root):
    registry = _yaml(repo_root / METRIC_PATH)
    categories = {item["category"] for item in registry["metrics"]}
    assert categories == {
        "HARD_SAFETY",
        "TARGET_EFFECTIVENESS",
        "FALSE_BLOCK",
        "REPRODUCIBILITY",
        "STATE_CORRECTNESS",
        "CLAIM_SUPPORT",
        "LEAKAGE_PREVENTION",
        "COST",
        "MAINTENANCE",
    }
    assert set(registry["category_separation"]) == {
        "correctness",
        "reliability",
        "cost",
        "maintenance",
    }


@pytest.mark.parametrize(
    "metric_id",
    [
        "targeted_detection_recall",
        "valid_control_false_block_rate",
        "claim_support_precision",
        "reproduction_success_rate",
        "input_token_overhead",
        "output_token_overhead",
        "elapsed_time_overhead",
    ],
)
def test_baseline_derived_formula_is_frozen_without_candidate_results(repo_root, metric_id):
    policy = _yaml(repo_root / THRESHOLD_PATH)
    threshold = {item["metric_id"]: item for item in policy["thresholds"]}[metric_id]
    assert threshold["rule_kind"] == "BASELINE_DERIVED"
    assert threshold["formula"]
    assert threshold["value"] is None
    assert threshold["candidate_results_used"] is False


def test_false_block_threshold_is_paired_noninferiority(repo_root):
    policy = _yaml(repo_root / THRESHOLD_PATH)
    threshold = {item["metric_id"]: item for item in policy["thresholds"]}[
        "valid_control_false_block_rate"
    ]
    assert "paired" in threshold["formula"]
    assert "noninferiority" in threshold["formula"]
    assert threshold["noncompensatory"] is True


@pytest.mark.parametrize(
    ("metric_id", "value"),
    [("retry_burden", 0.10), ("tracked_code_surface", 24), ("maintenance_score", 24)],
)
def test_cost_and_maintenance_absolute_caps_are_frozen(repo_root, metric_id, value):
    policy = _yaml(repo_root / THRESHOLD_PATH)
    threshold = {item["metric_id"]: item for item in policy["thresholds"]}[metric_id]
    assert threshold["comparator"] == "LE"
    assert threshold["value"] == value


def test_threshold_mutation_marks_all_dependent_results_stale(repo_root):
    policy = _yaml(repo_root / THRESHOLD_PATH)
    assert policy["mutation_effect"] == "STALE_ALL_DEPENDENT_RESULTS"
    assert policy["disagreement_routing"] == "RETEST_REQUIRED"
    assert len(policy["abstention_conditions"]) >= 3


def test_oracle_class_map_closes_pre_result_denominator_gap(repo_root):
    mapping = _json(repo_root / BENCHMARK_ROOT / "manifests/oracle_class_map.json")
    assert mapping["frozen_before_prototype"] is True
    assert mapping["candidate_results_present"] is False
    assert mapping["record_count"] == 20
    assert {item["oracle_class"] for item in mapping["records"]} == {
        "VALID_CONTROL",
        "INVALID_CONTROL",
    }
    assert all(item["seed_identity_hash"] for item in mapping["records"])


@pytest.mark.parametrize("audit_path", AUDIT_PATHS)
def test_threshold_designers_are_read_only_peer_invisible_and_preserved(repo_root, audit_path):
    audit = _json(repo_root / audit_path)
    assert audit["round"] == "THRESHOLD_DESIGN"
    assert audit["read_only"] is True
    assert audit["peer_outputs_visible"] is False
    assert audit["verdict"] == "RETEST_REQUIRED"
    assert audit["proposed_rules"]


def test_protocol_stage_order_and_hard_gate_exclusion(repo_root):
    protocol = _yaml(repo_root / PROTOCOL_PATH)
    assert [item["stage"] for item in protocol["stages"]] == [1, 2, 3]
    assert protocol["stages"][0]["model_execution"] is False
    assert protocol["stages"][1]["entry_condition"] == (
        "the architecture passed every Stage 1 hard gate"
    )


@pytest.mark.parametrize(
    "required",
    [
        "same model cohort",
        "same Prompt",
        "same data",
        "same timeout",
        "same sandbox",
        "same network/MCP policy",
        "same hidden cases",
        "same grader",
    ],
)
def test_stage2_fairness_equalities_are_frozen(repo_root, required):
    assert required in _yaml(repo_root / PROTOCOL_PATH)["stage2_equalities"]


def test_protocol_budget_formula_and_caps(repo_root):
    protocol = _yaml(repo_root / PROTOCOL_PATH)
    budget = _yaml(repo_root / BUDGET_PATH)
    assert protocol["main_start_formula"] == "eligible_architecture_count * 4 * 2"
    assert budget["maximum_main_starts_for_three_eligible_arms"] == 24
    assert budget["maximum_retry_starts_for_three_eligible_arms"] == 6
    assert budget["absolute_start_cap"] == 30
    assert protocol["retry_allowance_formula"] == "ceil(main_model_starts * 0.25)"


def test_protocol_contains_no_upstream_candidate_arm(repo_root):
    protocol = _yaml(repo_root / PROTOCOL_PATH)
    assert "HANDSOMEZR" not in protocol["architecture_arms"]
    assert "YUSHUI" not in protocol["architecture_arms"]
    assert {"HANDSOMEZR", "YUSHUI"} <= set(protocol["prohibited_arms"])


def test_ablation_is_preregistered_and_not_post_hoc(repo_root):
    protocol = _yaml(repo_root / PROTOCOL_PATH)
    ablation = _yaml(repo_root / ABLATION_PATH)
    assert len(protocol["ablation"]["stage1_arms"]) >= 7
    assert protocol["ablation"]["stage2_max_component_ablations"] == 2
    assert protocol["ablation"]["candidate_results_used"] is False
    assert protocol["ablation"]["post_hoc_selection"] is False
    assert ablation["executed"] is False


def test_protocol_hash_and_schema_fail_after_post_hoc_mutation(repo_root):
    protocol = _yaml(repo_root / PROTOCOL_PATH)
    schema = _json(repo_root / PROTOCOL_CONTRACT)
    protocol["ablation"]["post_hoc_selection"] = True
    body = copy.deepcopy(protocol)
    body.pop("protocol_hash")
    protocol["protocol_hash"] = sha256_json(body)
    assert list(Draft202012Validator(schema).iter_errors(protocol))


@pytest.mark.parametrize(
    "counter",
    [
        "real_model_starts_in_phase_002d_r2",
        "api_calls_in_phase_002d_r2",
        "prototype_executions_in_phase_002d_r2",
    ],
)
def test_freeze_phase_execution_counters_are_zero(repo_root, counter):
    assert _yaml(repo_root / BUDGET_PATH)[counter] == 0
