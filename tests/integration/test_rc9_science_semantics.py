"""Actual common CLI positives and targeted scientific semantics counterexamples."""

import copy
import importlib.util
import json
import subprocess
import sys

import pytest


def module(repo_root):
    spec = importlib.util.spec_from_file_location(
        "rc9_neutral_helper", repo_root / "tests/integration/test_actual_controller_neutral_e2e.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def metric(*, predictive=True):
    return {
        "target": "discharge_remaining_time" if predictive else "allocation_quantity",
        "quantity": "REMAINING_TIME" if predictive else "SCALAR",
        "target_unit": "min" if predictive else "unit",
        "unit": "%" if predictive else "unit",
        "prediction_origin": "PER_SAMPLE" if predictive else "NOT_APPLICABLE",
        "formula": "ABSOLUTE_RELATIVE_ERROR" if predictive else "VALUE",
        "denominator": "TRUE_REMAINING_TIME" if predictive else "ONE",
        "sample_unit": "historical_origin" if predictive else "allocation",
        "aggregation": "MEAN" if predictive else "SINGLE",
        "weights": "UNIFORM",
        "direction": "MIN",
        "zero_denominator_policy": "REJECT",
    }


def temporal_data(kind, *, scale=1, reverse=False, entity_prefix="E"):
    observations = []
    for entity, maximum in [("A", 8), ("B", 12)]:
        for t in range(0, maximum + 1, 2):
            observations.append(
                {
                    "observation_id": f"{entity}-{t}",
                    "entity_id": entity_prefix + entity,
                    "observed_at": t * scale,
                    "available_at": t * scale,
                    "value": 12 - t / 10,
                }
            )
    observations.append(
        {
            "observation_id": "A-end",
            "entity_id": entity_prefix + "A",
            "observed_at": 20 * scale,
            "available_at": 20 * scale,
            "value": 10,
        }
    )
    samples = []
    for entity, origin, split in [
        ("A", 4, "VALIDATION"),
        ("A", 8, "VALIDATION"),
        ("B", 12, "FORECAST"),
    ]:
        ids = [f"{entity}-{t}" for t in range(0, origin + 1, 2)]
        samples.append(
            {
                "sample_id": f"{entity}-origin-{origin}",
                "entity_id": entity_prefix + entity,
                "origin": origin * scale,
                "target_time": 20 * scale,
                "split": split,
                "target_observation_id": "A-end" if split == "VALIDATION" else None,
                "feature_observation_ids": ids,
                "preprocess_fit_observation_ids": ids,
                "model_fit_observation_ids": ids,
            }
        )
    if reverse:
        observations.reverse()
    return {"experiment_kind": kind, "x": [1, 2], "y": [3, 4], "observations": observations}, {
        "schema_version": "temporal-visibility/v1",
        "task": "SAME_ENTITY_FUTURE",
        "index_path": "data/raw/input.json",
        "samples": samples,
    }


def build(
    repo_root,
    tmp_path,
    kind="prediction",
    *,
    mutation=None,
    scale=1,
    reverse=False,
    entity_prefix="E",
):
    h = module(repo_root)
    core = h._module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        "rc9_semantic_core",
    )
    data, temporal = temporal_data(kind, scale=scale, reverse=reverse, entity_prefix=entity_prefix)
    reqs, definitions, types = [], {}, {}
    for i, req_id in enumerate(["REQ-A", "REQ-B"]):
        predictive = kind == "prediction" or (kind == "mixed" and req_id == "REQ-B")
        req = h._requirement(req_id, fields=["time", "voltage"] if predictive else ["x", "y"])
        definition = metric(predictive=predictive)
        key = "metric_" + chr(ord("a") + i)
        definitions[key] = definition
        req.update(metric_contracts={key: definition}, scientific_facts_required=True)
        if predictive:
            req["prediction_spec"] = {
                "kind": "CONDITIONAL_ESTIMATE",
                "claim_type": "PREDICTIVE",
                "target_field": "future_remaining_time",
                "future_truth_field": "future_end_time",
                "known_input_fields": ["time", "voltage"],
                "model_basis": "OLS prefix-only affine voltage trajectory extrapolated to 10 V",
                "conditions": ["The local affine relation continues to 10 V; no regime change."],
                "historical_validation_required": True,
                "empirical_accuracy_required": False,
            }
        types[req_id] = "PREDICTIVE" if predictive else "FEASIBILITY"
        reqs.append(req)
    sources = [
        h._source("SRC-ALL", ["REQ-A", "REQ-B"], "AUTO", fields=["x", "y", "time", "voltage"])
    ]
    suff = {
        "contract_version": "data-sufficiency/v1",
        "requirements": reqs,
        "sources": sources,
        "acquisition_plans": [],
        "source_compositions": [],
        "coverage_mode_by_requirement": {
            r["requirement_id"]: {"mode": "SINGLE_SOURCE", "source_id": "SRC-ALL"} for r in reqs
        },
        "aggregate_completion_claimed": False,
        "requirement_assessments": [h._assessment(r["requirement_id"]) for r in reqs],
    }
    selection, semantic = h._selection_and_semantic(
        core,
        reqs,
        "",
        mode="PER_REQUIREMENT" if kind == "mixed" else "GLOBAL_JOINT",
        selected_candidates={"REQ-A": "CAND", "REQ-B": "BASE" if kind == "mixed" else "CAND"},
        claim_types=types,
    )
    for claim in semantic["claims"]:
        if claim["claim_type"] == "PREDICTIVE":
            claim["prediction_scope"] = "CONDITIONAL_ESTIMATE"
            claim["support_predicates"].update(
                validation_boundary_frozen=True,
                conditional_model_bound=True,
                historical_validation_recorded=True,
                held_out_test_valid=False,
                target_accuracy_verified=False,
            )
            claim["uncertainty"] = {"kind": "UNCALIBRATED_POINT_ESTIMATE", "calibrated": False}
        else:
            claim["support_predicates"]["independent_constraint_recalculation"] = True
    plan = {
        "metric_definitions": definitions,
        "splits": {"train": [], "validation": [], "test": []},
        "evaluation_design": {"mode": "NONPREDICTIVE_FINAL_VERIFICATION"},
    }
    if kind != "optimization":
        plan.update(
            temporal_design=temporal,
            evaluation_design={"mode": "CONDITIONAL_PREDICTION_FINAL_VERIFICATION"},
            splits={"train": ["PREFIX"], "validation": ["A-origin-4", "A-origin-8"], "test": []},
        )
    if mutation is not None:
        mutation(data, plan, reqs, semantic)
    core, case = h._build_runtime_case(
        repo_root,
        tmp_path,
        requirements=reqs,
        sources=sources,
        sufficiency=suff,
        selection=selection,
        semantic=semantic,
        model_fixture="tests/fixtures/rc9_science_model.py",
        checker_fixture="tests/fixtures/rc9_science_checker.py",
        raw_data=data,
        plan_extra=plan,
        execute_via_cli=True,
    )
    return h, core, case


