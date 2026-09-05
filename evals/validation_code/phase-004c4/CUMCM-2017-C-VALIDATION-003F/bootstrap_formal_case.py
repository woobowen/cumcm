#!/usr/bin/env python3
"""Build the answer-sealed RC7 case workspace without running a model."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

CASE_ID = "CUMCM-2017-C-VALIDATION-003F"
CASE_CODE = ("prepare_case.py", "pipeline.py", "independent_checks.py")
METRIC = "REQ2_GROUPED_MAE_PPM"
SEEDS = [17001, 17017, 17033]


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_content(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), dict):
        raise ValueError(f"invalid preparation artifact: {path}")
    return copy.deepcopy(payload["content"])


def accepted(core: Any, case_root: Path, key: str, content: dict[str, Any]) -> None:
    core.write_json(case_root / core.ARTIFACT_PATHS[key], core.artifact(key, content))


def advance_to(core: Any, case_root: Path, target: str) -> None:
    while core.load_state(case_root)["state"] != target:
        core.advance_once(case_root)


def assessment(requirement_id: str, source_id: str) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "data_sufficiency_status": "SUFFICIENT",
        "missing_fields": [],
        "missing_entities": [],
        "missing_time_scope": [],
        "candidate_sources": [source_id],
        "acquisition_cost": "NONE",
        "acquisition_time": "NONE",
        "allowed_substitutions": [],
        "forbidden_substitutions": ["SIMULATION", "ACQUIRED_EMPIRICAL"],
        "affected_downstream_stages": [],
    }


def output_contract_probe(requirement_ids: list[str]) -> dict[str, Any]:
    relative = "experiments/selected_output_contract_probe.json"
    return {
        "candidate_id": "CONTRACT-PROBE",
        "status": "CONTRACT_PROBE",
        "probe_only": True,
        "ranking_eligible": False,
        "result_values_are_placeholders": True,
        "final_metrics": {METRIC: 0.0},
        "claim_scope": "Structural placeholder only; no model result is represented.",
        "requirement_claims": {
            requirement_id: {
                "claim_id": f"CLAIM-PROBE-{index}",
                "claim_text": "Structural placeholder only; no empirical claim is made.",
                "evidence_artifact_ids": [relative],
            }
            for index, requirement_id in enumerate(requirement_ids, start=1)
        },
        "figure_ready_data": [{"figure_id": "STRUCTURAL-PROBE", "series": [0.0]}],
        "uncertainty": {"scope": "PLACEHOLDER"},
        "limitations": ["Placeholder values are excluded from ranking and evidence."],
        "robustness_evidence": {
            "metric": METRIC,
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "STRUCTURAL-PROBE",
                    "metric": METRIC,
                    "result": 0.0,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": ["This contract probe is not an empirical result."],
        },
    }


def build_freezes(
    core: Any,
    candidate_ids: list[str],
    splits: dict[str, list[str]],
    baseline_id: str,
    inputs: dict[str, str],
    stop_rule: str,
    generated_at: str,
    code_files: list[dict[str, str]],
    code_commit: str,
) -> dict[str, str]:
    return {
        "candidate_set": core.canonical_hash(candidate_ids),
        "metric": core.canonical_hash(
            {
                "name": METRIC,
                "direction": "MIN",
                "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
                "selection_rule": "ARGMIN_THEN_ID",
            }
        ),
        "seed_schedule": core.canonical_hash(SEEDS),
        "split_assignment": core.canonical_hash(splits),
        "baseline": core.canonical_hash(baseline_id),
        "input_set": core.canonical_hash(inputs),
        "execution_policy": core.canonical_hash(
            {"stop_rule": stop_rule, "handoff_generated_at": generated_at}
        ),
        "code_set": core.canonical_hash(code_files),
        "code_commit": core.canonical_hash(code_commit),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", required=True, type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--handoff-generated-at", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    case_root = args.case_root.resolve()
    repository_root = args.repository_root.resolve()
    result_root = repository_root / (
        f"evals/results/phase-004c4/fresh_validation/{CASE_ID}/pre_run/preparation"
    )
    code_source = repository_root / (f"evals/validation_code/phase-004c4/{CASE_ID}")
    core = load_module(
        repository_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        "cumcm_2017c_bootstrap_core",
    )
    if core.current_git_commit() != args.code_commit:
        raise ValueError("code commit must be the current checked-out commit")
    if (case_root / "case_state.json").exists():
        raise ValueError("formal case workspace already initialized")
    core.initialize_case(case_root, CASE_ID, "general")

    requirements = load_content(result_root / "problem_requirements.json")
    accepted(core, case_root, "problem_requirements", requirements)
    advance_to(core, case_root, "REQUIREMENTS_VALIDATED")

    accepted(
        core,
        case_root,
        "research_plan",
        {
            "mode": "ANSWER_SEALED_OFFICIAL_INPUT_ONLY",
            "questions": [
                "Can the official Data1 support bounded relation and quality claims?",
                "Which frozen candidate best predicts Data2 concentration by grouped OOS error?",
                "How do frozen sample-size and feature-dimension perturbations change error?",
            ],
            "external_search": False,
            "answer_access_status": "NOT_ACCESSED",
        },
    )
    sources = load_content(result_root / "source_ledger.json")
    accepted(core, case_root, "source_ledger", sources)
    advance_to(core, case_root, "SOURCES_PLANNED")

    accepted(
        core,
        case_root,
        "assumptions_and_symbols",
        load_content(result_root / "assumptions_and_symbols.json"),
    )
    input_relatives = {
        "CUMCM-2017-problem-C.docx": "data/raw/CUMCM-2017-problem-C.docx",
        "Data1.xls": "data/raw/Data1.xls",
        "Data2.xls": "data/raw/Data2.xls",
        "readme.txt": "data/raw/readme.txt",
    }
    expected = load_content(result_root / "data_audit.json")["data_hashes"]
    input_hashes = {relative: expected[name] for name, relative in input_relatives.items()}
    development = case_root / "splits/development_payload.json"
    input_hashes["splits/development_payload.json"] = core.file_hash(development)
    audit = load_content(result_root / "data_audit.json")
    audit["data_hashes"] = input_hashes
    audit["replay_audit_artifact"] = {
        "path": "data/derived/preparation_data_audit.json",
        "sha256": core.file_hash(case_root / "data/derived/preparation_data_audit.json"),
    }
    accepted(core, case_root, "data_audit", audit)
    advance_to(core, case_root, "DATA_AUDITED")

    reqs = requirements["requirements"]
    source_records = sources["sources"]
    source_by_requirement = {
        "REQ-1-DATA1-RELATION-QUALITY": "SRC-OFFICIAL-DATA1",
        "REQ-2-DATA2-CONCENTRATION-MODEL": "SRC-OFFICIAL-DATA2",
        "REQ-3-SAMPLE-SIZE-FEATURE-DIMENSION": "SRC-OFFICIAL-DATA2",
    }
    sufficiency = {
        "contract_version": "data-sufficiency/v1",
        "requirements": reqs,
        "sources": source_records,
        "acquisition_plans": [],
        "source_compositions": [],
        "coverage_mode_by_requirement": {
            requirement_id: {"mode": "SINGLE_SOURCE", "source_id": source_id}
            for requirement_id, source_id in source_by_requirement.items()
        },
        "aggregate_completion_claimed": False,
        "requirement_assessments": [
            assessment(requirement_id, source_id)
            for requirement_id, source_id in source_by_requirement.items()
        ],
    }
    accepted(core, case_root, "data_sufficiency", sufficiency)
    candidates = load_content(result_root / "model_candidates.json")
    accepted(core, case_root, "model_candidates", candidates)
    advance_to(core, case_root, "MODELS_PROPOSED")

    case_code_root = case_root / "code"
    case_code_root.mkdir(parents=True, exist_ok=True)
    for name in CASE_CODE:
        shutil.copyfile(code_source / name, case_code_root / name)
    code_files = [
        {
            "scope": "SKILL_ROOT",
            "path": "scripts/cumcm_case.py",
            "repository_path": ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
            "sha256": core.file_hash(core.SKILL_ROOT / "scripts/cumcm_case.py"),
        }
    ]
    code_files.extend(
        {
            "scope": "CASE_ROOT",
            "path": f"code/{name}",
            "repository_path": (f"evals/validation_code/phase-004c4/{CASE_ID}/{name}"),
            "sha256": core.file_hash(case_code_root / name),
        }
        for name in CASE_CODE
    )
    candidate_ids = [item["candidate_id"] for item in candidates["candidates"]]
    baseline_id = next(
        item["candidate_id"] for item in candidates["candidates"] if item["baseline"] is True
    )
    splits = {
        "train": ["FROZEN_DEVELOPMENT_TRAIN_GROUPS"],
        "validation": ["FROZEN_DEVELOPMENT_LOCO_FOLDS"],
        "test": ["SEALED_ONE_SHOT_GROUPS"],
    }
    stop_rule = (
        "one attempt per candidate and seed; no adaptive retry, tuning, candidate, split, "
        "metric, rubric or output-contract change"
    )
    freezes = build_freezes(
        core,
        candidate_ids,
        splits,
        baseline_id,
        input_hashes,
        stop_rule,
        args.handoff_generated_at,
        code_files,
        args.code_commit,
    )
    accepted(
        core,
        case_root,
        "experiment_plan",
        {
            "preregistered": True,
            "execution_prepared": True,
            "candidate_ids": candidate_ids,
            "baseline_id": baseline_id,
            "metric": METRIC,
            "metric_direction": "MIN",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
            "selection_rule": "ARGMIN_THEN_ID",
            "random_seeds": SEEDS,
            "splits": splits,
            "required_input_hashes": input_hashes,
            "required_code_files": code_files,
            "code_commit": args.code_commit,
            "trusted_freeze_registry": freezes,
            "stop_rule": stop_rule,
            "handoff_generated_at": args.handoff_generated_at,
            "scenario_hash": core.file_hash(development),
        },
    )
    core.write_json(
        case_root / "experiments/selected_output_contract_probe.json",
        output_contract_probe([item["requirement_id"] for item in reqs]),
        overwrite=False,
    )
    advance_to(core, case_root, "RUNNING")
    state = core.load_state(case_root)
    print(
        json.dumps(
            {
                "case_id": CASE_ID,
                "model_run_count": 0,
                "state": state["state"],
                "state_sha256": core.file_hash(case_root / "case_state.json"),
                "trusted_freeze_registry": freezes,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
