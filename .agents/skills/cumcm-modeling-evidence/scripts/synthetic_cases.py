"""Project-original deterministic prediction and optimization smoke cases."""

from __future__ import annotations

from pathlib import Path
from statistics import median
from typing import Any


def _accepted(core: Any, case_root: Path, key: str, content: dict[str, Any]) -> None:
    core.write_json(
        case_root / core.ARTIFACT_PATHS[key],
        core.artifact(key, content),
    )


def _advance_to(core: Any, case_root: Path, target: str) -> None:
    while core.load_state(case_root)["state"] != target:
        core.advance_once(case_root)


def _freezes(
    core: Any,
    candidate_ids: list[str],
    metric: str,
    splits: dict[str, list[Any]],
    baseline_id: str,
    direction: str = "MIN",
) -> dict[str, str]:
    return {
        "candidate_set": core.canonical_hash(candidate_ids),
        "metric": core.canonical_hash(
            {
                "name": metric,
                "direction": direction,
                "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
                "selection_rule": "ARGMIN_THEN_ID" if direction == "MIN" else "ARGMAX_THEN_ID",
            }
        ),
        "seed_schedule": core.canonical_hash([20260904]),
        "split_assignment": core.canonical_hash(splits),
        "baseline": core.canonical_hash(baseline_id),
    }


def _common_intake(
    core: Any,
    case_root: Path,
    requirements: list[dict[str, str]],
    questions: list[str],
) -> None:
    _accepted(
        core,
        case_root,
        "problem_requirements",
        {"case_id": core.load_state(case_root)["case_id"], "requirements": requirements},
    )
    _advance_to(core, case_root, "REQUIREMENTS_VALIDATED")
    _accepted(
        core,
        case_root,
        "research_plan",
        {
            "mode": "OFFLINE_PROJECT_ORIGINAL",
            "questions": questions,
            "external_search": False,
        },
    )
    _accepted(
        core,
        case_root,
        "source_ledger",
        {
            "sources": [{"source_id": "SRC-PROJECT-ORIGINAL", "kind": "PROJECT_ORIGINAL"}],
            "answer_access_status": "NOT_ACCESSED",
        },
    )
    _advance_to(core, case_root, "SOURCES_PLANNED")