def complete(repo_root, case):
    process = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/finalize_fresh_c_validation.py"),
            "--case-root",
            str(case),
            "--check-code",
            "models/independent_check.py",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert process.stdout.strip(), process.stderr
    return process, json.loads(process.stdout.splitlines()[-1])


@pytest.mark.parametrize("kind", ["optimization", "prediction", "mixed"])
def test_three_real_cli_e2e_allow_bounded_scientific_completion(repo_root, tmp_path, kind):
    _, core, case = build(repo_root, tmp_path, kind)
    p, result = complete(repo_root, case)
    assert p.returncode == 0, (result, p.stderr)
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    assert result["test_access_count"] == 0
    assert core.load_json(case / core.SCIENTIFIC_FINAL_LEDGER)["status"] == "SUCCESS"
    if kind == "mixed":
        assert len(result["selected_run_ids"]) == 2
    for claim in core.read_artifact(case, "semantic_claim_support")["content"]["claims"]:
        if claim["claim_type"] == "PREDICTIVE":
            assert claim["support_predicates"]["target_accuracy_verified"] is False


@pytest.mark.parametrize(
    "usage",
    ["feature_observation_ids", "preprocess_fit_observation_ids", "model_fit_observation_ids"],
)
def test_temporal_future_label_and_whole_data_transform_rejected_before_model(
    repo_root, tmp_path, usage
):
    def mutate(data, plan, reqs, semantic):
        plan["temporal_design"]["samples"][0][usage].append("A-end")

    with pytest.raises(ValueError, match="RC_TEMPORAL_FUTURE_INFORMATION"):
        build(repo_root, tmp_path, mutation=mutate)
    assert not list((tmp_path / "case").glob("runs/*/execution_capture.json"))


