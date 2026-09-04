#!/usr/bin/env python3
"""Freeze a registered blind first run before any answer unlock."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "benchmarks/case_registry.yaml"
CASE_CORE = REPO_ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
REASON_CODE = re.compile(r"^RC_[A-Z0-9_]+(?::[A-Z0-9_]+)*$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_BLOCKED_EVIDENCE = (
    "evidence/first_run_failure.json",
    "evidence/first_run_stage_status.json",
    "evidence/first_run_timing.json",
    "experiments/experiment_plan.json",
)
OPTIONAL_FIRST_RUN_EVIDENCE = (
    "data/data_audit.json",
    "models/assumptions_and_symbols.json",
    "models/model_candidates.json",
    "problem/problem_requirements.json",
    "research/pre_freeze_search_log.jsonl",
    "research/source_ledger.json",
    "research/research_plan.json",
    "state/development_eval_binding.json",
    "state/first_run_start_freeze.json",
    "results/model_comparison.json",
    "results/robustness.json",
    "results/final_result.json",
    "evidence/claim_evidence.json",
    "handoff/modeling_to_paper.json",
    "evidence/first_run_metrics.json",
    "evidence/first_run_stage_status.json",
    "evidence/first_run_timing.json",
    "evidence/first_run_failures.json",
)
BATCH_SUCCESS_EVIDENCE = (
    "data/data_audit.json",
    "models/assumptions_and_symbols.json",
    "models/model_candidates.json",
    "problem/problem_requirements.json",
    "research/pre_freeze_search_log.jsonl",
    "research/source_ledger.json",
    "experiments/experiment_plan.json",
    "results/model_comparison.json",
    "results/robustness.json",
    "results/final_result.json",
    "evidence/claim_evidence.json",
    "handoff/modeling_to_paper.json",
    "evidence/first_run_metrics.json",
    "evidence/first_run_stage_status.json",
    "evidence/first_run_timing.json",
    "evidence/first_run_failures.json",
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_time(value: str | None, code: str) -> str:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(code) from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{code.removesuffix('_INVALID')}_TIMEZONE_REQUIRED")
    return value


def parsed_time(value: str, code: str) -> datetime:
    checked = iso_time(value, code)
    return datetime.fromisoformat(checked.replace("Z", "+00:00"))


def validate_timeline(start_time: str, freeze_time: str) -> None:
    if parsed_time(freeze_time, "FREEZE_TIME_INVALID") < parsed_time(
        start_time, "START_TIME_INVALID"
    ):
        raise ValueError("FREEZE_TIME_BEFORE_START")


def git_output(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ValueError("GIT_EVIDENCE_UNAVAILABLE")
    return completed.stdout.strip()


def skill_tree_evidence(commit: str) -> dict[str, str]:
    tree = git_output("rev-parse", f"{commit}:.agents/skills/cumcm-modeling-evidence")
    listing = git_output("ls-tree", "-r", commit, ".agents/skills/cumcm-modeling-evidence")
    return {
        "git_tree_sha1": tree,
        "deterministic_listing_sha256": hashlib.sha256(
            (listing + "\n").encode("utf-8")
        ).hexdigest(),
    }


def evidence_hashes(case_root: Path, blocked: bool, *, batch_case: bool = False) -> dict[str, str]:
    required = (
        REQUIRED_BLOCKED_EVIDENCE if blocked else BATCH_SUCCESS_EVIDENCE if batch_case else ()
    )
    missing = [relative for relative in required if not (case_root / relative).is_file()]
    if missing:
        raise ValueError(f"FIRST_RUN_EVIDENCE_MISSING:{missing[0]}")
    discovered = {
        str(path.relative_to(case_root))
        for pattern in ("results/*.json", "evidence/first_run*.json")
        for path in case_root.glob(pattern)
        if path.is_file()
    }
    paths = sorted(set(required) | set(OPTIONAL_FIRST_RUN_EVIDENCE) | discovered)
    return {
        relative: file_hash(case_root / relative)
        for relative in paths
        if (case_root / relative).is_file()
    }


def canonical_hash(value: Any) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_json_object(path: Path, reason_code: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(reason_code)
    return value


def case_code_tree_hash(case_root: Path, experiment_plan: Path) -> str:
    plan = load_json_object(experiment_plan, "EXPERIMENT_PLAN_INVALID")
    content = plan.get("content")
    records = content.get("required_code_files") if isinstance(content, dict) else None
    case_records = (
        [item for item in records if isinstance(item, dict) and item.get("scope") == "CASE_ROOT"]
        if isinstance(records, list)
        else []
    )
    if not case_records:
        raise ValueError("CASE_CODE_SET_MISSING")
    normalized: list[dict[str, str]] = []
    for item in case_records:
        relative = item.get("path")
        expected = item.get("sha256")
        repository_path = item.get("repository_path")
        if not all(
            isinstance(value, str) and value for value in (relative, expected, repository_path)
        ):
            raise ValueError("CASE_CODE_RECORD_INVALID")
        path = case_root / str(relative)
        if not path.is_file() or file_hash(path) != expected:
            raise ValueError("CASE_CODE_HASH_MISMATCH")
        normalized.append(
            {
                "path": str(relative),
                "repository_path": str(repository_path),
                "sha256": str(expected),
            }
        )
    return canonical_hash(sorted(normalized, key=lambda item: item["path"]))


def manual_intervention_count(metrics_path: Path) -> int:
    metrics = load_json_object(metrics_path, "FIRST_RUN_METRICS_INVALID")
    content = metrics.get("content")
    value = metrics.get("manual_intervention_count")
    if value is None and isinstance(content, dict):
        value = content.get("manual_intervention_count")
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("MANUAL_INTERVENTION_COUNT_INVALID")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def read_registry(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("cases"), list)
        or not all(isinstance(case, dict) for case in value.get("cases", []))
    ):
        raise ValueError("DEVELOPMENT_REGISTRY_INVALID")
    return value


def write_registry(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def load_core():
    spec = importlib.util.spec_from_file_location("cumcm_case_freeze", CASE_CORE)
    if spec is None or spec.loader is None:
        raise ValueError("FORMAL_SKILL_CORE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_manifest_skill_binding(
    core: Any, record: dict[str, Any], manifest: dict[str, Any]
) -> None:
    code_files = manifest.get("code_files")
    runner_path = ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
    runner_records = (
        [
            item
            for item in code_files
            if isinstance(item, dict)
            and item.get("scope") == "SKILL_ROOT"
            and item.get("repository_path") == runner_path
        ]
        if isinstance(code_files, list)
        else []
    )
    if len(runner_records) != 1 or core.git_blob_hash(
        str(record.get("skill_commit", "")), runner_path
    ) != runner_records[0].get("sha256"):
        raise ValueError("RUN_SKILL_COMMIT_MISMATCH")


def freeze(args: argparse.Namespace) -> dict[str, Any]:
    core = load_core()
    registry = read_registry(args.registry)
    matches = [case for case in registry["cases"] if case.get("case_id") == args.case_id]
    if len(matches) != 1:
        raise ValueError("CASE_REGISTRATION_NOT_UNIQUE")
    record = matches[0]
    if record.get("answer_access_status") != "SEALED":
        raise ValueError("ANSWER_ALREADY_UNLOCKED")
    if record.get("first_run_status") != "IN_PROGRESS":
        raise ValueError("FIRST_RUN_NOT_IN_PROGRESS")
    if args.blocked_reason_code and not REASON_CODE.fullmatch(args.blocked_reason_code):
        raise ValueError("BLOCKED_REASON_CODE_INVALID")
    state_path = args.case_root / "case_state.json"
    if not state_path.is_file():
        raise ValueError("CASE_STATE_MISSING")
    state = core.load_state(args.case_root)
    if state.get("case_id") != args.case_id:
        raise ValueError("CASE_STATE_ID_MISMATCH")
    if state.get("skill_version") != record.get("skill_version"):
        raise ValueError("CASE_STATE_SKILL_VERSION_MISMATCH")
    if (
        state.get("state") not in {"READY_FOR_PAPER_HANDOFF", "STALE", "REJECTED"}
        and not args.blocked_reason_code
    ):
        raise ValueError("FIRST_RUN_NOT_TERMINAL_OR_BLOCKED")
    binding_relative = "state/development_eval_binding.json"
    binding_path = args.case_root / binding_relative
    if not binding_path.is_file():
        raise ValueError("DEVELOPMENT_BINDING_MISSING")
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    expected_binding = {
        "case_id": args.case_id,
        "problem_source": record.get("problem_source"),
        "problem_hash": record.get("problem_hash"),
        "data_hashes": record.get("data_hashes"),
        "skill_version": record.get("skill_version"),
        "skill_commit": record.get("skill_commit"),
        "answer_access_status": "SEALED",
    }
    if binding != expected_binding:
        raise ValueError("DEVELOPMENT_BINDING_MISMATCH")
    expected_workspace = {
        str(record["problem_source"]): str(record["problem_hash"]),
        **{str(key): str(value) for key, value in record.get("data_hashes", {}).items()},
        binding_relative: file_hash(binding_path),
    }
    if any(
        state["evidence_bindings"].get(path) != digest
        for path, digest in expected_workspace.items()
    ):
        raise ValueError("DEVELOPMENT_STATE_BINDING_MISMATCH")
    manifests = sorted(args.case_root.glob("runs/*/manifest.json"))
    if not manifests and not args.blocked_reason_code:
        raise ValueError("FIRST_RUN_MANIFEST_MISSING")
    manifest_hashes: dict[str, str] = {}
    consumed_inputs: dict[str, str] = {}
    freezes = core.trusted_freezes(args.case_root) if manifests else {}
    for path in manifests:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("run_id") != path.parent.name:
            raise ValueError("RUN_ID_PATH_MISMATCH")
        validation = core.validate_manifest(
            manifest,
            case_root=args.case_root,
            trusted_freezes=freezes,
        )
        non_success_only = validation.reason_codes and all(
            code.startswith("RC_MANIFEST_NOT_SUCCESS:") for code in validation.reason_codes
        )
        if not validation.accepted and not non_success_only:
            raise ValueError(";".join(validation.reason_codes))
        validate_manifest_skill_binding(core, record, manifest)
        for item in manifest["input_files"]:
            consumed_inputs[item["path"]] = item["sha256"]
        manifest_hashes[str(path.relative_to(args.case_root))] = file_hash(path)
    if manifests and any(
        consumed_inputs.get(path) != digest
        for path, digest in record.get("data_hashes", {}).items()
    ):
        raise ValueError("RUN_INPUTS_NOT_BOUND_TO_REGISTRY")
    if not core.stale_check(args.case_root, mutate=False).accepted:
        raise ValueError("CASE_WORKSPACE_STALE")
    freeze_time = iso_time(args.freeze_time, "FREEZE_TIME_INVALID")
    validate_timeline(str(record.get("start_time", "")), freeze_time)
    if not GIT_SHA.fullmatch(args.worktree_commit):
        raise ValueError("WORKTREE_COMMIT_INVALID")
    git_output("cat-file", "-e", f"{args.worktree_commit}^{{commit}}")
    batch_case = record.get("batch_id") == "C-TARGET-BATCH-001"
    artifact_hashes = evidence_hashes(
        args.case_root,
        blocked=bool(args.blocked_reason_code),
        batch_case=batch_case,
    )
    experiment_plan_path = args.case_root / "experiments/experiment_plan.json"
    code_tree_hash = (
        case_code_tree_hash(args.case_root, experiment_plan_path)
        if experiment_plan_path.is_file()
        else None
    )
    metrics_path = args.case_root / "evidence/first_run_metrics.json"
    intervention_count = manual_intervention_count(metrics_path) if metrics_path.is_file() else None
    result_hashes = {
        path: digest for path, digest in artifact_hashes.items() if path.startswith("results/")
    }
    failure_hashes = {
        path: digest
        for path, digest in artifact_hashes.items()
        if path in {"evidence/first_run_failure.json", "evidence/first_run_failures.json"}
    }
    for path in manifests:
        manifest = load_json_object(path, "RUN_MANIFEST_INVALID")
        if manifest.get("status") != "SUCCESS":
            relative = str(path.relative_to(args.case_root))
            failure_hashes[relative] = manifest_hashes[relative]
    freeze_id = f"{args.case_id}-FIRST-RUN-FREEZE-001"
    skill_tree = skill_tree_evidence(str(record["skill_commit"]))
    freeze_artifact = {
        "schema_version": "1.0.0",
        "artifact_type": "development_first_run_freeze",
        "freeze_id": freeze_id,
        "case_id": args.case_id,
        "batch_id": record.get("batch_id"),
        "batch_position": record.get("batch_position"),
        "batch_skill_version": "RC3" if batch_case else None,
        "set_type": record["set_type"],
        "problem_type": record.get("target_problem_type"),
        "answer_state_at_freeze": "SEALED",
        "answer_access_status": "SEALED",
        "model_prior_status": record.get("model_prior_status"),
        "first_run_status": "FROZEN",
        "start_time": record["start_time"],
        "freeze_time": freeze_time,
        "blocked_reason_code": args.blocked_reason_code,
        "model": record["model"],
        "reasoning": record["reasoning"],
        "problem_hash": record["problem_hash"],
        "data_hashes": record["data_hashes"],
        "formal_skill_version": record.get("formal_skill_version", record["skill_version"]),
        "formal_skill_commit": record.get("formal_skill_commit", record["skill_commit"]),
        "formal_skill_tree": skill_tree["git_tree_sha1"],
        "skill": {
            "version": record["skill_version"],
            "commit": record["skill_commit"],
            **skill_tree,
        },
        "worktree_commit": args.worktree_commit,
        "case_state": state["state"],
        "case_state_sha256": file_hash(state_path),
        "search_log_hash": artifact_hashes.get("research/pre_freeze_search_log.jsonl"),
        "source_ledger_hash": artifact_hashes.get("research/source_ledger.json"),
        "requirement_trace_hash": artifact_hashes.get("problem/problem_requirements.json"),
        "data_audit_hash": artifact_hashes.get("data/data_audit.json"),
        "model_portfolio_hash": artifact_hashes.get("models/model_candidates.json"),
        "experiment_plan_hash": artifact_hashes.get("experiments/experiment_plan.json"),
        "case_code_tree_hash": code_tree_hash,
        "run_manifest_hashes": manifest_hashes,
        "failure_hashes": failure_hashes,
        "result_hashes": result_hashes,
        "robustness_hash": artifact_hashes.get("results/robustness.json"),
        "claim_evidence_hash": artifact_hashes.get("evidence/claim_evidence.json"),
        "handoff_hash": artifact_hashes.get("handoff/modeling_to_paper.json"),
        "timing_hash": artifact_hashes.get("evidence/first_run_timing.json"),
        "manual_intervention_count": intervention_count,
        "first_run_artifact_hashes": artifact_hashes,
    }
    freeze_artifact["freeze_hash"] = canonical_hash(freeze_artifact)
    serialized = json.dumps(freeze_artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    freeze_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    evidence = {
        "skill_version": record["skill_version"],
        "skill_commit": record["skill_commit"],
        "case_state": state["state"],
        "case_state_sha256": file_hash(state_path),
        "run_manifest_hashes": manifest_hashes,
        "blocked_reason_code": args.blocked_reason_code,
        "first_run_artifact_hashes": artifact_hashes,
        "freeze_id": freeze_id,
        "freeze_sha256": freeze_sha256,
        "worktree_commit": args.worktree_commit,
    }
    if not args.dry_run:
        write_json(args.freeze_output, freeze_artifact)
        if file_hash(args.freeze_output) != freeze_sha256:
            raise ValueError("FREEZE_ARTIFACT_HASH_MISMATCH")
        record["first_run_status"] = "FROZEN"
        record["freeze_time"] = freeze_time
        record["first_run_evidence"] = evidence
        record["first_run_freeze"] = {
            "freeze_id": freeze_id,
            "path": str(args.freeze_output.resolve().relative_to(REPO_ROOT)),
            "sha256": freeze_sha256,
            "subject_commit": args.worktree_commit,
        }
        write_registry(args.registry, registry)
    return {
        "status": "PASS",
        "dry_run": args.dry_run,
        "case_id": args.case_id,
        "first_run_status": "FROZEN",
        "answer_access_status": "SEALED",
        "freeze_time": freeze_time,
        "freeze_output": str(args.freeze_output),
        "freeze_sha256": freeze_sha256,
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--freeze-output", type=Path, required=True)
    parser.add_argument("--worktree-commit", required=True)
    parser.add_argument("--freeze-time")
    parser.add_argument("--blocked-reason-code")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = freeze(args)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(
            json.dumps(
                {"status": "BLOCK", "reason_codes": [str(exc) or type(exc).__name__]},
                sort_keys=True,
            )
        )
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
