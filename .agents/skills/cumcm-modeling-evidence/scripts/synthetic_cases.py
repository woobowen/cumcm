"""Project-original deterministic prediction and optimization smoke cases."""

from __future__ import annotations

from pathlib import Path
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
    direction: str = "MIN",
) -> dict[str, str]:
    return {
        "candidate_set": core.canonical_hash(candidate_ids),
        "metric": core.canonical_hash({"name": metric, "direction": direction}),
        "seed_schedule": core.canonical_hash([20260904]),
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
    raw_path: str,
    raw_hash: str,
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
    manifest = {
        "run_id": run_id,
        "input_files": [{"path": raw_path, "sha256": raw_hash}],
        "input_hash": core.canonical_hash([raw_hash]),
        "code_commit": "SKILL-0.2.0-COMPETITION-RC1",
        "code_tree_hash": core.file_hash(Path(core.__file__)),
        "configuration_hash": core.canonical_hash({"candidate_id": candidate_id, "seed": 20260904}),
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
    state = core.load_state(case_root)
    audit = core.read_artifact(case_root, "data_audit")["content"]
    assumptions = core.read_artifact(case_root, "assumptions_and_symbols")["content"]
    selected = final["selected_model"]
    manifest = manifests[selected]
    return {
        "contract_version": "modeling-to-paper/v1",
        "problem_requirements": requirements,
        "requirement_traceability": {
            item["requirement_id"]: claim["claim_id"] for item in requirements
        },
        "data_dictionary": {
            "case_kind": state["case_kind"],
            "raw_files": sorted(audit["data_hashes"]),
        },
        "data_quality_report": audit,
        "assumptions": assumptions["assumptions"],
        "symbols": assumptions["symbols"],
        "formulas": formulas,
        "sources": core.read_artifact(case_root, "source_ledger")["content"]["sources"],
        "selected_models": [item for item in candidates if item["candidate_id"] == selected],
        "final_runs": [
            {
                "run_id": manifest["run_id"],
                "manifest_hash": core.canonical_hash(manifest),
                "output_hash": manifest["output_hash"],
            }
        ],
        "final_metrics": final["final_metrics"],
        "result_tables": tables,
        "figure_ready_data": figures,
        "validation_results": {
            "comparison_decision_hash": final["decision_hash"],
            "selected_model": selected,
            "test_used_for_selection": comparison["test_access"]["used_for_selection"],
        },
        "robustness_results": robustness,
        "uncertainty": {
            "scope": "deterministic synthetic perturbations",
            "quantified": True,
        },
        "failure_cases": robustness["failure_cases"],
        "limitations": limitations,
        "claim_evidence": {claim["claim_id"]: claim},
        "reproduction": {
            "skill_version": core.VERSION,
            "architecture": core.ARCHITECTURE,
            "run_manifest_hash": core.canonical_hash(manifest),
            "offline": True,
        },
        "generated_at": "2026-09-04T00:00:00Z",
        "approved_by": ["MACHINE_TECHNICAL_GATES"],
    }


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
    core.write_json(raw_path, rows, overwrite=False)
    raw_hash = core.file_hash(raw_path)
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
            "data_hashes": {raw_relative: raw_hash},
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
    freezes = _freezes(core, candidate_ids, "MAE")
    splits = {
        "train": list(range(1, 7)),
        "validation": list(range(7, 10)),
        "test": list(range(10, 13)),
    }
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
            "random_seeds": [20260904],
            "candidate_ids": candidate_ids,
            "trusted_freeze_registry": freezes,
            "stop_rule": "one deterministic run per candidate",
        },
    )
    _advance_to(core, case_root, "RUNNING")
    train = [(1, 3), (2, 5), (3, 7), (4, 9), (5, 11), (6, 13)]
    validation = [(7, 15), (8, 17), (9, 19)]
    test = [(10, 21), (11, 23), (12, 25)]
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
        }
    )
    attempts: list[dict[str, Any]] = []
    manifests: dict[str, dict[str, Any]] = {}
    for candidate in candidate_ids:
        output = {
            "candidate_id": candidate,
            "predictions": [
                {"time": t, "actual": y, "prediction": predictors[candidate](t)}
                for t, y in validation + test
            ],
            "validation_mae": validation_scores[candidate],
        }
        manifest = _write_run(
            core,
            case_root,
            candidate_id=candidate,
            raw_path=raw_relative,
            raw_hash=raw_hash,
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
            }
        )
    comparison = {
        "candidate_ids": candidate_ids,
        "baseline_id": "P-BASELINE-MEAN",
        "splits": splits,
        "metric": "MAE",
        "metric_direction": "MIN",
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
            "model_comparison",
            "robustness_analysis",
            "final_result",
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
    core.write_json(raw_path, problem, overwrite=False)
    raw_hash = core.file_hash(raw_path)
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
    freezes = _freezes(core, candidate_ids, "negative_profit")
    splits = {
        "train": ["problem-definition"],
        "validation": ["feasibility-and-objective"],
        "test": ["complete-enumeration-certificate"],
    }
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
            "random_seeds": [20260904],
            "candidate_ids": candidate_ids,
            "trusted_freeze_registry": freezes,
            "stop_rule": "enumerate bounded integer feasible region once",
        },
    )
    _advance_to(core, case_root, "RUNNING")
    feasible = [
        (a, b, 4 * a + 5 * b)
        for a in range(6)
        for b in range(6)
        if 2 * a + b <= 8 and a + 3 * b <= 10
    ]
    optimum = max(feasible, key=lambda item: (item[2], -item[0], -item[1]))
    outcomes = {
        "O-BASELINE-A-ONLY": {"x_A": 4, "x_B": 0, "profit": 16, "feasible": True},
        "O-ENUMERATION": {
            "x_A": optimum[0],
            "x_B": optimum[1],
            "profit": optimum[2],
            "feasible": True,
        },
        "O-INFEASIBLE-PROPOSAL": {
            "x_A": 5,
            "x_B": 5,
            "profit": 45,
            "feasible": False,
        },
    }
    scores = {key: -float(value["profit"]) for key, value in outcomes.items() if value["feasible"]}
    selected = min(scores, key=lambda key: (scores[key], key))
    decision_hash = core.canonical_hash(
        {
            "selected_candidate_id": selected,
            "validation_scores": scores,
            "metric": "negative_profit",
            "rule": "ARGMIN_THEN_ID",
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
            raw_path=raw_relative,
            raw_hash=raw_hash,
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
            }
        )
    comparison = {
        "candidate_ids": candidate_ids,
        "baseline_id": "O-BASELINE-A-ONLY",
        "splits": splits,
        "metric": "negative_profit",
        "metric_direction": "MIN",
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
    for labor in (7, 9):
        variants = [
            (a, b, 4 * a + 5 * b)
            for a in range(6)
            for b in range(6)
            if 2 * a + b <= labor and a + 3 * b <= 10
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
    scope = f"在给定整数约束与完整枚举域内，最优利润为 {result['profit']}"
    final = {
        "status": "FINAL_CANDIDATE",
        "selected_model": selected,
        "run_id": manifest["run_id"],
        "output_hash": manifest["output_hash"],
        "decision_hash": decision_hash,
        "final_metrics": {
            "profit": result["profit"],
            "x_A": result["x_A"],
            "x_B": result["x_B"],
        },
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
            "complete_enumeration",
            "model_comparison",
            "robustness_analysis",
            "final_result",
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
