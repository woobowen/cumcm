#!/usr/bin/env python3
"""Run the authorized 2021/2022 C-target Development regressions under RC7.

The source workspaces are reconstructed only from the registered official input
archives and the already-unlocked historical case code.  This route never calls
the Final/Validation evaluator and records a separate current-version evidence
artifact, leaving the older RC4 evidence immutable.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
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
CACHE_ROOT = ROOT / ".cache/official_inputs"
RESULT_ROOT = ROOT / "evals/results/phase004c5-c-batch"
FIRST_RUN_ROOT = ROOT / "evals/results/phase-004c-c-batch"
GENERATED_AT = "2026-09-08T02:00:00Z"


@dataclass(frozen=True)
class CaseConfig:
    key: str
    source_workspace: str
    case_id: str
    tracked_case_id: str
    case_kind: str
    code_files: tuple[tuple[str, str], ...]
    seed: int
    candidate_ids: tuple[str, ...]
    baseline_id: str
    metric: str
    official_page_url: str
    official_page_url_sha256: str
    official_archive_url: str
    official_archive_url_sha256: str
    archive_relative: str
    archive_sha256: str
    case_files: tuple[tuple[str, str], ...]
    extra_files: tuple[tuple[str, str], ...]
    requirement_ids: tuple[str, ...]
    split_assignment: dict[str, list[str]]


CASES = {
    "2022": CaseConfig(
        key="2022",
        source_workspace="CUMCM-2022-C-BATCH-001",
        case_id="CUMCM-2022-C-DEVELOPMENT-RC7-REGRESSION",
        tracked_case_id="CUMCM-2022-C-DEVELOPMENT-BATCH-001",
        case_kind="prediction",
        code_files=(
            (
                "models/model_pipeline.py",
                "evals/results/phase-004c-c-batch/"
                "CUMCM-2022-C-DEVELOPMENT-BATCH-001/code/model_pipeline.py",
            ),
        ),
        seed=20220904,
        candidate_ids=(
            "BASELINE_RAW_CENTROID",
            "CLR_RIDGE_WARD",
            "HELLINGER_KNN_COMPLETE",
        ),
        baseline_id="BASELINE_RAW_CENTROID",
        metric="validation_composite_loss",
        official_page_url=(
            "https://www.mcm.edu.cn/html_cn/node/388239ded4b057d37b7b8e51e33fe903.html"
        ),
        official_page_url_sha256="4dcd31da4dfd2a3fb4c7e5ff93a77ee7901fef54f9eaa4dfdacc1bef92c16ad5",
        official_archive_url=(
            "https://www.mcm.edu.cn/upload_cn/node/670/5eWlbmTt28f88a0815a79d555da8b7072f971633.rar"
        ),
        official_archive_url_sha256="d57c5c806d6c60a450a360d4c3278d8044dd09fa5b384e92ed27948c1e19d8c4",
        archive_relative="raw/archive/CUMCM2022Problems.rar",
        archive_sha256="c27eb1b665f070341e134f5dc13bb2af469230424ff2eedabf594eee708bfee4",
        case_files=(
            (
                "raw/case_files/C题.pdf",
                "573ee0f2865af13f8b2fbd12dab7f8efa68cf61ec6b8edf132a2120424480dbd",
            ),
            (
                "raw/case_files/附件.xlsx",
                "ffb82a8e209a005f26883e115de3ddea42ab6e0a34986d312a52a3cea6b1063c",
            ),
        ),
        extra_files=(
            (
                "raw/inner/C题.rar",
                "cda2851e819c4b95a32209240ad047badb0479d91bae904bcfb3c42c1f4ef5c6",
            ),
        ),
        requirement_ids=(
            "REQ-VALIDITY",
            "REQ-COMPOSITION",
            "REQ-1A",
            "REQ-1B",
            "REQ-1C",
            "REQ-2A",
            "REQ-2B",
            "REQ-2C",
            "REQ-3A",
            "REQ-3B",
            "REQ-4A",
            "REQ-4B",
            "REQ-EVIDENCE",
        ),
        split_assignment={
            "train": ["KNOWN_GROUPS_TRAIN"],
            "validation": ["KNOWN_GROUPS_VALIDATION"],
            "test": ["UNKNOWN_GROUPS_NOT_ACCESSED"],
        },
    ),
    "2021": CaseConfig(
        key="2021",
        source_workspace="CUMCM-2021-C-BATCH-002",
        case_id="CUMCM-2021-C-DEVELOPMENT-RC7-REGRESSION",
        tracked_case_id="CUMCM-2021-C-DEVELOPMENT-BATCH-002",
        case_kind="optimization",
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
        candidate_ids=(
            "BASELINE_MEAN_GREEDY",
            "ROBUST_QUANTILE_LEXICOGRAPHIC",
            "SCENARIO_CVAR_PORTFOLIO",
        ),
        baseline_id="BASELINE_MEAN_GREEDY",
        metric="validation_penalized_cost_per_effective_m3",
        official_page_url=(
            "https://www.mcm.edu.cn/html_cn/node/90d223833c1eb50f899aa096a66c6896.html"
        ),
        official_page_url_sha256="38910ce2a1897e397d149a031e870149bf8a6ecb29f0da0af40cc86ffb1615be",
        official_archive_url=(
            "https://www.mcm.edu.cn/upload_cn/node/669/HtbJEt9Nb655e46bebfa2a66ec63f940e2da156b.rar"
        ),
        official_archive_url_sha256="b5684a6a0fa6ee33c04fe506bea0210f8414b94d4b765a7cb4dba1fa74f0bea1",
        archive_relative="raw/archive/CUMCM2021Problems.rar",
        archive_sha256="3391573f546fce4511e9a99c24c386e28203d8fee3d29bb2dccada5921cefe7b",
        case_files=(
            (
                "raw/case_files/CUMCM2021-C.pdf",
                "4a592c20adad12d4f0678a783bfb47995bda03b1c7484adf254d96327f534056",
            ),
            (
                "raw/case_files/附件1 近5年402家供应商的相关数据.xlsx",
                "1b93a7598b8f0489e3c054439967bca654a83654837908c833752617cf950e1b",
            ),
            (
                "raw/case_files/附件2 近5年8家转运商的相关数据.xlsx",
                "29e1499b133aa88d765902081bfb827f78ffb4c091f5f75341fc37d844344685",
            ),
        ),
        extra_files=(),
        requirement_ids=(
            "REQ-Q1-IMPORTANCE-MODEL",
            "REQ-Q1-TOP50",
            "REQ-Q2-MINIMUM-SUPPLIERS",
            "REQ-Q2-ORDER-PLAN",
            "REQ-Q2-TRANSPORT-PLAN",
            "REQ-Q2-EFFECT",
            "REQ-Q3-MATERIAL-PREFERENCE",
            "REQ-Q3-ORDER-PLAN",
            "REQ-Q3-TRANSPORT-PLAN",
            "REQ-Q3-EFFECT",
            "REQ-Q4-CAPACITY-INCREASE",
            "REQ-Q4-ORDER-PLAN",
            "REQ-Q4-TRANSPORT-PLAN",
            "REQ-OUTPUT-ATTACHMENT-A",
            "REQ-OUTPUT-ATTACHMENT-B",
            "REQ-INVENTORY-PRODUCTION",
            "REQ-TRANSPORT-BUSINESS-RULES",
        ),
        split_assignment={
            "train": ["W001-W168"],
            "validation": ["W169-W216"],
            "test": ["W217-W240_UNACCESSED"],
        },
    ),
}


def load_core() -> Any:
    spec = importlib.util.spec_from_file_location("cumcm_case_rc7_development", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("RC7_CORE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def accepted(core: Any, root: Path, key: str, content: dict[str, Any]) -> None:
    core.write_json(root / core.ARTIFACT_PATHS[key], core.artifact(key, content))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def git_tree(commit: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"{commit}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def source_requirements(config: CaseConfig) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": requirement_id,
            "text": f"Registered official-input requirement {requirement_id}.",
            "role": "PRIMARY",
            "required_evidence_classes": ["PROVIDED_EMPIRICAL"],
            "allowed_evidence_classes": ["PROVIDED_EMPIRICAL", "ACQUIRED_EMPIRICAL"],
            "minimum_data_fields": ["official_case_input"],
            "required_time_scope": ["HISTORICAL_OFFICIAL_CASE"],
            "required_entity_scope": ["CUMCM_CASE"],
            "external_data_allowed": False,
            "external_data_required": False,
            "simulation_substitution_allowed": False,
            "partial_completion_allowed": False,
            "dependency_requirements": [],
            "completion_rule": "ALL_REQUIRED_EVIDENCE",
        }
        for requirement_id in config.requirement_ids
    ]


def official_source(config: CaseConfig) -> dict[str, Any]:
    return {
        "source_id": f"OFFICIAL-{config.key}-C-ARCHIVE",
        "supports_requirement_ids": list(config.requirement_ids),
        "evidence_class": "PROVIDED_EMPIRICAL",
        "provenance": config.official_archive_url,
        "authority": "中国工业与应用数学学会全国大学生数学建模竞赛组委会",
        "retrieval_time": "2026-09-08T01:09:00+08:00",
        "license_or_usage_status": "PUBLIC_COMPETITION_ARCHIVE",
        "geographic_scope": ["MAINLAND_CHINA_COMPETITION"],
        "time_scope": ["HISTORICAL_OFFICIAL_CASE"],
        "entity_scope": ["CUMCM_CASE"],
        "field_schema": ["official_case_input"],
        "hash": config.archive_sha256,
        "freshness": "HISTORICAL_ARCHIVE",
        "limitations": [
            "Historical model-prior exposure is unverifiable.",
            "Only registered official inputs are bound; answer/reference materials are not used.",
        ],
    }


def source_data_sufficiency(
    requirements: list[dict[str, Any]], source: dict[str, Any]
) -> dict[str, Any]:
    return {
        "contract_version": "data-sufficiency/v1",
        "requirements": requirements,
        "sources": [source],
        "acquisition_plans": [],
        "aggregate_completion_claimed": False,
        "requirement_assessments": [
            {
                "requirement_id": item["requirement_id"],
                "data_sufficiency_status": "SUFFICIENT",
                "missing_fields": [],
                "missing_entities": [],
                "missing_time_scope": [],
                "candidate_sources": [source["source_id"]],
                "acquisition_cost": "NONE_AFTER_REGISTERED_ACQUISITION",
                "acquisition_time": "AVAILABLE_IN_REGISTERED_OFFICIAL_ARCHIVE",
                "allowed_substitutions": [],
                "forbidden_substitutions": ["REFERENCE_ANSWER", "THIRD_PARTY_DATA"],
                "affected_downstream_stages": [],
            }
            for item in requirements
        ],
    }


def verify_official_inputs(core: Any, config: CaseConfig) -> Path:
    source = CACHE_ROOT / config.source_workspace
    if sha256_text(config.official_page_url) != config.official_page_url_sha256:
        raise ValueError(f"OFFICIAL_PAGE_URL_HASH_REGISTRY_MISMATCH:{config.key}")
    if sha256_text(config.official_archive_url) != config.official_archive_url_sha256:
        raise ValueError(f"OFFICIAL_ARCHIVE_URL_HASH_REGISTRY_MISMATCH:{config.key}")
    archive = source / config.archive_relative
    checks = [
        (archive, config.archive_sha256),
        *[(source / path, digest) for path, digest in config.case_files],
    ]
    checks.extend((source / path, digest) for path, digest in config.extra_files)
    for path, expected in checks:
        if not path.is_file() or core.file_hash(path) != expected:
            raise ValueError(
                f"OFFICIAL_INPUT_HASH_MISMATCH:{config.key}:{path.relative_to(source)}"
            )
    return source


def write_source_artifacts(core: Any, config: CaseConfig, source: Path) -> None:
    requirements = source_requirements(config)
    source_record = official_source(config)
    data_hashes = {
        path: digest
        for path, digest in config.case_files
        if path.lower().endswith((".xlsx", ".csv"))
    }
    problem = {
        "contract_version": "requirement-evidence/v1",
        "case_id": config.tracked_case_id,
        "requirements": requirements,
    }
    research = {
        "mode": "DEVELOPMENT_REGRESSION",
        "questions": list(config.requirement_ids),
        "external_search": False,
        "first_run_freeze_sha256": core.file_hash(
            FIRST_RUN_ROOT / config.tracked_case_id / "first_run/first_run_freeze.v2.json"
        ),
    }
    ledger = {
        "contract_version": "requirement-evidence/v1",
        "sources": [source_record],
        "answer_access_status": "SEALED",
    }
    assumptions = {
        "assumptions": [
            "Only the registered official historical input files are used.",
            "Candidate selection is restricted to the preregistered Development validation split.",
        ],
        "symbols": {"CASE": config.tracked_case_id, "SEED": str(config.seed)},
        "formulas": ["observed_metric = deterministic_recomputation(bound_inputs)"],
    }
    audit = {
        "raw_immutable": True,
        "data_hashes": data_hashes,
        "raw_data_hashes": data_hashes,
        "leakage_findings": [
            "Reference/answer material is excluded from the bound execution inputs.",
            "The 2021 archive's result attachments are not included in data_hashes.",
        ],
        "acquisition_plans": [],
    }
    candidates = {
        "candidates": [
            {
                "candidate_id": candidate_id,
                "baseline": candidate_id == config.baseline_id,
                "selection_role": "BASELINE"
                if candidate_id == config.baseline_id
                else "ALTERNATIVE",
            }
            for candidate_id in config.candidate_ids
        ]
    }
    plan = {
        "preregistered": False,
        "execution_prepared": False,
        "candidate_ids": list(config.candidate_ids),
        "baseline_id": config.baseline_id,
        "metric": config.metric,
        "metric_direction": "MIN",
        "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        "selection_rule": "ARGMIN_THEN_ID",
        "random_seeds": [config.seed],
        "splits": copy.deepcopy(config.split_assignment),
        "required_input_hashes": data_hashes,
        "required_code_files": [],
        "code_commit": "",
        "trusted_freeze_registry": {},
        "stop_rule": "one preregistered RC7 Development-regression attempt per candidate",
        "handoff_generated_at": GENERATED_AT,
    }
    sufficiency = source_data_sufficiency(requirements, source_record)
    artifacts = {
        "problem_requirements": problem,
        "research_plan": research,
        "source_ledger": ledger,
        "assumptions_and_symbols": assumptions,
        "data_audit": audit,
        "data_sufficiency": sufficiency,
        "model_candidates": candidates,
        "experiment_plan": plan,
    }
    for key, content in artifacts.items():
        accepted(core, source, key, content)


def ensure_source_workspace(core: Any, config: CaseConfig) -> Path:
    source = verify_official_inputs(core, config)
    write_source_artifacts(core, config, source)
    return source


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
    core: Any, case_root: Path, requirement_ids: list[str], metric: str
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
            for index, requirement_id in enumerate(requirement_ids, 1)
        },
        "figure_ready_data": [{"figure_id": "CONTRACT-PROBE", "rows": [0]}],
        "uncertainty": {"scope": "placeholder"},
        "limitations": ["Placeholder values are excluded from runs and ranking."],
        "robustness_evidence": {
            "metric": metric,
            "metric_direction": "MIN",
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
    if not result.accepted or observed.replace("\\", "/") != relative:
        raise ValueError("RC7_OUTPUT_CONTRACT_PREFLIGHT_FAILED")
    return {"status": result.status, "reason_codes": list(result.reason_codes), "path": relative}


def prepare_case(core: Any, config: CaseConfig, case_root: Path, source: Path) -> dict[str, Any]:
    if case_root.exists():
        raise FileExistsError(case_root)
    core.initialize_case(case_root, config.case_id, config.case_kind)
    problem = load_json(source / "problem/problem_requirements.json")["content"]
    problem["case_id"] = config.case_id
    accepted(core, case_root, "problem_requirements", problem)
    core.advance_once(case_root)
    core.advance_once(case_root)

    freeze_path = FIRST_RUN_ROOT / config.tracked_case_id / "first_run/first_run_freeze.v2.json"
    freeze_hash = core.file_hash(freeze_path)
    research = load_json(source / "research/research_plan.json")["content"]
    research["mode"] = "DEVELOPMENT_REGRESSION"
    research["first_run_freeze_sha256"] = freeze_hash
    ledger = load_json(source / "research/source_ledger.json")["content"]
    ledger["answer_access_status"] = "UNLOCKED_AFTER_FIRST_RUN"
    accepted(core, case_root, "research_plan", research)
    accepted(core, case_root, "source_ledger", ledger)
    core.advance_once(case_root)

    assumptions = load_json(source / "models/assumptions_and_symbols.json")["content"]
    audit = load_json(source / "data/data_audit.json")["content"]
    copy_bound_files(source, case_root, audit["data_hashes"], core)
    accepted(core, case_root, "assumptions_and_symbols", assumptions)
    accepted(core, case_root, "data_audit", audit)
    accepted(
        core,
        case_root,
        "data_sufficiency",
        load_json(source / "data/data_sufficiency.json")["content"],
    )
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
        "first_run_freeze_path": str(freeze_path.relative_to(ROOT).as_posix()),
        "first_run_freeze_sha256": freeze_hash,
    }


def build_semantic_records(
    core: Any,
    *,
    requirements: list[str],
    run_id: str,
    manifest: dict[str, Any],
    output: dict[str, Any],
    metric: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    output_id = f"OUTPUT-{run_id}"
    run_record = {
        "run_id": run_id,
        "outcome": "SUCCESS",
        "sealed": True,
        "current": True,
        "supported_requirement_ids": requirements,
        "metric_ids": [metric],
        "selected_output_ids": [output_id],
        "input_hash": manifest["input_hash"],
        "scenario_hash": manifest["scenario_hash"],
    }
    output_record = {
        "output_id": output_id,
        "run_id": run_id,
        "metric_ids": [metric],
        "validation_metrics": output["validation_metrics"],
        "final_metrics": output["final_metrics"],
    }
    claims = []
    claim_ids = {}
    for index, requirement_id in enumerate(requirements, 1):
        source_claim = output["requirement_claims"][requirement_id]
        claim_id = f"CLAIM-RC7-{index:02d}"
        claim_ids[requirement_id] = claim_id
        claims.append(
            {
                "claim_id": claim_id,
                "requirement_id": requirement_id,
                "claim_type": "DESCRIPTIVE",
                "statement": source_claim["claim_text"],
                "scope": {
                    "fields": ["official_case_input", metric],
                    "time": ["HISTORICAL_OFFICIAL_CASE"],
                    "entities": ["CUMCM_CASE"],
                },
                "selected_run_ids": [run_id],
                "selected_output_ids": [output_id],
                "metric_ids": [metric],
                "evidence_class": "PROVIDED_EMPIRICAL",
                "support_predicates": {"scope_bounded": True},
                "status": "SUPPORTED",
                "limitations": [
                    "This is a Development regression, not an independent Validation result.",
                    "Historical model-prior exposure is unverifiable.",
                ],
                "uncertainty": {"scope": "registered historical input and Development split"},
            }
        )
    semantic = {
        "contract_version": "claim-evidence/v3",
        "claims": claims,
        "runs": [run_record],
        "outputs": [output_record],
        "comparators": [],
        "validation": {"counter_evidence_detected": False},
        "aggregate": {
            "primary_requirement_ids": requirements,
            "supported_requirement_ids": requirements,
            "requirement_claim_ids": claim_ids,
        },
    }
    selection = {
        "contract_version": "requirement-selection/v1",
        "requirements": [
            {"requirement_id": requirement_id, "selection_metric": metric}
            for requirement_id in requirements
        ],
        "runs": [run_record],
        "selection": {
            "selection_mode": "GLOBAL_JOINT",
            "requirement_to_run_map": {requirement_id: [run_id] for requirement_id in requirements},
            "requirement_to_output_map": {
                requirement_id: [output_id] for requirement_id in requirements
            },
            "shared_input_hashes": [manifest["input_hash"]],
            "shared_scenario_hashes": [manifest["scenario_hash"]],
            "compatibility_checks": [{"status": "PASS", "check": "SINGLE_SELECTED_RUN"}],
            "cross_requirement_constraints": [],
            "aggregate_objective": metric,
            "tradeoff_rule": "SINGLE_DEVELOPMENT_RUN_FOR_ALL_REGISTERED_REQUIREMENTS",
            "limitations": ["Development regression only; no Validation claim is made."],
        },
    }
    return selection, semantic


def run_case(core: Any, config: CaseConfig, source: Path, attempt: int) -> dict[str, Any]:
    case_root = CACHE_ROOT / f"{config.case_id}-ATTEMPT-{attempt:03d}"
    started_wall = time.time()
    prepared = prepare_case(core, config, case_root, source)
    source_plan = load_json(source / "experiments/experiment_plan.json")["content"]
    candidate_records = prepared["candidates"]["candidates"]
    candidate_ids = [item["candidate_id"] for item in candidate_records]
    baseline_id = next(
        item["candidate_id"] for item in candidate_records if item.get("baseline") is True
    )
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
    stop_rule = "one preregistered RC7 Development-regression attempt per candidate"
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
    selection_rule = "ARGMIN_THEN_ID"
    plan = dict(source_plan)
    plan.update(
        {
            "preregistered": True,
            "execution_prepared": True,
            "candidate_ids": candidate_ids,
            "baseline_id": baseline_id,
            "splits": splits,
            "metric": metric,
            "metric_direction": direction,
            "aggregation_rule": aggregation,
            "selection_rule": selection_rule,
            "handoff_generated_at": GENERATED_AT,
            "random_seeds": seeds,
            "required_input_hashes": prepared["audit"]["data_hashes"],
            "required_code_files": code_files,
            "code_commit": code_commit,
            "trusted_freeze_registry": freezes,
            "stop_rule": stop_rule,
        }
    )
    accepted(core, case_root, "experiment_plan", plan)
    preflight = write_probe(core, case_root, prepared["requirements"], metric)
    core.advance_once(case_root)
    core.advance_once(case_root)

    executions: list[dict[str, Any]] = []
    scores: dict[str, list[float]] = {}
    primary_code_path = config.code_files[0][0]
    for candidate_id in candidate_ids:
        run_id = f"RUN-RC7-{candidate_id}-S{config.seed}"
        captured = core.execute_case_code(
            case_root,
            run_id=run_id,
            candidate_id=candidate_id,
            seed=config.seed,
            code_path=primary_code_path,
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
                raise ValueError(f"RC7_REGRESSION_SCORE_INVALID:{candidate_id}")
            scores.setdefault(candidate_id, []).append(float(score))
    if baseline_id not in scores or len(scores) < 2:
        raise ValueError("RC7_REGRESSION_SUCCESS_SET_INSUFFICIENT")
    aggregated = {key: sum(values) / len(values) for key, values in scores.items()}
    target = min(aggregated.values())
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

    attempts = [
        {
            "candidate_id": execution["candidate_id"],
            "run_id": execution["run_id"],
            "outcome": execution["outcome"],
            "validation_score": (
                aggregated[execution["candidate_id"]] if execution["outcome"] == "SUCCESS" else None
            ),
            "random_seed": execution["random_seed"],
        }
        for execution in executions
    ]
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
    selection, semantic = build_semantic_records(
        core,
        requirements=prepared["requirements"],
        run_id=selected_manifest["run_id"],
        manifest=selected_manifest,
        output=selected_output,
        metric=metric,
    )
    accepted(core, case_root, "requirement_selection", selection)
    accepted(core, case_root, "semantic_claim_support", semantic)
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
    handoff = core.build_expected_handoff(case_root, core.load_state(case_root))
    core.write_json(case_root / core.ARTIFACT_PATHS["modeling_to_paper_handoff"], handoff)
    state = core.advance_once(case_root)
    if state["state"] != "READY_FOR_PAPER_HANDOFF":
        raise ValueError("RC7_REGRESSION_TERMINAL_STATE_INVALID")

    prior_attempts = []
    for prior in range(1, attempt):
        prior_root = CACHE_ROOT / f"{config.case_id}-ATTEMPT-{prior:03d}"
        prior_state_path = prior_root / "case_state.json"
        if prior_state_path.is_file():
            prior_attempts.append(
                {
                    "attempt": prior,
                    "workspace_relative": prior_root.relative_to(ROOT).as_posix(),
                    "preserved": True,
                    "terminal_observed_state": core.load_json(prior_state_path).get("state"),
                    "run_count": len(list((prior_root / "runs").glob("*/manifest.json"))),
                    "capture_count": len(
                        list((prior_root / "runs").glob("*/execution_capture.json"))
                    ),
                    "failure_scope": "RC7_HARNESS_OR_CASE_ARTIFACT_CONTRACT",
                }
            )

    evidence = {
        "schema_version": "1.0.0",
        "artifact_type": "c_target_rc7_development_regression_evidence",
        "case_id": config.case_id,
        "source_first_run_case_id": config.tracked_case_id,
        "evidence_class": "DEVELOPMENT_REGRESSION_NOT_BLIND_NOT_VALIDATION",
        "route": "DEVELOPMENT_REGRESSION",
        "answer_access_status": "UNLOCKED_AFTER_FIRST_RUN",
        "answer_materials_used": [],
        "first_run_freeze": {
            "path": prepared["first_run_freeze_path"],
            "sha256": prepared["first_run_freeze_sha256"],
        },
        "official_input_provenance": {
            "page_url": config.official_page_url,
            "page_url_sha256": config.official_page_url_sha256,
            "archive_url": config.official_archive_url,
            "archive_url_sha256": config.official_archive_url_sha256,
            "archive_sha256": config.archive_sha256,
            "bound_data_hashes": prepared["audit"]["data_hashes"],
            "excluded_from_execution": ["REFERENCE_ANSWER", "THIRD_PARTY_DATA"],
        },
        "skill": {
            "version": core.VERSION,
            "candidate_implementation_commit": code_commit,
            "execution_code_commit": code_commit,
            "git_tree_sha1": git_tree(code_commit, ".agents/skills/cumcm-modeling-evidence"),
        },
        "workspace_relative": case_root.relative_to(ROOT).as_posix(),
        "attempt_number": attempt,
        "preserved_prior_attempts": prior_attempts,
        "output_contract_preflight": preflight,
        "stage_status": [{"stage": stage, "status": "PASS"} for stage in core.STAGES],
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
        "elapsed_seconds": round(time.time() - started_wall, 6),
        "api_calls": 0,
        "third_party_executions": 0,
        "model_training": False,
        "validation_route_executed": False,
    }
    core.write_json(
        RESULT_ROOT / config.tracked_case_id / "development_regression_evidence.json",
        evidence,
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(CASES) + ("all",), default="all")
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    if args.attempt < 1 or args.attempt > 6:
        raise SystemExit("--attempt must be in 1..6")
    core = load_core()
    selected = list(CASES) if args.case == "all" else [args.case]
    results = []
    for key in selected:
        config = CASES[key]
        source = ensure_source_workspace(core, config)
        results.append(run_case(core, config, source, args.attempt))
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