def _write_run(
    core: Any,
    case_root: Path,
    *,
    candidate_id: str,
    input_paths: list[str],
    output: dict[str, Any],
    freezes: dict[str, str],
    decision_hash: str,
    outcome: str = "SUCCESS",
    failure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_id = f"RUN-{candidate_id}"
    output_path = case_root / f"runs/{run_id}/output.json"
    core.write_json(output_path, output)
    output_file_hash = core.file_hash(output_path)
    input_files = [
        {"path": relative, "sha256": core.file_hash(case_root / relative)}
        for relative in input_paths
    ]
    code_paths = ["scripts/cumcm_case.py", "scripts/synthetic_cases.py"]
    code_files = [
        {
            "scope": "SKILL_ROOT",
            "path": relative,
            "repository_path": f".agents/skills/cumcm-modeling-evidence/{relative}",
            "sha256": core.file_hash(core.SKILL_ROOT / relative),
        }
        for relative in code_paths
    ]
    configuration = {"candidate_id": candidate_id, "seed": 20260904}
    manifest = {
        "run_id": run_id,
        "input_files": input_files,
        "input_hash": core.canonical_hash([item["sha256"] for item in input_files]),
        "code_commit": core.current_git_commit(),
        "code_files": code_files,
        "code_tree_hash": core.canonical_hash([item["sha256"] for item in code_files]),
        "configuration": configuration,
        "configuration_hash": core.canonical_hash(configuration),
        "random_seed": 20260904,
        "argv": ["cumcm_case.py", "smoke", "--kind", core.load_state(case_root)["case_kind"]],
        "cwd_policy": "CASE_ROOT_RELATIVE",
        "environment_allowlist": {"PYTHONHASHSEED": "0", "TZ": "UTC"},
        "output_files": [
            {
                "path": str(output_path.relative_to(case_root)),
                "sha256": output_file_hash,
            }
        ],
        "output_hash": core.canonical_hash([output_file_hash]),
        "outcome": outcome,
        "failure": failure,
        "supersession": None,
        "trusted_capture": True,
        "freeze_bindings": freezes,
        "decision_hash": decision_hash,
    }
    core.write_json(case_root / f"runs/{run_id}/manifest.json", manifest)
    return manifest


def _handoff(
    core: Any,
    case_root: Path,
    *,
    requirements: list[dict[str, str]],
    claim: dict[str, Any],
    final: dict[str, Any],
    comparison: dict[str, Any],
    robustness: dict[str, Any],
    candidates: list[dict[str, Any]],
    manifests: dict[str, dict[str, Any]],
    formulas: list[dict[str, str]],
    tables: list[dict[str, Any]],
    figures: list[dict[str, Any]],
    limitations: list[str],
) -> dict[str, Any]:
    del requirements, claim, final, comparison, robustness, candidates, manifests
    del formulas, tables, figures, limitations
    return core.build_expected_handoff(case_root, core.load_state(case_root))


def _prediction(core: Any, case_root: Path) -> dict[str, Any]:
    rows = [
        {
            "time": index,
            "target": 2 * index + 1 if index != 5 else None,
            "future_target": 2 * (index + 1) + 1,
        }
        for index in range(1, 13)
    ]
    rows[5]["target"] = 99
    raw_relative = "data/raw/prediction_rows.json"
    raw_path = case_root / raw_relative
    if raw_path.is_file():
        if core.load_json(raw_path) != rows:
            raise ValueError("RC_PREDICTION_BOUND_RAW_INPUT_MISMATCH")
    else:
        core.write_json(raw_path, rows, overwrite=False)
    raw_hash = core.file_hash(raw_path)
    consumed_rows = core.load_json(raw_path)
    if not isinstance(consumed_rows, list) or len(consumed_rows) < 6:
        raise ValueError("RC_PREDICTION_RAW_INPUT_INVALID")
    observed = sorted(
        (int(row["time"]), float(row["target"]))
        for row in consumed_rows
        if isinstance(row, dict)
        and isinstance(row.get("time"), int)
        and isinstance(row.get("target"), (int, float))
        and not isinstance(row.get("target"), bool)
    )
    slopes = [
        (right_y - left_y) / (right_t - left_t)
        for index, (left_t, left_y) in enumerate(observed)
        for right_t, right_y in observed[index + 1 :]
        if right_t != left_t
    ]
    robust_slope = median(slopes)
    robust_intercept = median(y - robust_slope * t for t, y in observed)
    residuals = [abs(y - (robust_intercept + robust_slope * t)) for t, y in observed]
    residual_threshold = max(1.0, 6.0 * median(residuals))
    cleaned: list[dict[str, float | int]] = []
    imputed_times: list[int] = []
    outlier_times: list[int] = []
    for row in sorted(consumed_rows, key=lambda item: item["time"]):
        time = int(row["time"])
        target = row.get("target")
        expected = robust_intercept + robust_slope * time
        if target is None:
            imputed_times.append(time)
            value = expected
        elif abs(float(target) - expected) > residual_threshold:
            outlier_times.append(time)
            value = expected
        else:
            value = float(target)
        cleaned.append({"time": time, "target": value})
    processed_relative = "data/processed/prediction_clean.json"
    processed_path = case_root / processed_relative
    processing = {
        "records": cleaned,
        "lineage": {
            "raw_path": raw_relative,
            "raw_sha256": raw_hash,
            "method": "THEIL_SEN_TREND_IMPUTE_AND_RESIDUAL_REPLACE_V1",
            "robust_slope": robust_slope,
            "robust_intercept": robust_intercept,
            "residual_threshold": residual_threshold,
            "imputed_times": imputed_times,
            "outlier_times": outlier_times,
            "discarded_fields": ["future_target"],
        },
    }
    core.write_json(processed_path, processing, overwrite=False)
    processed_hash = core.file_hash(processed_path)
    requirements = [
        {"requirement_id": "REQ-P-1", "text": "按时间顺序比较预测模型"},
        {"requirement_id": "REQ-P-2", "text": "拒绝 future_target 泄漏字段"},
        {"requirement_id": "REQ-P-3", "text": "输出稳健性与证据绑定"},
    ]
    _common_intake(core, case_root, requirements, ["时间回归机制", "数据泄漏控制"])
    _accepted(
        core,
        case_root,
        "assumptions_and_symbols",
        {
            "assumptions": ["短区间线性趋势可作为候选"],
            "symbols": {"t": "time", "y": "target", "y_hat": "prediction"},
            "formulas": ["y_hat=a+b*t", "MAE=mean(abs(y-y_hat))"],
        },
    )
    _accepted(
        core,
        case_root,
        "data_audit",
        {
            "raw_immutable": True,
            "data_hashes": {
                raw_relative: raw_hash,
                processed_relative: processed_hash,
            },
            "raw_data_hashes": {raw_relative: raw_hash},
            "processed_data_hashes": {processed_relative: processed_hash},
            "processing_lineage": processing["lineage"],
            "missing_values": 1,
            "outliers": 1,
            "rejected_leakage_fields": ["future_target"],
            "time_order_required": True,
        },
    )
    _advance_to(core, case_root, "DATA_AUDITED")
    candidates = [
        {
            "candidate_id": "P-BASELINE-MEAN",
            "baseline": True,
            "method": "train_mean",
        },
        {
            "candidate_id": "P-LINEAR-TREND",
            "baseline": False,
            "method": "least_squares",
        },
    ]
    _accepted(
        core,
        case_root,
        "model_candidates",
        {"candidates": candidates, "leakage_fields_excluded": ["future_target"]},
    )
    _advance_to(core, case_root, "MODELS_PROPOSED")
    candidate_ids = [item["candidate_id"] for item in candidates]
    splits = {
        "train": list(range(1, 7)),
        "validation": list(range(7, 10)),
        "test": list(range(10, 13)),
    }
    freezes = _freezes(core, candidate_ids, "MAE", splits, "P-BASELINE-MEAN")
    _accepted(
        core,
        case_root,
        "experiment_plan",
        {
            "preregistered": True,
            "execution_prepared": True,
            "splits": splits,
            "metric": "MAE",
            "metric_direction": "MIN",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
            "selection_rule": "ARGMIN_THEN_ID",
            "baseline_id": "P-BASELINE-MEAN",
            "handoff_generated_at": "2026-09-04T00:00:00Z",
            "random_seeds": [20260904],
            "candidate_ids": candidate_ids,
            "trusted_freeze_registry": freezes,
            "stop_rule": "one deterministic run per candidate",
        },
    )
    _advance_to(core, case_root, "RUNNING")
    model_input = core.load_json(processed_path)
    if (
        not isinstance(model_input, dict)
        or model_input.get("lineage", {}).get("raw_sha256") != raw_hash
        or core.file_hash(processed_path) != processed_hash
    ):
        raise ValueError("RC_PREDICTION_PROCESSED_INPUT_INVALID")
    points = {
        int(row["time"]): float(row["target"])
        for row in model_input.get("records", [])
        if isinstance(row, dict)
    }

    def split_points(name: str) -> list[tuple[int, float]]:
        try:
            return [(time, points[time]) for time in splits[name]]
        except KeyError as exc:
            raise ValueError("RC_PREDICTION_SPLIT_INPUT_MISSING") from exc

    train = split_points("train")
    validation = split_points("validation")
    test = split_points("test")
    mean_y = sum(y for _, y in train) / len(train)
    mean_t = sum(t for t, _ in train) / len(train)
    slope = sum((t - mean_t) * (y - mean_y) for t, y in train) / sum(
        (t - mean_t) ** 2 for t, _ in train
    )
    intercept = mean_y - slope * mean_t

    def baseline(_time: int) -> float:
        return mean_y

    def linear(time: int) -> float:
        return intercept + slope * time

    predictors = {"P-BASELINE-MEAN": baseline, "P-LINEAR-TREND": linear}
    validation_scores = {
        candidate: sum(abs(y - predict(t)) for t, y in validation) / len(validation)
        for candidate, predict in predictors.items()
    }
    selected = min(validation_scores, key=lambda key: (validation_scores[key], key))
    decision_hash = core.canonical_hash(
        {
            "selected_candidate_id": selected,
            "validation_scores": validation_scores,
            "metric": "MAE",
            "rule": "ARGMIN_THEN_ID",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        }
    )
    attempts: list[dict[str, Any]] = []
    manifests: dict[str, dict[str, Any]] = {}
    for candidate in candidate_ids:
        test_mae_for_candidate = sum(abs(y - predictors[candidate](t)) for t, y in test) / len(test)
        claim_scope_for_candidate = (
            f"在本合成数据冻结 test split 上，{candidate} 的 MAE 为 {test_mae_for_candidate:.6g}"
        )
        output = {
            "candidate_id": candidate,
            "validation_metrics": {"MAE": validation_scores[candidate]},
            "final_metrics": {"test_mae": test_mae_for_candidate},
            "claim_scope": claim_scope_for_candidate,
            "predictions": [
                {"time": t, "actual": y, "prediction": predictors[candidate](t)}
                for t, y in validation + test
            ],
            "validation_mae": validation_scores[candidate],
            "figure_ready_data": [
                {
                    "figure_id": "TEST_PREDICTIONS",
                    "series": [
                        {
                            "time": t,
                            "actual": y,
                            "prediction": predictors[candidate](t),
                        }
                        for t, y in test
                    ],
                }
            ],
            "limitations": ["仅验证项目原创小样本；不代表外部效度或生产适用性"],
            "uncertainty": {
                "scope": "deterministic synthetic perturbations",
                "quantified": True,
            },
        }
        manifest = _write_run(
            core,
            case_root,
            candidate_id=candidate,
            input_paths=[raw_relative, processed_relative],
            output=output,
            freezes=freezes,
            decision_hash=decision_hash,
        )
        manifests[candidate] = manifest
        attempts.append(
            {
                "candidate_id": candidate,
                "run_id": manifest["run_id"],
                "outcome": "SUCCESS",
                "validation_score": validation_scores[candidate],
                "random_seed": 20260904,
            }
        )
    comparison = {
        "candidate_ids": candidate_ids,
        "baseline_id": "P-BASELINE-MEAN",
        "splits": splits,
        "metric": "MAE",
        "metric_direction": "MIN",
        "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        "selection_rule": "ARGMIN_THEN_ID",
        "random_seeds": [20260904],
        "attempts": attempts,
        "selected_candidate_id": selected,
        "selection_decision_hash": decision_hash,
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
        "test_access": {"authorized": True, "count": 1, "used_for_selection": False},
        "reliability": {"attempts": 2, "successful": 2, "failed_or_infeasible": 0},
    }
    _accepted(core, case_root, "model_comparison", comparison)
    _advance_to(core, case_root, "RUN_VALIDATED")
    selected_predictor = predictors[selected]
    test_mae = sum(abs(y - selected_predictor(t)) for t, y in test) / len(test)
    robustness = {
        "status": "VALIDATED",
        "perturbations": [
            {
                "name": "target_plus_0.5",
                "mae": sum(abs((y + 0.5) - selected_predictor(t)) for t, y in test) / len(test),
            },
            {
                "name": "target_minus_0.5",
                "mae": sum(abs((y - 0.5) - selected_predictor(t)) for t, y in test) / len(test),
            },
        ],
        "failure_cases": ["线性趋势外推不保证适用于结构突变"],
    }
    _accepted(core, case_root, "robustness_analysis", robustness)
    manifest = manifests[selected]
    scope = f"在本合成数据冻结 test split 上，{selected} 的 MAE 为 {test_mae:.6g}"
    final = {
        "status": "FINAL_CANDIDATE",
        "selected_model": selected,
        "run_id": manifest["run_id"],
        "output_hash": manifest["output_hash"],
        "decision_hash": decision_hash,
        "final_metrics": {"test_mae": test_mae},
        "claim_scope": scope,
    }
    _accepted(core, case_root, "final_result", final)
    _advance_to(core, case_root, "FINAL_CANDIDATE")
    claim = {
        "claim_id": "CLAIM-P-1",
        "claim_text": scope,
        "supported_scope": scope,
        "run_id": manifest["run_id"],
        "run_manifest_hash": core.canonical_hash(manifest),
        "input_hash": manifest["input_hash"],
        "code_hash": manifest["code_tree_hash"],
        "configuration_hash": manifest["configuration_hash"],
        "output_hash": manifest["output_hash"],
        "decision_hash": decision_hash,
        "evidence_artifact_ids": [
            "results/model_comparison.json",
            "results/robustness.json",
            "results/final_result.json",
            manifest["output_files"][0]["path"],
        ],
        "evidence_status": "CURRENT",
        "contradiction_status": "NONE",
    }
    _accepted(core, case_root, "claim_evidence", claim)
    _advance_to(core, case_root, "EVIDENCE_VALIDATED")
    handoff = _handoff(
        core,
        case_root,
        requirements=requirements,
        claim=claim,
        final=final,
        comparison=comparison,
        robustness=robustness,
        candidates=candidates,
        manifests=manifests,
        formulas=[{"formula_id": "F-P-1", "expression": "y_hat=a+b*t"}],
        tables=[{"table_id": "T-P-1", "rows": attempts}],
        figures=[
            {
                "figure_id": "FIG-P-1",
                "series": [
                    {"time": t, "actual": y, "prediction": selected_predictor(t)} for t, y in test
                ],
            }
        ],
        limitations=["仅验证项目原创小样本；不代表外部效度或生产适用性"],
    )
    core.write_json(case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"], handoff)
    _advance_to(core, case_root, "READY_FOR_PAPER_HANDOFF")
    return {
        "case_id": core.load_state(case_root)["case_id"],
        "kind": "prediction",
        "selected_model": selected,
        "run_ids": sorted(manifest["run_id"] for manifest in manifests.values()),
        "final_metric": test_mae,
        "handoff_hash": core.file_hash(
            case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"]
        ),
    }


def _optimization(core: Any, case_root: Path) -> dict[str, Any]:
    problem = {
        "capacity": {"labor": 8, "material": 10},
        "products": {
            "A": {"labor": 2, "material": 1, "profit": 4},
            "B": {"labor": 1, "material": 3, "profit": 5},
        },
    }
    raw_relative = "data/raw/optimization_problem.json"
    raw_path = case_root / raw_relative
    if raw_path.is_file():
        if core.load_json(raw_path) != problem:
            raise ValueError("RC_OPTIMIZATION_BOUND_RAW_INPUT_MISMATCH")
    else:
        core.write_json(raw_path, problem, overwrite=False)
    raw_hash = core.file_hash(raw_path)
    consumed_problem = core.load_json(raw_path)
    try:
        labor_capacity = int(consumed_problem["capacity"]["labor"])
        material_capacity = int(consumed_problem["capacity"]["material"])
        product_a = consumed_problem["products"]["A"]
        product_b = consumed_problem["products"]["B"]
        a_labor = int(product_a["labor"])
        a_material = int(product_a["material"])
        a_profit = int(product_a["profit"])
        b_labor = int(product_b["labor"])
        b_material = int(product_b["material"])
        b_profit = int(product_b["profit"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("RC_OPTIMIZATION_RAW_INPUT_INVALID") from exc
    if (
        min(
            labor_capacity,
            material_capacity,
            a_labor,
            a_material,
            b_labor,
            b_material,
        )
        <= 0
    ):
        raise ValueError("RC_OPTIMIZATION_RAW_INPUT_INVALID")
    requirements = [
        {"requirement_id": "REQ-O-1", "text": "最大化资源约束下利润"},
        {"requirement_id": "REQ-O-2", "text": "拒绝不可行方案并验证最优性"},
        {"requirement_id": "REQ-O-3", "text": "输出约束敏感性"},
    ]
    _common_intake(core, case_root, requirements, ["整数枚举", "资源敏感性"])
    _accepted(
        core,
        case_root,
        "assumptions_and_symbols",
        {
            "assumptions": ["产量为非负整数", "单位利润与资源消耗固定"],
            "symbols": {"x_A": "A产量", "x_B": "B产量", "z": "利润"},
            "formulas": [
                "max z=4*x_A+5*x_B",
                "2*x_A+x_B<=8",
                "x_A+3*x_B<=10",
            ],
        },
    )
    _accepted(
        core,
        case_root,
        "data_audit",
        {
            "raw_immutable": True,
            "data_hashes": {raw_relative: raw_hash},
            "units_checked": True,
            "constraint_coefficients_checked": True,
        },
    )
    _advance_to(core, case_root, "DATA_AUDITED")
    candidates = [
        {
            "candidate_id": "O-BASELINE-A-ONLY",
            "baseline": True,
            "method": "simple_feasible",
        },
        {
            "candidate_id": "O-ENUMERATION",
            "baseline": False,
            "method": "complete_integer_enumeration",
        },
        {
            "candidate_id": "O-INFEASIBLE-PROPOSAL",
            "baseline": False,
            "method": "deliberate_negative_control",
        },
    ]
    _accepted(
        core,
        case_root,
        "model_candidates",
        {"candidates": candidates, "feasibility_required": True},
    )
    _advance_to(core, case_root, "MODELS_PROPOSED")
    candidate_ids = [item["candidate_id"] for item in candidates]
    splits = {
        "train": ["problem-definition"],
        "validation": ["feasibility-and-objective"],
        "test": ["complete-enumeration-certificate"],
    }
    freezes = _freezes(
        core,
        candidate_ids,
        "negative_profit",
        splits,
        "O-BASELINE-A-ONLY",
    )
    _accepted(
        core,
        case_root,
        "experiment_plan",
        {
            "preregistered": True,
            "execution_prepared": True,
            "splits": splits,
            "metric": "negative_profit",
            "metric_direction": "MIN",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
            "selection_rule": "ARGMIN_THEN_ID",
            "baseline_id": "O-BASELINE-A-ONLY",
            "handoff_generated_at": "2026-09-04T00:00:00Z",
            "random_seeds": [20260904],
            "candidate_ids": candidate_ids,
            "trusted_freeze_registry": freezes,
            "stop_rule": "enumerate bounded integer feasible region once",
        },
    )
    _advance_to(core, case_root, "RUNNING")
    max_a = min(labor_capacity // a_labor, material_capacity // a_material)
    max_b = min(labor_capacity // b_labor, material_capacity // b_material)
    feasible = [
        (a, b, a_profit * a + b_profit * b)
        for a in range(max_a + 1)
        for b in range(max_b + 1)
        if a_labor * a + b_labor * b <= labor_capacity
        and a_material * a + b_material * b <= material_capacity
    ]
    optimum = max(feasible, key=lambda item: (item[2], -item[0], -item[1]))
    outcomes = {
        "O-BASELINE-A-ONLY": {
            "candidate_id": "O-BASELINE-A-ONLY",
            "x_A": max_a,
            "x_B": 0,
            "profit": a_profit * max_a,
            "feasible": True,
        },
        "O-ENUMERATION": {
            "candidate_id": "O-ENUMERATION",
            "x_A": optimum[0],
            "x_B": optimum[1],
            "profit": optimum[2],
            "feasible": True,
        },
        "O-INFEASIBLE-PROPOSAL": {
            "candidate_id": "O-INFEASIBLE-PROPOSAL",
            "x_A": max_a + 1,
            "x_B": max_b + 1,
            "profit": a_profit * (max_a + 1) + b_profit * (max_b + 1),
            "feasible": False,
        },
    }
    scores = {key: -float(value["profit"]) for key, value in outcomes.items() if value["feasible"]}
    for candidate, output in outcomes.items():
        output["validation_metrics"] = (
            {"negative_profit": scores[candidate]} if output["feasible"] else {}
        )
        output["final_metrics"] = {
            "profit": output["profit"],
            "x_A": output["x_A"],
            "x_B": output["x_B"],
        }
        output["claim_scope"] = (
            f"在给定整数约束与完整枚举域内，候选 {candidate} 的利润为 {output['profit']}"
        )
        output["figure_ready_data"] = [
            {
                "figure_id": "SELECTED_SOLUTION",
                "series": [
                    {
                        "x_A": output["x_A"],
                        "x_B": output["x_B"],
                        "profit": output["profit"],
                    }
                ],
            }
        ]
        output["limitations"] = ["只证明冻结的小规模整数域；未建立外部效度或生产性能"]
        output["uncertainty"] = {
            "scope": "deterministic synthetic perturbations",
            "quantified": True,
        }
    selected = min(scores, key=lambda key: (scores[key], key))
    decision_hash = core.canonical_hash(
        {
            "selected_candidate_id": selected,
            "validation_scores": scores,
            "metric": "negative_profit",
            "rule": "ARGMIN_THEN_ID",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        }
    )
    attempts: list[dict[str, Any]] = []
    manifests: dict[str, dict[str, Any]] = {}
    for candidate in candidate_ids:
        success = outcomes[candidate]["feasible"]
        manifest = _write_run(
            core,
            case_root,
            candidate_id=candidate,
            input_paths=[raw_relative],
            output=outcomes[candidate],
            freezes=freezes,
            decision_hash=decision_hash,
            outcome="SUCCESS" if success else "INFEASIBLE",
            failure=None if success else {"class": "CONSTRAINT_VIOLATION", "retained": True},
        )
        manifests[candidate] = manifest
        attempts.append(
            {
                "candidate_id": candidate,
                "run_id": manifest["run_id"],
                "outcome": manifest["outcome"],
                "validation_score": scores.get(candidate),
                "random_seed": 20260904,
            }
        )
    comparison = {
        "candidate_ids": candidate_ids,
        "baseline_id": "O-BASELINE-A-ONLY",
        "splits": splits,
        "metric": "negative_profit",
        "metric_direction": "MIN",
        "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        "selection_rule": "ARGMIN_THEN_ID",
        "random_seeds": [20260904],
        "attempts": attempts,
        "selected_candidate_id": selected,
        "selection_decision_hash": decision_hash,
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
        "test_access": {"authorized": True, "count": 1, "used_for_selection": False},
        "reliability": {"attempts": 3, "successful": 2, "failed_or_infeasible": 1},
    }
    _accepted(core, case_root, "model_comparison", comparison)
    _advance_to(core, case_root, "RUN_VALIDATED")
    perturbations = []
    for labor in (labor_capacity - 1, labor_capacity + 1):
        variants = [
            (a, b, a_profit * a + b_profit * b)
            for a in range(labor // a_labor + 1)
            for b in range(labor // b_labor + 1)
            if a_labor * a + b_labor * b <= labor
            and a_material * a + b_material * b <= material_capacity
        ]
        best = max(variants, key=lambda item: (item[2], -item[0], -item[1]))
        perturbations.append(
            {"labor_capacity": labor, "x_A": best[0], "x_B": best[1], "profit": best[2]}
        )
    robustness = {
        "status": "VALIDATED",
        "perturbations": perturbations,
        "failure_cases": ["资源或利润系数改变时需重新枚举"],
    }
    _accepted(core, case_root, "robustness_analysis", robustness)
    manifest = manifests[selected]
    result = outcomes[selected]
    selected_output = core.load_json(case_root / manifest["output_files"][0]["path"])
    scope = selected_output["claim_scope"]
    final = {
        "status": "FINAL_CANDIDATE",
        "selected_model": selected,
        "run_id": manifest["run_id"],
        "output_hash": manifest["output_hash"],
        "decision_hash": decision_hash,
        "final_metrics": selected_output["final_metrics"],
        "claim_scope": scope,
    }
    _accepted(core, case_root, "final_result", final)
    _advance_to(core, case_root, "FINAL_CANDIDATE")
    claim = {
        "claim_id": "CLAIM-O-1",
        "claim_text": scope,
        "supported_scope": scope,
        "run_id": manifest["run_id"],
        "run_manifest_hash": core.canonical_hash(manifest),
        "input_hash": manifest["input_hash"],
        "code_hash": manifest["code_tree_hash"],
        "configuration_hash": manifest["configuration_hash"],
        "output_hash": manifest["output_hash"],
        "decision_hash": decision_hash,
        "evidence_artifact_ids": [
            "results/model_comparison.json",
            "results/robustness.json",
            "results/final_result.json",
            manifest["output_files"][0]["path"],
        ],
        "evidence_status": "CURRENT",
        "contradiction_status": "NONE",
    }
    _accepted(core, case_root, "claim_evidence", claim)
    _advance_to(core, case_root, "EVIDENCE_VALIDATED")
    handoff = _handoff(
        core,
        case_root,
        requirements=requirements,
        claim=claim,
        final=final,
        comparison=comparison,
        robustness=robustness,
        candidates=candidates,
        manifests=manifests,
        formulas=[
            {"formula_id": "F-O-1", "expression": "max z=4*x_A+5*x_B"},
            {
                "formula_id": "F-O-2",
                "expression": "2*x_A+x_B<=8; x_A+3*x_B<=10",
            },
        ],
        tables=[{"table_id": "T-O-1", "rows": attempts}],
        figures=[{"figure_id": "FIG-O-1", "series": perturbations}],
        limitations=["只证明冻结的小规模整数域；未建立外部效度或生产性能"],
    )
    core.write_json(case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"], handoff)
    _advance_to(core, case_root, "READY_FOR_PAPER_HANDOFF")
    return {
        "case_id": core.load_state(case_root)["case_id"],
        "kind": "optimization",
        "selected_model": selected,
        "run_ids": sorted(manifest["run_id"] for manifest in manifests.values()),
        "objective": result["profit"],
        "handoff_hash": core.file_hash(
            case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"]
        ),
    }


def run_synthetic_case(
    core: Any,
    case_root: Path,
    case_id: str,
    kind: str,
) -> dict[str, Any]:
    if core.state_path(case_root).is_file():
        state = core.load_state(case_root)
        if state["state"] != "CREATED" or state["case_id"] != case_id or state["case_kind"] != kind:
            raise ValueError("RC_SMOKE_PREINITIALIZED_CASE_MISMATCH")
    else:
        core.initialize_case(case_root, case_id, kind)
    result = (
        _prediction(core, case_root) if kind == "prediction" else _optimization(core, case_root)
    )
    state = core.load_state(case_root)
    if state["state"] != "READY_FOR_PAPER_HANDOFF":
        raise ValueError("RC_SMOKE_NOT_READY_FOR_PAPER_HANDOFF")
    result["final_state"] = state["state"]
    result["transition_count"] = len(state["history"]) - 1
    result["case_state_hash"] = core.file_hash(core.state_path(case_root))
    return result
