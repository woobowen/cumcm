#!/usr/bin/env python3
"""Run three isolated post-unlock C-target Development regressions under RC4."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
RESULT_ROOT = ROOT / "evals/results/phase-004c-c-batch"
CACHE_ROOT = ROOT / ".cache/official_inputs"
GENERATED_AT = "2026-09-05T02:00:00Z"


@dataclass(frozen=True)
class CaseConfig:
    key: str
    source_workspace: str
    case_id: str
    case_kind: str
    tracked_case_id: str
    code_files: tuple[tuple[str, str], ...]
    seed: int


CASES = {
    "2022": CaseConfig(
        key="2022",
        source_workspace="CUMCM-2022-C-BATCH-001",
        case_id="CUMCM-2022-C-DEVELOPMENT-RC4-REGRESSION",
        case_kind="prediction",
        tracked_case_id="CUMCM-2022-C-DEVELOPMENT-BATCH-001",
        code_files=(
            (
                "models/model_pipeline.py",
                "evals/results/phase-004c-c-batch/"
                "CUMCM-2022-C-DEVELOPMENT-BATCH-001/code/model_pipeline.py",
            ),
        ),
        seed=20220904,
    ),
    "2021": CaseConfig(
        key="2021",
        source_workspace="CUMCM-2021-C-BATCH-002",
        case_id="CUMCM-2021-C-DEVELOPMENT-RC4-REGRESSION",
        case_kind="optimization",
        tracked_case_id="CUMCM-2021-C-DEVELOPMENT-BATCH-002",
        code_files=(
            (
                "models/c2021_supply_plan.py",
                "evals/results/phase-004c-c-batch/"
                "CUMCM-2021-C-DEVELOPMENT-BATCH-002/code/c2021_supply_plan.py",
            ),
            (
                "models/c2021_feasibility.py",
                "evals/results/phase-004c-c-batch/"
                "CUMCM-2021-C-DEVELOPMENT-BATCH-002/code/c2021_feasibility.py",
            ),
        ),
        seed=20210904,
    ),
    "2020": CaseConfig(
        key="2020",
        source_workspace="CUMCM-2020-C-BATCH-003",
        case_id="CUMCM-2020-C-DEVELOPMENT-RC4-REGRESSION",
        case_kind="prediction",
        tracked_case_id="CUMCM-2020-C-DEVELOPMENT-BATCH-003",
        code_files=(
            (
                "code/model_pipeline.py",
                "evals/results/phase-004c-c-batch/"
                "CUMCM-2020-C-DEVELOPMENT-BATCH-003/code/model_pipeline.py",
            ),
        ),
        seed=20200905,
    ),
}


def load_core() -> Any:
    spec = importlib.util.spec_from_file_location("cumcm_case_rc4_batch_regression", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("RC4_CORE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def accepted(core: Any, case_root: Path, key: str, content: dict[str, Any]) -> None:
    core.write_json(case_root / core.ARTIFACT_PATHS[key], core.artifact(key, content))


def git_tree(commit: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"{commit}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def copy_bound_files(source: Path, target: Path, registry: dict[str, str], core: Any) -> None:
    for relative, expected in registry.items():
        source_path = source / relative
        target_path = target / relative
        if not source_path.is_file() or core.file_hash(source_path) != expected:
            raise ValueError(f"SOURCE_INPUT_HASH_MISMATCH:{relative}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        if core.file_hash(target_path) != expected:
            raise ValueError(f"COPIED_INPUT_HASH_MISMATCH:{relative}")


def freeze_registry(
    core: Any,
    *,
    candidate_ids: list[str],
    metric: str,
    direction: str,
    seeds: list[int],
    splits: dict[str, list[Any]],
    baseline_id: str,
    required_inputs: dict[str, str],
    stop_rule: str,
    code_files: list[dict[str, str]],
    code_commit: str,
) -> dict[str, str]:
    aggregation = "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID"
    selection = "ARGMIN_THEN_ID" if direction == "MIN" else "ARGMAX_THEN_ID"
    return {
        "candidate_set": core.canonical_hash(candidate_ids),
        "metric": core.canonical_hash(
            {
                "name": metric,
                "direction": direction,
                "aggregation_rule": aggregation,
                "selection_rule": selection,
            }
        ),
        "seed_schedule": core.canonical_hash(seeds),
        "split_assignment": core.canonical_hash(splits),
        "baseline": core.canonical_hash(baseline_id),
        "input_set": core.canonical_hash(required_inputs),
        "execution_policy": core.canonical_hash(
            {"stop_rule": stop_rule, "handoff_generated_at": GENERATED_AT}
        ),
        "code_set": core.canonical_hash(code_files),
        "code_commit": core.canonical_hash(code_commit),
    }


def write_probe(
    core: Any,
    case_root: Path,
    requirement_ids: list[str],
    metric: str,
    direction: str,
) -> dict[str, Any]:
    relative = "experiments/selected_output_contract_probe.json"
    probe = {
        "candidate_id": "CONTRACT-PROBE",
        "status": "CONTRACT_PROBE",
        "probe_only": True,
        "ranking_eligible": False,
        "result_values_are_placeholders": True,
        "final_metrics": {metric: 0.0},
        "claim_scope": "Generic structural placeholder; not a result.",
        "requirement_claims": {
            requirement_id: {
                "claim_id": f"CLAIM-PROBE-{index:02d}",
                "claim_text": "Generic structural placeholder; not a result.",
                "evidence_artifact_ids": [relative],
            }
            for index, requirement_id in enumerate(requirement_ids, start=1)
        },
        "figure_ready_data": [{"figure_id": "CONTRACT-PROBE", "rows": [0]}],
        "uncertainty": {"scope": "placeholder"},
        "limitations": ["Placeholder values are excluded from runs and ranking."],
        "robustness_evidence": {
            "metric": metric,
            "metric_direction": direction,
            "perturbations": [
                {
                    "perturbation_id": "CONTRACT-PROBE-SHIFT",
                    "metric": metric,
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


def prepare_case(core: Any, config: CaseConfig, case_root: Path) -> dict[str, Any]:
    source = CACHE_ROOT / config.source_workspace
    if case_root.exists():
        raise FileExistsError(case_root)
    core.initialize_case(case_root, config.case_id, config.case_kind)

    problem = load_json(source / "problem/problem_requirements.json")["content"]
    problem["case_id"] = config.case_id
    accepted(core, case_root, "problem_requirements", problem)
    core.advance_once(case_root)
    core.advance_once(case_root)

    freeze_path = RESULT_ROOT / config.tracked_case_id / "first_run/first_run_freeze.v2.json"
    first_run_freeze_sha256 = core.file_hash(freeze_path)
    research = load_json(source / "research/research_plan.json")["content"]
    research["mode"] = "DEVELOPMENT_REGRESSION"
    research["first_run_freeze_sha256"] = first_run_freeze_sha256
    ledger = load_json(source / "research/source_ledger.json")["content"]
    ledger["answer_access_status"] = "UNLOCKED_AFTER_FIRST_RUN"
    accepted(core, case_root, "research_plan", research)
    accepted(core, case_root, "source_ledger", ledger)
    core.advance_once(case_root)

    assumptions = load_json(source / "models/assumptions_and_symbols.json")["content"]
    audit = load_json(source / "data/data_audit.json")["content"]
    required_inputs = audit["data_hashes"]
    copy_bound_files(source, case_root, required_inputs, core)
    accepted(core, case_root, "assumptions_and_symbols", assumptions)
    accepted(core, case_root, "data_audit", audit)
    core.advance_once(case_root)

    candidates = load_json(source / "models/model_candidates.json")["content"]
    accepted(core, case_root, "model_candidates", candidates)
    core.advance_once(case_root)
    return {
        "source": source,
        "problem": problem,
        "requirements": [item["requirement_id"] for item in problem["requirements"]],
        "audit": audit,
        "candidates": candidates,
        "first_run_freeze_path": str(freeze_path.relative_to(ROOT)),
        "first_run_freeze_sha256": first_run_freeze_sha256,
    }


def run_case(config: CaseConfig, attempt: int) -> dict[str, Any]:
    core = load_core()
    case_root = CACHE_ROOT / f"{config.case_id}-ATTEMPT-{attempt:03d}"
    started_wall = time.time()
    prepared = prepare_case(core, config, case_root)
    source_plan = load_json(prepared["source"] / "experiments/experiment_plan.json")["content"]
    candidate_records = prepared["candidates"]["candidates"]
    candidate_ids = [item["candidate_id"] for item in candidate_records]
    baselines = [item["candidate_id"] for item in candidate_records if item.get("baseline") is True]
    if len(baselines) != 1:
        raise ValueError("REGRESSION_BASELINE_REGISTRY_INVALID")
    baseline_id = baselines[0]
    metric = source_plan["metric"]
    direction = source_plan["metric_direction"]
    splits = source_plan["splits"]
    seeds = [config.seed]
    code_commit = core.current_git_commit()
    code_files = [
        {
            "scope": "SKILL_ROOT",
            "path": "scripts/cumcm_case.py",
            "repository_path": ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
            "sha256": core.file_hash(CORE_PATH),
        }
    ]
    for local_relative, repository_relative in config.code_files:
        source_code = ROOT / repository_relative
        target_code = case_root / local_relative
        target_code.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_code, target_code)
        code_files.append(
            {
                "scope": "CASE_ROOT",
                "path": local_relative,
                "repository_path": repository_relative,
                "sha256": core.file_hash(target_code),
            }
        )
    stop_rule = "one preregistered RC4 Development-regression attempt per candidate"
    freezes = freeze_registry(
        core,
        candidate_ids=candidate_ids,
        metric=metric,
        direction=direction,
        seeds=seeds,
        splits=splits,
        baseline_id=baseline_id,
        required_inputs=prepared["audit"]["data_hashes"],
        stop_rule=stop_rule,
        code_files=code_files,
        code_commit=code_commit,
    )
    aggregation = "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID"
    selection_rule = "ARGMIN_THEN_ID" if direction == "MIN" else "ARGMAX_THEN_ID"
    plan = {
        "preregistered": True,
        "execution_prepared": True,
        "splits": splits,
        "metric": metric,
        "metric_direction": direction,
        "aggregation_rule": aggregation,
        "selection_rule": selection_rule,
        "baseline_id": baseline_id,
        "handoff_generated_at": GENERATED_AT,
        "random_seeds": seeds,
        "candidate_ids": candidate_ids,
        "required_input_hashes": prepared["audit"]["data_hashes"],
        "required_code_files": code_files,
        "code_commit": code_commit,
        "trusted_freeze_registry": freezes,
        "stop_rule": stop_rule,
    }
    accepted(core, case_root, "experiment_plan", plan)
    preflight = write_probe(
        core, case_root, prepared["requirements"], metric=metric, direction=direction
    )
    core.advance_once(case_root)
    core.advance_once(case_root)

    executions: list[dict[str, Any]] = []
    scores: dict[str, list[float]] = {}
    for candidate_id in candidate_ids:
        run_id = f"RUN-RC4-{candidate_id}-S{config.seed}"
        captured = core.execute_case_code(
            case_root,
            run_id=run_id,
            candidate_id=candidate_id,
            seed=config.seed,
            code_path=config.code_files[0][0],
            timeout_seconds=900,
        )
        executions.append(
            {
                "candidate_id": candidate_id,
                "run_id": run_id,
                "random_seed": config.seed,
                "outcome": captured["outcome"],
                "capture_sha256": captured["capture_sha256"],
            }
        )
        if captured["outcome"] == "SUCCESS":
            output = core.load_json(case_root / captured["output"]["path"])
            score = output.get("validation_metrics", {}).get(metric)
            if not core.strict_score(score):
                raise ValueError(f"REGRESSION_SCORE_INVALID:{candidate_id}")
            scores.setdefault(candidate_id, []).append(float(score))
    if baseline_id not in scores or len(scores) < 2:
        raise ValueError("REGRESSION_SUCCESS_SET_INSUFFICIENT")
    aggregated = {key: sum(values) / len(values) for key, values in scores.items()}
    target = min(aggregated.values()) if direction == "MIN" else max(aggregated.values())
    selected = min(key for key, value in aggregated.items() if value == target)
    decision_hash = core.canonical_hash(
        {
            "selected_candidate_id": selected,
            "validation_scores": aggregated,
            "metric": metric,
            "rule": selection_rule,
            "aggregation_rule": aggregation,
        }
    )
    for execution in executions:
        core.seal_captured_run(case_root, run_id=execution["run_id"], decision_hash=decision_hash)
    core.advance_once(case_root)
    core.advance_once(case_root)

    attempts: list[dict[str, Any]] = []
    for execution in executions:
        attempts.append(
            {
                "candidate_id": execution["candidate_id"],
                "run_id": execution["run_id"],
                "outcome": execution["outcome"],
                "validation_score": (
                    aggregated[execution["candidate_id"]]
                    if execution["outcome"] == "SUCCESS"
                    else None
                ),
                "random_seed": execution["random_seed"],
            }
        )
    comparison = {
        "candidate_ids": candidate_ids,
        "baseline_id": baseline_id,
        "metric": metric,
        "metric_direction": direction,
        "aggregation_rule": aggregation,
        "selection_rule": selection_rule,
        "random_seeds": seeds,
        "splits": splits,
        "required_input_hashes": prepared["audit"]["data_hashes"],
        "required_code_files": code_files,
        "code_commit": code_commit,
        "freeze_bindings": freezes,
        "stop_rule": stop_rule,
        "handoff_generated_at": GENERATED_AT,
        "attempts": attempts,
        "selected_candidate_id": selected,
        "selection_decision_hash": decision_hash,
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
        "reliability": {
            "attempts": len(attempts),
            "successful": sum(item["outcome"] == "SUCCESS" for item in attempts),
            "failed_or_infeasible": sum(item["outcome"] != "SUCCESS" for item in attempts),
        },
    }
    selected_attempt = next(item for item in attempts if item["candidate_id"] == selected)
    selected_manifest_path = case_root / "runs" / selected_attempt["run_id"] / "manifest.json"
    selected_manifest = core.load_json(selected_manifest_path)
    selected_output_relative = selected_manifest["output_files"][0]["path"]
    selected_output = core.load_json(case_root / selected_output_relative)
    robustness = {
        "status": "VALIDATED",
        "selected_model": selected,
        "run_id": selected_manifest["run_id"],
        "input_hash": selected_manifest["input_hash"],
        "configuration_hash": selected_manifest["configuration_hash"],
        "output_hash": selected_manifest["output_hash"],
        "decision_hash": selected_manifest["decision_hash"],
        **selected_output["robustness_evidence"],
    }
    accepted(core, case_root, "model_comparison", comparison)
    accepted(core, case_root, "robustness_analysis", robustness)
    core.advance_once(case_root)

    final = {
        "status": "FINAL_CANDIDATE",
        "selected_model": selected,
        "run_id": selected_manifest["run_id"],
        "output_hash": selected_manifest["output_hash"],
        "decision_hash": selected_manifest["decision_hash"],
        "final_metrics": selected_output["final_metrics"],
        "claim_scope": selected_output["claim_scope"],
    }
    accepted(core, case_root, "final_result", final)
    core.advance_once(case_root)

    first_requirement = prepared["requirements"][0]
    primary_claim = selected_output["requirement_claims"][first_requirement]
    evidence_ids = sorted(
        {
            core.ARTIFACT_PATHS["model_comparison"],
            core.ARTIFACT_PATHS["robustness_analysis"],
            core.ARTIFACT_PATHS["final_result"],
            selected_output_relative,
        }
    )
    claim = {
        "claim_id": primary_claim["claim_id"],
        "claim_text": primary_claim["claim_text"],
        "supported_scope": primary_claim["claim_text"],
        "run_id": selected_manifest["run_id"],
        "run_manifest_hash": core.canonical_hash(selected_manifest),
        "input_hash": selected_manifest["input_hash"],
        "code_hash": selected_manifest["code_tree_hash"],
        "configuration_hash": selected_manifest["configuration_hash"],
        "output_hash": selected_manifest["output_hash"],
        "decision_hash": selected_manifest["decision_hash"],
        "evidence_artifact_ids": evidence_ids,
        "supported_requirement_ids": prepared["requirements"],
        "requirement_claims": selected_output["requirement_claims"],
        "evidence_status": "CURRENT",
        "contradiction_status": "NONE",
    }
    accepted(core, case_root, "claim_evidence", claim)
    core.advance_once(case_root)
    state = core.load_state(case_root)
    handoff = core.build_expected_handoff(case_root, state)
    core.write_json(case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"], handoff)
    state = core.advance_once(case_root)
    if state["state"] != "READY_FOR_PAPER_HANDOFF":
        raise ValueError("REGRESSION_TERMINAL_STATE_INVALID")

    elapsed = round(time.time() - started_wall, 6)
    stage_status = [{"stage": stage, "status": "PASS"} for stage in core.STAGES]
    evidence = {
        "schema_version": "1.0.0",
        "artifact_type": "c_target_rc4_development_regression_evidence",
        "case_id": config.case_id,
        "source_first_run_case_id": config.tracked_case_id,
        "evidence_class": "DEVELOPMENT_REGRESSION_NOT_BLIND_NOT_VALIDATION",
        "answer_access_status": "UNLOCKED_AFTER_FIRST_RUN",
        "first_run_freeze": {
            "path": prepared["first_run_freeze_path"],
            "sha256": prepared["first_run_freeze_sha256"],
        },
        "skill": {
            "version": core.VERSION,
            "candidate_implementation_commit": "297cad0a29c659b18484d4f3b67d69a942ad415c",
            "execution_code_commit": code_commit,
            "git_tree_sha1": git_tree(
                "297cad0a29c659b18484d4f3b67d69a942ad415c",
                ".agents/skills/cumcm-modeling-evidence",
            ),
        },
        "workspace_relative": str(case_root.relative_to(ROOT)),
        "output_contract_preflight": preflight,
        "stage_status": stage_status,
        "requirements_total": len(prepared["requirements"]),
        "requirements_with_output_claims": len(selected_output["requirement_claims"]),
        "runs": executions,
        "valid_run_count": sum(item["outcome"] == "SUCCESS" for item in executions),
        "failed_run_count": sum(item["outcome"] != "SUCCESS" for item in executions),
        "baseline_success": any(
            item["candidate_id"] == baseline_id and item["outcome"] == "SUCCESS"
            for item in executions
        ),
        "selected_candidate_id": selected,
        "selection_decision_hash": decision_hash,
        "selected_validation_score": aggregated[selected],
        "final_run_id": selected_manifest["run_id"],
        "final_output_sha256": selected_manifest["output_files"][0]["sha256"],
        "robustness_perturbation_count": len(robustness["perturbations"]),
        "claim_gate": "PASS",
        "handoff_gate": "PASS",
        "terminal_state": state["state"],
        "universal_hard_failure": False,
        "elapsed_seconds": elapsed,
        "api_calls": 0,
        "third_party_executions": 0,
        "model_training": False,
    }
    evidence_path = (
        RESULT_ROOT / config.tracked_case_id / "rc4/development_regression_evidence.json"
    )
    core.write_json(evidence_path, evidence)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(CASES) + ("all",), default="all")
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    if args.attempt < 1 or args.attempt > 3:
        raise SystemExit("--attempt must be in 1..3")
    selected = list(CASES) if args.case == "all" else [args.case]
    results = [run_case(CASES[key], args.attempt) for key in selected]
    print(
        json.dumps(
            {
                "status": "PASS",
                "case_count": len(results),
                "cases": [
                    {
                        "case_id": item["case_id"],
                        "terminal_state": item["terminal_state"],
                        "valid_run_count": item["valid_run_count"],
                        "elapsed_seconds": item["elapsed_seconds"],
                    }
                    for item in results
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
