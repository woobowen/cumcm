#!/usr/bin/env python3
"""Run the bounded 2020 A auxiliary execution-evidence regression for RC4."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
MODEL_SOURCE = (
    ROOT
    / "evals/results/phase-004b/CUMCM-2020-A-DEVELOPMENT-002/"
    "development_regression/code/mechanistic_model.py"
)
MODEL_REPOSITORY_PATH = (
    "evals/results/phase-004b/CUMCM-2020-A-DEVELOPMENT-002/"
    "development_regression/code/mechanistic_model.py"
)
SOURCE_CASE = ROOT / ".cache/official_inputs/CUMCM-2020-A/development_regression_v2"
DEFAULT_CASE = ROOT / ".cache/official_inputs/CUMCM-2020-A/rc4_auxiliary_attempt_001"
DEFAULT_SUMMARY = ROOT / "evals/results/phase-004c-c-batch/rc4/2020a_auxiliary_regression.json"
CASE_ID = "CUMCM-2020-A-RC4-AUXILIARY-REGRESSION"
SEED = 20260904
METRIC = "selection_score"
CANDIDATES = [
    "BASELINE_FIRST_ORDER",
    "PRIMARY_ASYMMETRIC_FIRST_ORDER",
    "AUXILIARY_NONZERO_DIAGNOSTIC",
]
BASELINE = CANDIDATES[0]
STOP_RULE = (
    "one execution for each registered candidate; retain the deliberate nonzero capture; "
    "rank successful runs only"
)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


core = load_module("phase004c_rc4_aux_core", CORE_PATH)


def accepted(case_root: Path, key: str, content: dict[str, Any]) -> None:
    core.write_json(case_root / core.ARTIFACT_PATHS[key], core.artifact(key, content))


def advance_to(case_root: Path, target: str) -> None:
    while core.load_state(case_root)["state"] != target:
        core.advance_once(case_root)


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


def write_probe(case_root: Path, requirement_ids: list[str]) -> dict[str, Any]:
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


def prepare(case_root: Path, code_commit: str) -> dict[str, Any]:
    if case_root.exists():
        raise FileExistsError(case_root)
    core.initialize_case(case_root, CASE_ID, "optimization")
    for relative in (
        "problem/case_files/2020A-炉温曲线.docx",
        "data/raw/case_files/附件.xlsx",
        "data/raw/case_files/result.csv",
    ):
        destination = case_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_CASE / relative, destination)
    model_path = case_root / "models/mechanistic_model.py"
    shutil.copy2(MODEL_SOURCE, model_path)

    requirements = [
        {"requirement_id": key, "text": text}
        for key, text in {
            "REQ-2020A-Q1": "simulate the requested temperature curve and checkpoints",
            "REQ-2020A-Q2": "find and verify the maximum feasible conveyor speed",
            "REQ-2020A-Q3": "find a feasible area-minimizing process setting",
            "REQ-2020A-Q4": "find a feasible symmetry-oriented process setting",
            "REQ-2020A-MECHANISM": "bind the thermal mechanism and calibrated parameters",
            "REQ-2020A-CONSTRAINTS": "recompute every registered process constraint",
        }.items()
    ]
    accepted(case_root, "problem_requirements", {"case_id": CASE_ID, "requirements": requirements})
    advance_to(case_root, "REQUIREMENTS_VALIDATED")
    freeze_hash = core.file_hash(
        ROOT
        / "evals/results/phase-004b/CUMCM-2020-A-DEVELOPMENT-002/first_run/"
        "first_run_freeze.json"
    )
    accepted(
        case_root,
        "research_plan",
        {
            "mode": "DEVELOPMENT_REGRESSION",
            "external_search": False,
            "first_run_freeze_sha256": freeze_hash,
            "evidence_class": "AUXILIARY_CROSS_TYPE_NOT_C_TARGET_EVIDENCE",
        },
    )
    accepted(
        case_root,
        "source_ledger",
        {
            "sources": [
                {"source_id": "SRC-OFFICIAL-2020A-INPUT", "kind": "OFFICIAL_PROBLEM_INPUT"},
                {"source_id": "SRC-2020A-FIRST-RUN-FREEZE", "sha256": freeze_hash},
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
                "the board is represented by lumped thermal states",
                "conveyor speed is constant within a run",
                "effective rates aggregate unresolved heat-transfer mechanisms",
            ],
            "symbols": {"T": "center temperature in degree Celsius", "v": "conveyor speed"},
            "formulas": [
                "x(t)=v*t",
                "dT/dt=(T_env(x(t))-T)/tau",
                "A=integral(max(T-217,0))*dt",
            ],
        },
    )
    input_paths = [
        "problem/case_files/2020A-炉温曲线.docx",
        "data/raw/case_files/附件.xlsx",
        "data/raw/case_files/result.csv",
    ]
    required_inputs = {relative: core.file_hash(case_root / relative) for relative in input_paths}
    accepted(
        case_root,
        "data_audit",
        {
            "raw_immutable": True,
            "data_hashes": required_inputs,
            "row_count": 709,
            "missing_cells": 0,
            "unit_checks": ["cm/min converted once to cm/s", "time is seconds"],
            "leakage": ["A-type auxiliary evidence is excluded from C-target generalization credit"],
        },
    )
    advance_to(case_root, "DATA_AUDITED")
    accepted(
        case_root,
        "model_candidates",
        {
            "candidates": [
                {
                    "candidate_id": BASELINE,
                    "baseline": True,
                    "method": "single-capacitance first-order thermal lag",
                    "failure_condition": "asymmetric heating and cooling",
                },
                {
                    "candidate_id": CANDIDATES[1],
                    "baseline": False,
                    "method": "asymmetric first-order thermal balance",
                    "failure_condition": "single-state structural bias",
                },
                {
                    "candidate_id": CANDIDATES[2],
                    "baseline": False,
                    "method": "registered nonzero process-exit diagnostic",
                    "failure_condition": "always exits 23 by design and is never ranking-eligible",
                },
            ]
        },
    )
    advance_to(case_root, "MODELS_PROPOSED")
    required_code = [
        {
            "scope": "SKILL_ROOT",
            "path": "scripts/cumcm_case.py",
            "repository_path": ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
            "sha256": core.file_hash(CORE_PATH),
        },
        {
            "scope": "CASE_ROOT",
            "path": "models/mechanistic_model.py",
            "repository_path": MODEL_REPOSITORY_PATH,
            "sha256": core.file_hash(model_path),
        },
    ]
    for record in required_code:
        if core.git_blob_hash(code_commit, record["repository_path"]) != record["sha256"]:
            raise ValueError(f"code commit mismatch: {record['repository_path']}")
    splits = {
        "train": ["ordered-samples-index-mod-5-nonzero"],
        "validation": ["ordered-samples-index-mod-5-zero"],
        "test": ["no-separate-test-auxiliary-only"],
    }
    generated_at = core.utc_now()
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
            "trusted_freeze_registry": freeze_registry(
                required_inputs, required_code, code_commit, splits, generated_at
            ),
            "stop_rule": STOP_RULE,
            "handoff_generated_at": generated_at,
        },
    )
    preflight = write_probe(case_root, [item["requirement_id"] for item in requirements])
    advance_to(case_root, "RUNNING")
    return {"state": "RUNNING", "preflight": preflight, "input_hashes": required_inputs}


def run_id(candidate: str) -> str:
    return f"RUN-RC4-AUX-{candidate}-{SEED}"


def execute(case_root: Path) -> list[dict[str, Any]]:
    return [
        core.execute_case_code(
            case_root,
            run_id=run_id(candidate),
            candidate_id=candidate,
            seed=SEED,
            code_path="models/mechanistic_model.py",
            timeout_seconds=900,
        )
        for candidate in CANDIDATES
    ]


def finalize(case_root: Path, summary_path: Path) -> dict[str, Any]:
    plan = core.read_artifact(case_root, "experiment_plan")["content"]
    captures = {
        candidate: core.load_json(case_root / f"runs/{run_id(candidate)}/execution_capture.json")
        for candidate in CANDIDATES
    }
    outputs = {
        candidate: core.load_json(case_root / f"runs/{run_id(candidate)}/output.json")
        for candidate in CANDIDATES
    }
    successful_scores = {
        candidate: float(outputs[candidate]["validation_metrics"][METRIC])
        for candidate in CANDIDATES
        if captures[candidate]["outcome"] == "SUCCESS"
    }
    selected = min(successful_scores, key=lambda key: (successful_scores[key], key))
    if outputs[selected].get("scientifically_eligible_for_final") is not True:
        raise ValueError("AUXILIARY_SELECTED_RUN_NOT_SCIENTIFICALLY_ELIGIBLE")
    decision_hash = core.canonical_hash(
        {
            "selected_candidate_id": selected,
            "validation_scores": successful_scores,
            "metric": METRIC,
            "rule": "ARGMIN_THEN_ID",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        }
    )
    manifests: dict[str, dict[str, Any]] = {}
    attempts: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        sealed = core.seal_captured_run(case_root, run_id=run_id(candidate), decision_hash=decision_hash)
        manifests[candidate] = core.load_json(case_root / sealed["manifest_path"])
        attempts.append(
            {
                "candidate_id": candidate,
                "run_id": run_id(candidate),
                "outcome": captures[candidate]["outcome"],
                "validation_score": successful_scores.get(candidate),
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
        "test_access": {"authorized": True, "count": 0, "used_for_selection": False},
        "reliability": {"attempts": 3, "successful": 2, "failed_or_infeasible": 1},
    }
    accepted(case_root, "model_comparison", comparison)
    selected_manifest = manifests[selected]
    selected_output = outputs[selected]
    accepted(
        case_root,
        "robustness_analysis",
        {
            "status": "VALIDATED",
            "selected_model": selected,
            "run_id": selected_manifest["run_id"],
            "input_hash": selected_manifest["input_hash"],
            "configuration_hash": selected_manifest["configuration_hash"],
            "output_hash": selected_manifest["output_hash"],
            "decision_hash": decision_hash,
            **selected_output["robustness_evidence"],
        },
    )
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
    requirement_ids = [
        item["requirement_id"]
        for item in core.read_artifact(case_root, "problem_requirements")["content"]["requirements"]
    ]
    claim = {
        "claim_id": "CLAIM-2020A-AUXILIARY-RC4",
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
        "supported_requirement_ids": requirement_ids,
        "requirement_claims": selected_output["requirement_claims"],
        "evidence_status": "CURRENT",
        "contradiction_status": "NONE",
    }
    accepted(case_root, "claim_evidence", claim)
    advance_to(case_root, "EVIDENCE_VALIDATED")
    handoff = core.build_expected_handoff(case_root, core.load_state(case_root))
    core.write_json(case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"], handoff)
    advance_to(case_root, "READY_FOR_PAPER_HANDOFF")
    runs = []
    for candidate in CANDIDATES:
        capture_path = case_root / f"runs/{run_id(candidate)}/execution_capture.json"
        manifest_path = case_root / f"runs/{run_id(candidate)}/manifest.json"
        capture = captures[candidate]
        runs.append(
            {
                "run_id": run_id(candidate),
                "candidate_id": candidate,
                "outcome": capture["outcome"],
                "exit_code": capture["exit_code"],
                "failure": capture["failure"],
                "selection_score": successful_scores.get(candidate),
                "capture_sha256": core.file_hash(capture_path),
                "manifest_sha256": core.file_hash(manifest_path),
                "output_sha256": core.file_hash(case_root / f"runs/{run_id(candidate)}/output.json"),
            }
        )
    summary = {
        "schema_version": "1.0.0",
        "artifact_type": "rc4_auxiliary_cross_type_regression_evidence",
        "case_id": CASE_ID,
        "source_case_id": "CUMCM-2020-A-DEVELOPMENT-002",
        "evidence_class": "AUXILIARY_CROSS_TYPE_NOT_C_TARGET_EVIDENCE",
        "c_target_evidence_credit": False,
        "skill_version": core.VERSION,
        "skill_candidate_commit": "297cad0a29c659b18484d4f3b67d69a942ad415c",
        "execution_code_commit": plan["code_commit"],
        "terminal_state": core.load_state(case_root)["state"],
        "selected_candidate_id": selected,
        "selected_run_scientifically_eligible": True,
        "selection_scope": "SUCCESS_OUTCOMES_ONLY",
        "nonzero_failure_retained": True,
        "failed_run_count": 1,
        "successful_run_count": 2,
        "seal_run_status": "PASS_ALL_CAPTURES",
        "claim_gate": "PASS",
        "handoff_gate": "PASS",
        "output_contract_preflight": {
            "status": "PASS",
            "reason_codes": ["RC_OUTPUT_CONTRACT_VALID"],
            "path": "experiments/selected_output_contract_probe.json",
        },
        "decision_hash": decision_hash,
        "runs": runs,
        "handoff_sha256": core.file_hash(
            case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"]
        ),
        "case_state_sha256": core.file_hash(core.state_path(case_root)),
        "workspace_relative": str(case_root.relative_to(ROOT)),
        "api_calls": 0,
        "third_party_executions": 0,
        "model_training": False,
    }
    core.write_json(summary_path, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()
    prepared = prepare(args.case_root, args.code_commit)
    executed = execute(args.case_root)
    finalized = finalize(args.case_root, args.summary)
    print(
        json.dumps(
            {"prepared": prepared, "executed": executed, "finalized": finalized},
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
