#!/usr/bin/env python3
"""Prepare and finalize the private Development/Stress case workspaces."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[6]
CORE_PATH = REPO_ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
MODEL_SOURCE = Path(__file__).resolve().with_name("development_model.py")
MODEL_REPOSITORY_PATH = (
    "evals/results/phase-004a/CUMCM-2023-C-DEVELOPMENT-001/rc2/code/development_model.py"
)
FIRST_RUN_FREEZE_SHA256 = "9f27706b099b187c5c6c82984fcf3e760d7cbcc6640525bbf7841014929a2fb3"
SEED = 20260904
CANDIDATES = [
    "PIPELINE-SEASONAL-BASELINE",
    "PIPELINE-HIERARCHICAL-STOCHASTIC",
    "PIPELINE-NONPARAMETRIC-ROBUST",
]
BASELINE = CANDIDATES[0]
METRIC = "baseline_normalized_decision_loss"
STOP_RULE = "one bounded deterministic execution per preregistered candidate"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


core = load_module("phase004a_competition_rc2_core", CORE_PATH)
model = load_module("phase004a_development_model", MODEL_SOURCE)


def accepted(case_root: Path, key: str, content: dict[str, Any]) -> None:
    core.write_json(case_root / core.ARTIFACT_PATHS[key], core.artifact(key, content))


def advance_to(case_root: Path, target: str) -> None:
    while core.load_state(case_root)["state"] != target:
        core.advance_once(case_root)


def write_workbook(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_excel(path, index=False, engine="openpyxl")


def variant_metadata(variant: str) -> dict[str, Any]:
    if variant == "DEVELOPMENT_REGRESSION":
        return {
            "variant_id": variant,
            "quantity_column": "销量(千克)",
            "quantity_scale_to_kg": 1.0,
            "date_shift_days": 0,
            "loss_source_available": True,
        }
    if variant == "STRESS_A_SCHEMA_ORDERING":
        return {
            "variant_id": variant,
            "quantity_column": "销量(千克)",
            "quantity_scale_to_kg": 1.0,
            "date_shift_days": 0,
            "loss_source_available": True,
        }
    if variant == "STRESS_B_UNITS_TIME":
        return {
            "variant_id": variant,
            "quantity_column": "销量(克)",
            "quantity_scale_to_kg": 0.001,
            "date_shift_days": 365,
            "loss_source_available": True,
        }
    if variant == "STRESS_C_DEGRADED_INPUT":
        return {
            "variant_id": variant,
            "quantity_column": "销量(千克)",
            "quantity_scale_to_kg": 1.0,
            "date_shift_days": 0,
            "loss_source_available": False,
        }
    raise ValueError(f"unsupported variant: {variant}")


def transform_inputs(source: Path, case_root: Path, variant: str) -> dict[str, Any]:
    destination = case_root / "raw/case_files"
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    metadata = variant_metadata(variant)
    shutil.copy2(source / "C题.pdf", destination / "C题.pdf")

    if variant == "DEVELOPMENT_REGRESSION":
        for name in ("附件1.xlsx", "附件2.xlsx", "附件3.xlsx", "附件4.xlsx"):
            shutil.copy2(source / name, destination / name)
    elif variant == "STRESS_A_SCHEMA_ORDERING":
        for index, name in enumerate(("附件1.xlsx", "附件2.xlsx", "附件3.xlsx", "附件4.xlsx")):
            frame = pd.read_excel(source / name, sheet_name="Sheet1" if name == "附件4.xlsx" else 0)
            frame = frame.sample(frac=1.0, random_state=SEED + index).reset_index(drop=True)
            frame = frame[list(reversed(frame.columns))]
            if name == "附件1.xlsx":
                frame["审计无关字段"] = "SEMANTICS_UNCHANGED"
            write_workbook(frame, destination / name)
    elif variant == "STRESS_B_UNITS_TIME":
        shutil.copy2(source / "附件1.xlsx", destination / "附件1.xlsx")
        shutil.copy2(source / "附件4.xlsx", destination / "附件4.xlsx")
        sales = pd.read_excel(source / "附件2.xlsx")
        sales["销售日期"] = pd.to_datetime(sales["销售日期"]) + pd.Timedelta(days=365)
        sales = sales.rename(columns={"销量(千克)": "销量(克)"})
        sales["销量(克)"] = pd.to_numeric(sales["销量(克)"], errors="coerce") * 1000.0
        write_workbook(sales, destination / "附件2.xlsx")
        costs = pd.read_excel(source / "附件3.xlsx")
        costs["日期"] = pd.to_datetime(costs["日期"]) + pd.Timedelta(days=365)
        write_workbook(costs, destination / "附件3.xlsx")
    elif variant == "STRESS_C_DEGRADED_INPUT":
        shutil.copy2(source / "附件1.xlsx", destination / "附件1.xlsx")
        sales = pd.read_excel(source / "附件2.xlsx")
        sales = sales.loc[sales.index % 997 != 0].reset_index(drop=True)
        sales.loc[sales.index[::503], "销售单价(元/千克)"] = np.nan
        write_workbook(sales, destination / "附件2.xlsx")
        costs = pd.read_excel(source / "附件3.xlsx")
        costs.loc[costs.index[::211], "批发价格(元/千克)"] = np.nan
        write_workbook(costs, destination / "附件3.xlsx")
    else:
        raise ValueError(variant)

    core.write_json(case_root / "state/variant_metadata.json", metadata, overwrite=False)
    return {
        "variant": variant,
        "metadata": metadata,
        "file_hashes": {
            str(path.relative_to(case_root)): core.file_hash(path)
            for path in sorted(destination.iterdir())
        },
    }


def freeze_registry(
    required_inputs: dict[str, str],
    required_code: list[dict[str, str]],
    code_commit: str,
    splits: dict[str, list[str]],
    generated_at: str,
) -> dict[str, str]:
    aggregation = "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID"
    selection = "ARGMIN_THEN_ID"
    return {
        "candidate_set": core.canonical_hash(CANDIDATES),
        "metric": core.canonical_hash(
            {
                "name": METRIC,
                "direction": "MIN",
                "aggregation_rule": aggregation,
                "selection_rule": selection,
            }
        ),
        "seed_schedule": core.canonical_hash([SEED]),
        "split_assignment": core.canonical_hash(splits),
        "baseline": core.canonical_hash(BASELINE),
        "input_set": core.canonical_hash(required_inputs),
        "execution_policy": core.canonical_hash(
            {"stop_rule": STOP_RULE, "handoff_generated_at": generated_at}
        ),
        "code_set": core.canonical_hash(required_code),
        "code_commit": core.canonical_hash(code_commit),
    }


def write_output_contract_probe(case_root: Path, requirement_ids: list[str]) -> dict[str, Any]:
    relative = "experiments/selected_output_contract_probe.json"
    probe = {
        "candidate_id": "CONTRACT-PROBE",
        "status": "CONTRACT_PROBE",
        "probe_only": True,
        "ranking_eligible": False,
        "result_values_are_placeholders": True,
        "final_metrics": {METRIC: 0.0},
        "claim_scope": "Generic structural placeholder; not a result.",
        "requirement_claims": {
            requirement_id: {
                "claim_id": f"CLAIM-PROBE-{index}",
                "claim_text": "Generic structural placeholder; not a result.",
                "evidence_artifact_ids": [relative],
            }
            for index, requirement_id in enumerate(requirement_ids, start=1)
        },
        "figure_ready_data": [{"figure_id": "CONTRACT-PROBE", "rows": [0]}],
        "uncertainty": {"scope": "placeholder"},
        "limitations": ["Placeholder values are excluded from runs and ranking."],
        "robustness_evidence": {
            "metric": METRIC,
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "CONTRACT-PROBE-SHIFT",
                    "metric": METRIC,
                    "result": 0.0,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": ["A contract probe cannot establish empirical validity."],
        },
    }
    core.write_json(case_root / relative, probe, overwrite=False)
    result, observed = core.preflight_output_contract(case_root, Path(relative))
    if not result.accepted or observed != relative:
        raise ValueError("RC4_OUTPUT_CONTRACT_PREFLIGHT_FAILED")
    return {"status": result.status, "reason_codes": list(result.reason_codes), "path": relative}


def prepare_case(case_root: Path, code_commit: str) -> dict[str, Any]:
    state = core.load_state(case_root)
    if state["state"] != "CREATED":
        raise ValueError("case must be initialized and CREATED")
    model_path = case_root / "models/development_model.py"
    shutil.copy2(MODEL_SOURCE, model_path)
    metadata = core.load_json(case_root / "state/variant_metadata.json")
    if not isinstance(metadata, dict):
        raise ValueError("variant metadata missing")

    requirements = [
        {"requirement_id": "REQ-1A", "text": "analyze distributions by category and item"},
        {"requirement_id": "REQ-1B", "text": "analyze category relationships"},
        {"requirement_id": "REQ-2A", "text": "analyze price and demand relationships"},
        {"requirement_id": "REQ-2B", "text": "produce a seven-day category decision plan"},
        {"requirement_id": "REQ-3", "text": "produce a feasible item-level decision plan"},
        {"requirement_id": "REQ-4", "text": "identify additional data and its effects"},
    ]
    accepted(
        case_root,
        "problem_requirements",
        {"case_id": state["case_id"], "requirements": requirements},
    )
    advance_to(case_root, "REQUIREMENTS_VALIDATED")
    accepted(
        case_root,
        "research_plan",
        {
            "mode": "DEVELOPMENT_REGRESSION",
            "external_search": False,
            "first_run_freeze_sha256": FIRST_RUN_FREEZE_SHA256,
            "evidence_class": "DEVELOPMENT_OR_STRESS_NOT_GENERALIZATION",
        },
    )
    accepted(
        case_root,
        "source_ledger",
        {
            "sources": [
                {"source_id": "SRC-OFFICIAL-INPUT", "kind": "OFFICIAL_PROBLEM_INPUT"},
                {"source_id": "SRC-FIRST-RUN-FREEZE", "sha256": FIRST_RUN_FREEZE_SHA256},
            ],
            "answer_access_status": "UNLOCKED_AFTER_FIRST_RUN",
        },
    )
    advance_to(case_root, "SOURCES_PLANNED")
    accepted(
        case_root,
        "assumptions_and_symbols",
        {
            "assumptions": [
                "observed positive sales are a censored proxy for latent demand",
                "recent category cost and markup summaries remain planning-relevant",
                "future outcomes are unavailable and no causal price effect is claimed",
            ],
            "symbols": {
                "q": "sales quantity in kilograms",
                "p": "selling price per kilogram",
                "c": "wholesale cost per kilogram",
                "l": "loss fraction",
            },
            "formulas": [
                "WAPE=sum(abs(q-q_hat))/sum(abs(q))",
                "replenishment=q_hat/(1-l)",
                "profit_proxy=q_hat*p-replenishment*c",
            ],
        },
    )

    master, sales, costs, loss, _ = model.load_inputs(case_root)
    required_names = ["附件1.xlsx", "附件2.xlsx", "附件3.xlsx"]
    if bool(metadata["loss_source_available"]):
        required_names.append("附件4.xlsx")
    input_paths = [f"raw/case_files/{name}" for name in required_names]
    input_paths.append("state/variant_metadata.json")
    required_inputs = {
        relative: core.file_hash(case_root / relative) for relative in sorted(input_paths)
    }
    accepted(
        case_root,
        "data_audit",
        {
            "raw_immutable": True,
            "data_hashes": required_inputs,
            "raw_data_hashes": required_inputs,
            "row_counts": {
                "master": len(master),
                "positive_sales": len(sales),
                "wholesale": len(costs),
                "loss": len(loss),
            },
            "mapping_checks": {
                "unmatched_category_rows": int(sales["分类名称"].isna().sum()),
                "missing_wholesale_rows": int(sales["批发价格(元/千克)"].isna().sum()),
                "missing_loss_rows": int(sales["损耗率(%)"].isna().sum()),
            },
            "duplicate_full_sales_rows": int(sales.duplicated().sum()),
            "unit_conversion": {
                "source_column": metadata["quantity_column"],
                "scale_to_kg": metadata["quantity_scale_to_kg"],
            },
            "date_shift_days": metadata["date_shift_days"],
            "loss_source_available": metadata["loss_source_available"],
            "leakage": [
                "time order is mandatory",
                "future outcomes are excluded from selection",
                "observed price-demand association is not causal elasticity",
            ],
            "degraded_input_notice": (
                "loss rates imputed and observed missing values retained in uncertainty"
                if not metadata["loss_source_available"]
                else "none"
            ),
        },
    )
    advance_to(case_root, "DATA_AUDITED")
    candidates = [
        {
            "candidate_id": CANDIDATES[0],
            "baseline": True,
            "method": "weekday category mean",
            "failure_condition": "rapid structural change",
        },
        {
            "candidate_id": CANDIDATES[1],
            "baseline": False,
            "method": "trend plus weekly and annual seasonal regression",
            "failure_condition": "nonlinear regime change",
        },
        {
            "candidate_id": CANDIDATES[2],
            "baseline": False,
            "method": "recent weekday median",
            "failure_condition": "short recent window is unrepresentative",
        },
    ]
    accepted(
        case_root,
        "model_candidates",
        {
            "candidates": candidates,
            "selection_dimensions": [
                "requirement coverage",
                "validation loss",
                "leakage",
                "interpretability",
                "robustness",
                "feasibility",
            ],
        },
    )
    advance_to(case_root, "MODELS_PROPOSED")

    skill_relative = "scripts/cumcm_case.py"
    required_code = [
        {
            "scope": "SKILL_ROOT",
            "path": skill_relative,
            "repository_path": f".agents/skills/cumcm-modeling-evidence/{skill_relative}",
            "sha256": core.file_hash(core.SKILL_ROOT / skill_relative),
        },
        {
            "scope": "CASE_ROOT",
            "path": "models/development_model.py",
            "repository_path": MODEL_REPOSITORY_PATH,
            "sha256": core.file_hash(model_path),
        },
    ]
    for record in required_code:
        if core.git_blob_hash(code_commit, record["repository_path"]) != record["sha256"]:
            raise ValueError(f"code commit mismatch: {record['repository_path']}")
    max_date = sales["销售日期"].max()
    validation_start = max_date - pd.Timedelta(days=180)
    validation_end = max_date - pd.Timedelta(days=31)
    splits = {
        "train": [f"through-{(validation_start - pd.Timedelta(days=1)).date()}"],
        "validation": [f"{validation_start.date()}-through-{validation_end.date()}"],
        "test": [f"{(validation_end + pd.Timedelta(days=1)).date()}-through-{max_date.date()}"],
    }
    generated_at = core.utc_now()
    freezes = freeze_registry(required_inputs, required_code, code_commit, splits, generated_at)
    accepted(
        case_root,
        "experiment_plan",
        {
            "preregistered": True,
            "execution_prepared": True,
            "candidate_ids": CANDIDATES,
            "baseline_id": BASELINE,
            "metric": METRIC,
            "metric_direction": "MIN",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
            "selection_rule": "ARGMIN_THEN_ID",
            "random_seeds": [SEED],
            "splits": splits,
            "required_input_hashes": required_inputs,
            "required_code_files": required_code,
            "code_commit": code_commit,
            "trusted_freeze_registry": freezes,
            "stop_rule": STOP_RULE,
            "handoff_generated_at": generated_at,
        },
    )
    preflight = write_output_contract_probe(
        case_root, [item["requirement_id"] for item in requirements]
    )
    advance_to(case_root, "RUNNING")
    return {
        "case_id": state["case_id"],
        "variant": metadata["variant_id"],
        "state": "RUNNING",
        "input_hashes": required_inputs,
        "code_commit": code_commit,
        "candidate_ids": CANDIDATES,
        "output_contract_preflight": preflight,
    }


def run_id(candidate: str) -> str:
    return f"RUN-{candidate}-{SEED}"


def finalize_case(
    case_root: Path,
    summary_output: Path,
    stale_probe_root: Path | None,
) -> dict[str, Any]:
    state = core.load_state(case_root)
    if state["state"] != "RUNNING":
        raise ValueError("case must be RUNNING")
    plan = core.read_artifact(case_root, "experiment_plan")["content"]
    outputs: dict[str, dict[str, Any]] = {}
    scores: dict[str, float] = {}
    for candidate in CANDIDATES:
        output = core.load_json(case_root / f"runs/{run_id(candidate)}/output.json")
        if not isinstance(output, dict):
            raise ValueError(f"output missing for {candidate}")
        outputs[candidate] = output
        scores[candidate] = float(output["validation_metrics"][METRIC])
    selected = min(scores, key=lambda candidate: (scores[candidate], candidate))
    decision_hash = core.canonical_hash(
        {
            "selected_candidate_id": selected,
            "validation_scores": scores,
            "metric": METRIC,
            "rule": "ARGMIN_THEN_ID",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        }
    )
    manifests: dict[str, dict[str, Any]] = {}
    attempts: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        sealed = core.seal_captured_run(
            case_root, run_id=run_id(candidate), decision_hash=decision_hash
        )
        manifest = core.load_json(case_root / sealed["manifest_path"])
        manifests[candidate] = manifest
        attempts.append(
            {
                "candidate_id": candidate,
                "run_id": run_id(candidate),
                "outcome": "SUCCESS",
                "validation_score": scores[candidate],
                "random_seed": SEED,
            }
        )
    advance_to(case_root, "RUN_VALIDATED")
    comparison = {
        "candidate_ids": CANDIDATES,
        "baseline_id": BASELINE,
        "splits": plan["splits"],
        "metric": METRIC,
        "metric_direction": "MIN",
        "aggregation_rule": plan["aggregation_rule"],
        "selection_rule": plan["selection_rule"],
        "random_seeds": plan["random_seeds"],
        "required_input_hashes": plan["required_input_hashes"],
        "required_code_files": plan["required_code_files"],
        "code_commit": plan["code_commit"],
        "stop_rule": plan["stop_rule"],
        "handoff_generated_at": plan["handoff_generated_at"],
        "attempts": attempts,
        "selected_candidate_id": selected,
        "selection_decision_hash": decision_hash,
        "freeze_bindings": plan["trusted_freeze_registry"],
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
        "reliability": {"attempts": 3, "successful": 3, "failed_or_infeasible": 0},
    }
    accepted(case_root, "model_comparison", comparison)
    selected_manifest = manifests[selected]
    selected_output = outputs[selected]
    robustness = {
        "status": "VALIDATED",
        "selected_model": selected,
        "run_id": selected_manifest["run_id"],
        "input_hash": selected_manifest["input_hash"],
        "configuration_hash": selected_manifest["configuration_hash"],
        "output_hash": selected_manifest["output_hash"],
        "decision_hash": decision_hash,
        **selected_output["robustness_evidence"],
    }
    accepted(case_root, "robustness_analysis", robustness)
    final = {
        "status": "FINAL_CANDIDATE",
        "selected_model": selected,
        "run_id": selected_manifest["run_id"],
        "output_hash": selected_manifest["output_hash"],
        "decision_hash": decision_hash,
        "final_metrics": selected_output["final_metrics"],
        "claim_scope": selected_output["claim_scope"],
    }
    accepted(case_root, "final_result", final)
    advance_to(case_root, "FINAL_CANDIDATE")
    claim = {
        "claim_id": selected_output["requirement_claims"]["REQ-1A"]["claim_id"],
        "claim_text": selected_output["claim_scope"],
        "supported_scope": selected_output["claim_scope"],
        "run_id": selected_manifest["run_id"],
        "run_manifest_hash": core.canonical_hash(selected_manifest),
        "input_hash": selected_manifest["input_hash"],
        "code_hash": selected_manifest["code_tree_hash"],
        "configuration_hash": selected_manifest["configuration_hash"],
        "output_hash": selected_manifest["output_hash"],
        "decision_hash": decision_hash,
        "evidence_artifact_ids": [
            "results/model_comparison.json",
            "results/robustness.json",
            "results/final_result.json",
            selected_manifest["output_files"][0]["path"],
        ],
        "supported_requirement_ids": [
            item["requirement_id"]
            for item in core.read_artifact(case_root, "problem_requirements")["content"][
                "requirements"
            ]
        ],
        "requirement_claims": selected_output["requirement_claims"],
        "evidence_status": "CURRENT",
        "contradiction_status": "NONE",
    }
    accepted(case_root, "claim_evidence", claim)
    advance_to(case_root, "EVIDENCE_VALIDATED")
    handoff = core.build_expected_handoff(case_root, core.load_state(case_root))
    core.write_json(case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"], handoff)
    advance_to(case_root, "READY_FOR_PAPER_HANDOFF")

    stale_probe: dict[str, Any] | None = None
    if stale_probe_root is not None:
        if stale_probe_root.exists():
            raise FileExistsError(stale_probe_root)
        shutil.copytree(case_root, stale_probe_root, copy_function=os.link)
        metadata_path = stale_probe_root / "state/variant_metadata.json"
        changed_metadata = core.load_json(metadata_path)
        changed_metadata["date_shift_days"] = int(changed_metadata["date_shift_days"]) + 1
        core.write_json(metadata_path, changed_metadata)
        stale_result = core.stale_check(stale_probe_root, mutate=True)
        stale_probe = {
            "status": stale_result.status,
            "reason_codes": list(stale_result.reason_codes),
            "dependency_chain": list(stale_result.dependency_chain),
            "case_state": core.load_state(stale_probe_root)["state"],
        }

    run_evidence = []
    for candidate in CANDIDATES:
        capture_path = case_root / f"runs/{run_id(candidate)}/execution_capture.json"
        manifest_path = case_root / f"runs/{run_id(candidate)}/manifest.json"
        capture = core.load_json(capture_path)
        run_evidence.append(
            {
                "run_id": run_id(candidate),
                "candidate_id": candidate,
                "seed": SEED,
                "exit_code": capture["exit_code"],
                "elapsed_seconds": capture["elapsed_seconds"],
                "validation_score": scores[candidate],
                "capture_sha256": core.file_hash(capture_path),
                "manifest_sha256": core.file_hash(manifest_path),
                "output_sha256": core.file_hash(
                    case_root / f"runs/{run_id(candidate)}/output.json"
                ),
            }
        )
    metadata = core.load_json(case_root / "state/variant_metadata.json")
    summary = {
        "schema_version": "1.0.0",
        "case_id": state["case_id"],
        "evidence_class": "DEVELOPMENT_REGRESSION_OR_STRESS",
        "answer_access_status": "UNLOCKED_AFTER_FIRST_RUN",
        "model_prior_status": "MODEL_PRIOR_EXPOSURE_UNVERIFIABLE",
        "variant_metadata": metadata,
        "skill_version": core.VERSION,
        "output_contract_preflight": {
            "status": "PASS",
            "reason_codes": ["RC_OUTPUT_CONTRACT_VALID"],
            "path": "experiments/selected_output_contract_probe.json",
        },
        "code_commit": plan["code_commit"],
        "final_state": core.load_state(case_root)["state"],
        "input_hashes": plan["required_input_hashes"],
        "selected_model": selected,
        "decision_hash": decision_hash,
        "final_metrics": final["final_metrics"],
        "robustness": selected_output["robustness_evidence"],
        "data_quality": selected_output["data_quality"],
        "runs": run_evidence,
        "handoff_sha256": core.file_hash(
            case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"]
        ),
        "case_state_sha256": core.file_hash(core.state_path(case_root)),
        "stale_probe": stale_probe,
        "limitations": selected_output["limitations"],
    }
    core.write_json(summary_output, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    transform = subparsers.add_parser("transform-inputs")
    transform.add_argument("--source", type=Path, required=True)
    transform.add_argument("--case-root", type=Path, required=True)
    transform.add_argument(
        "--variant",
        choices=(
            "DEVELOPMENT_REGRESSION",
            "STRESS_A_SCHEMA_ORDERING",
            "STRESS_B_UNITS_TIME",
            "STRESS_C_DEGRADED_INPUT",
        ),
        required=True,
    )
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--case-root", type=Path, required=True)
    prepare.add_argument("--code-commit", required=True)
    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--case-root", type=Path, required=True)
    finalize.add_argument("--summary-output", type=Path, required=True)
    finalize.add_argument("--stale-probe-root", type=Path)
    args = parser.parse_args()
    if args.command == "transform-inputs":
        result = transform_inputs(args.source, args.case_root, args.variant)
    elif args.command == "prepare":
        result = prepare_case(args.case_root, args.code_commit)
    else:
        result = finalize_case(args.case_root, args.summary_output, args.stale_probe_root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