def test_new_entity_transfer_keeps_entity_isolation(repo_root, tmp_path):
    def mutate(data, plan, reqs, semantic):
        plan["temporal_design"]["task"] = "NEW_ENTITY_GENERALIZATION"

    with pytest.raises(ValueError, match="RC_TEMPORAL_NEW_ENTITY_GROUP_OVERLAP"):
        build(repo_root, tmp_path, mutation=mutate)


@pytest.mark.parametrize("mutation", ["descriptive", "accuracy", "interval"])
def test_conditional_output_cannot_be_relabelled_or_upgraded(repo_root, tmp_path, mutation):
    h, core, case = build(repo_root, tmp_path)
    semantic = core.read_artifact(case, "semantic_claim_support")["content"]
    if mutation == "descriptive":
        semantic["claims"][0]["claim_type"] = "DESCRIPTIVE"
        expected = "RC_PREDICTIVE_REQUIREMENT_RELABELLED"
    elif mutation == "accuracy":
        semantic["claims"][0]["support_predicates"]["target_accuracy_verified"] = True
        expected = "RC_PREDICTIVE_CONDITIONAL_SUPPORT_INVALID"
    else:
        semantic["claims"][0]["uncertainty"] = {"kind": "PREDICTION_INTERVAL", "calibrated": True}
        expected = "RC_PREDICTION_INTERVAL_UNCALIBRATED"
    h._accepted(core, case, "semantic_claim_support", semantic)
    p, result = complete(repo_root, case)
    assert p.returncode != 0, result
    assert expected in result["reason_codes"]
    assert not (case / core.SCIENTIFIC_FINAL_LEDGER).exists()


@pytest.mark.parametrize(
    "change",
    [
        "quantity",
        "target_unit",
        "prediction_origin",
        "denominator",
        "aggregation",
        "direction",
        "zero_denominator_policy",
    ],
)
def test_metric_contract_drift_does_not_inherit_old_freeze(repo_root, tmp_path, change):
    h, core, case = build(repo_root, tmp_path)
    plan = core.read_artifact(case, "experiment_plan")["content"]
    plan["metric_definitions"]["metric_a"][change] = "SUBSTITUTE"
    h._accepted(core, case, "experiment_plan", plan)
    with pytest.raises(ValueError, match="RC_METRIC|RC_TRUSTED_FREEZE"):
        core.trusted_freezes(case)


def test_elapsed_error_is_not_remaining_error_even_with_same_ranking(repo_root):
    core = module(repo_root)._module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        "rc9_metric_unit",
    )
    rows = [
        {
            "sample_id": "cut",
            "target": "discharge_remaining_time",
            "unit": "min",
            "origin": 90,
            "predicted_end_time": 101,
            "observed_end_time": 100,
        }
    ]
    remaining = metric()
    elapsed = copy.deepcopy(remaining)
    elapsed.update(quantity="ELAPSED_TIME", denominator="TRUE_ELAPSED_TIME")
    assert core.recompute_metric(remaining, rows)["value"] == 10
    assert core.recompute_metric(elapsed, rows)["value"] == 1
    assert core.metric_freeze_payload(
        {"metric_definitions": {"error": remaining}}
    ) != core.metric_freeze_payload({"metric_definitions": {"error": elapsed}})
    rows[0]["origin"] = 100
    with pytest.raises(ValueError, match="RC_METRIC_ZERO_DENOMINATOR"):
        core.recompute_metric(remaining, rows)


@pytest.mark.parametrize(
    ("scale", "reverse", "entity_prefix"), [(2, False, "RENAMED"), (1, True, "Z")]
)
def test_same_entity_origin_scale_order_and_identity_metamorphisms(
    repo_root, tmp_path, scale, reverse, entity_prefix
):
    _, _, case = build(
        repo_root, tmp_path, scale=scale, reverse=reverse, entity_prefix=entity_prefix
    )
    p, result = complete(repo_root, case)
    assert p.returncode == 0, (result, p.stderr)
