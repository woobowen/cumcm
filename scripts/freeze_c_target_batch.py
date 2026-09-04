#!/usr/bin/env python3
"""Generate the answer-sealed RC3 pre-run freeze for the three-case C batch."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "benchmarks/case_registry.yaml"
STATE_PATH = REPO_ROOT / "state/project_state.json"
INPUT_REGISTRATION_PATH = REPO_ROOT / "evals/results/phase-004c-c-batch/input_registration.json"
DEFAULT_OUTPUT = REPO_ROOT / "evals/results/phase-004c-c-batch/batch_pre_run_freeze.json"
SKILL_ROOT = ".agents/skills/cumcm-modeling-evidence"
RUNNER_PATH = f"{SKILL_ROOT}/scripts/cumcm_case.py"
TARGET_POLICY_PATH = "rules/target_problem_policy.yaml"
SEARCH_POLICY_PATH = "docs/SEARCH_POLICY.md"
PHASE = "PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C"
BATCH_ID = "C-TARGET-BATCH-001"
SKILL_VERSION = "0.2.0-competition-rc3"
SKILL_COMMIT = "8a2a813ff34d8c2701c64ff9d959848e7b88c27c"
SKILL_TREE = "a4551c8aa0b6b119823f6ce9df3f0f948339bb33"
ARCHITECTURE = "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
BRANCH = "feat/phase004c-c-target-batch-generalization"
HEX40 = re.compile(r"^[0-9a-f]{40}$")

CASE_SPECS = (
    (
        "CUMCM-2022-C-DEVELOPMENT-BATCH-001",
        ".cache/official_inputs/CUMCM-2022-C-BATCH-001",
        1,
    ),
    (
        "CUMCM-2021-C-DEVELOPMENT-BATCH-002",
        ".cache/official_inputs/CUMCM-2021-C-BATCH-002",
        2,
    ),
    (
        "CUMCM-2020-C-DEVELOPMENT-BATCH-003",
        ".cache/official_inputs/CUMCM-2020-C-BATCH-003",
        3,
    ),
)

RUBRIC = (
    "first_pass_completion",
    "requirement_coverage",
    "main_question_coverage",
    "time_to_requirement_trace",
    "time_to_data_audit",
    "time_to_first_baseline",
    "time_to_first_valid_result",
    "time_to_final_candidate",
    "time_to_handoff",
    "valid_run_ratio",
    "failed_run_count",
    "manual_intervention_count",
    "recovery_count",
    "hard_failure_count",
    "model_portfolio_quality",
    "data_audit_completeness",
    "mathematical_validity",
    "numerical_validity",
    "feasibility",
    "robustness_completeness",
    "claim_evidence_completeness",
    "handoff_completeness",
    "reproducibility",
    "search_quality",
    "contest_efficiency",
)

HARD_FAILURES = (
    "MAIN_QUESTION_MISSED",
    "UNEXECUTED_CODE_CLAIMED_AS_RESULT",
    "TEST_FUTURE_TARGET_OR_GROUP_LEAKAGE",
    "INFEASIBLE_SOLUTION_ACCEPTED",
    "NONCONVERGED_RUN_ACCEPTED",
    "RAW_INPUT_OVERWRITTEN",
    "RESULT_NOT_BOUND_TO_CODE_AND_INPUT",
    "CLAIM_WITHOUT_EVIDENCE",
    "REFERENCE_ANSWER_EXPOSED_PRE_FREEZE",
    "UNCAPTURED_NUMBER_MANUALLY_INSERTED",
    "FORMAL_SKILL_MUTATED_DURING_BATCH_FIRST_RUN",
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("YAML_OBJECT_REQUIRED")
    return value


def git_text(*arguments: str) -> str:
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


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=REPO_ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        raise ValueError("GIT_EVIDENCE_UNAVAILABLE")
    return completed.stdout


def iso_time(value: str | None) -> str:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("FREEZE_TIME_INVALID") from exc
    if parsed.utcoffset() is None:
        raise ValueError("FREEZE_TIME_TIMEZONE_REQUIRED")
    return value


def dependency_snapshot() -> dict[str, Any]:
    packages = sorted(
        {
            (
                str(distribution.metadata.get("Name") or "UNKNOWN").lower(),
                str(distribution.version),
            )
            for distribution in importlib.metadata.distributions()
        }
    )
    records = [{"name": name, "version": version} for name, version in packages]
    return {
        "method": "importlib.metadata_name_version_only",
        "package_count": len(records),
        "packages": records,
        "sha256": canonical_hash(records),
    }


def case_record(registry: dict[str, Any], case_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in registry.get("cases", [])
        if isinstance(item, dict) and item.get("case_id") == case_id
    ]
    if len(matches) != 1:
        raise ValueError(f"BATCH_CASE_NOT_UNIQUE:{case_id}")
    return matches[0]


def verify_case(
    case_id: str, case_root: Path, position: int, record: dict[str, Any]
) -> dict[str, Any]:
    if (
        record.get("batch_id") != BATCH_ID
        or record.get("batch_position") != position
        or record.get("set_type") != "DEVELOPMENT"
        or record.get("target_problem_type") != "C"
        or record.get("evidence_role") != "DEVELOPMENT_BATCH"
        or record.get("answer_access_status") != "SEALED"
        or record.get("reference_unlock") != "LOCKED"
        or record.get("first_run_status") != "IN_PROGRESS"
        or record.get("strict_first_run_eligibility") != "ELIGIBLE_MODEL_PRIOR_UNVERIFIABLE"
        or record.get("model_prior_status") != "MODEL_PRIOR_EXPOSURE_UNVERIFIABLE"
        or record.get("formal_skill_version") != SKILL_VERSION
        or record.get("formal_skill_commit") != SKILL_COMMIT
        or record.get("skill_version") != SKILL_VERSION
        or record.get("skill_commit") != SKILL_COMMIT
        or record.get("no_solution_exposure_result") != "PASS_NO_SOLUTION_OR_REFERENCE_ACCESSED"
    ):
        raise ValueError(f"BATCH_CASE_NOT_FREEZABLE:{case_id}")
    state_path = case_root / "case_state.json"
    state = load_json(state_path)
    if (
        state.get("case_id") != case_id
        or state.get("state") != "CREATED"
        or state.get("skill_version") != SKILL_VERSION
        or len(state.get("history", [])) != 1
    ):
        raise ValueError(f"BATCH_CASE_ALREADY_STARTED:{case_id}")
    if any((case_root / "runs").glob("*")):
        raise ValueError(f"BATCH_CASE_RUN_EXISTS_BEFORE_FREEZE:{case_id}")
    search_log = case_root / "research/pre_freeze_search_log.jsonl"
    lines = [line for line in search_log.read_text(encoding="utf-8").splitlines() if line]
    events = [json.loads(line) for line in lines]
    if (
        not events
        or any(event.get("case_id") != case_id for event in events)
        or any(event.get("answer_state") != "SEALED" for event in events)
        or any(event.get("no_solution_exposure") is not True for event in events)
        or any(event.get("access_class") == "ACCIDENTAL_SOLUTION_EXPOSURE" for event in events)
    ):
        raise ValueError(f"PRE_FREEZE_SEARCH_LOG_INVALID:{case_id}")
    input_paths = [str(record["problem_source"]), *record["data_hashes"]]
    expected = {str(record["problem_source"]): str(record["problem_hash"]), **record["data_hashes"]}
    for relative in input_paths:
        path = case_root / relative
        if not path.is_file() or file_hash(path) != expected[relative]:
            raise ValueError(f"RAW_INPUT_HASH_MISMATCH:{case_id}")
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
        )
        ignored = subprocess.run(
            ["git", "check-ignore", "--quiet", str(path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            check=False,
        )
        if tracked.returncode == 0 or ignored.returncode != 0:
            raise ValueError(f"RAW_INPUT_TRACKING_BOUNDARY_FAILED:{case_id}")
    return {
        "answer_state": "SEALED",
        "batch_position": position,
        "case_id": case_id,
        "case_state": "CREATED",
        "case_state_sha256": file_hash(state_path),
        "contamination_status": record["contamination_status"],
        "data_hashes": record["data_hashes"],
        "first_run_status": "IN_PROGRESS",
        "generalization_axis": record["generalization_axis"],
        "model": record["model"],
        "model_prior_status": record["model_prior_status"],
        "official_archive_sha256": record["official_package_sha256"],
        "official_title": record["official_title"],
        "problem_hash": record["problem_hash"],
        "problem_source": record["problem_source"],
        "reasoning": record["reasoning"],
        "reference_unlock": "LOCKED",
        "registration_start_time": record["start_time"],
        "search_log_sha256": file_hash(search_log),
        "set_type": "DEVELOPMENT",
        "strict_first_run_eligibility": record["strict_first_run_eligibility"],
        "timebox_seconds": 10800,
    }


def build_freeze(args: argparse.Namespace) -> dict[str, Any]:
    if not HEX40.fullmatch(args.subject_commit):
        raise ValueError("SUBJECT_COMMIT_INVALID")
    if git_text("rev-parse", "HEAD") != args.subject_commit:
        raise ValueError("SUBJECT_COMMIT_NOT_CURRENT_HEAD")
    if git_text("rev-parse", f"origin/{BRANCH}") != args.subject_commit:
        raise ValueError("SUBJECT_COMMIT_NOT_REMOTE_VERIFIED")
    state = load_json(STATE_PATH)
    if (
        state.get("phase") != PHASE
        or state.get("technical_adjudication_status") != "C_TARGET_BATCH_IN_PROGRESS"
        or state.get("current_batch_id") != BATCH_ID
        or state.get("batch_skill_frozen") is not True
        or state.get("batch_reference_unlocked") is not False
    ):
        raise ValueError("PROJECT_STATE_NOT_READY_FOR_BATCH_FREEZE")
    registry = load_yaml(REGISTRY_PATH)
    if any(
        isinstance(item, dict) and item.get("batch_id") == BATCH_ID
        for item in registry.get("planned_cases", [])
    ):
        raise ValueError("BATCH_CASE_REMAINS_PLANNED")
    if git_text("rev-parse", f"{SKILL_COMMIT}:{SKILL_ROOT}") != SKILL_TREE:
        raise ValueError("FROZEN_SKILL_TREE_MISMATCH")
    unchanged = subprocess.run(
        ["git", "diff", "--quiet", SKILL_COMMIT, "--", SKILL_ROOT],
        cwd=REPO_ROOT,
        check=False,
    )
    if unchanged.returncode != 0:
        raise ValueError("FORMAL_SKILL_MUTATED_BEFORE_BATCH_FREEZE")
    listing = git_text("ls-tree", "-r", SKILL_COMMIT, SKILL_ROOT)
    runner_at_commit = git_bytes("show", f"{SKILL_COMMIT}:{RUNNER_PATH}")
    if hashlib.sha256(runner_at_commit).hexdigest() != file_hash(REPO_ROOT / RUNNER_PATH):
        raise ValueError("RUNNER_DRIFT")
    input_registration = load_json(INPUT_REGISTRATION_PATH)
    cases = [
        verify_case(case_id, REPO_ROOT / relative, position, case_record(registry, case_id))
        for case_id, relative, position in CASE_SPECS
    ]
    freeze: dict[str, Any] = {
        "agent_roles": [
            "modeling_orchestrator",
            "problem_and_model_analyst",
            "data_and_experiment_engineer",
            "adversarial_evidence_auditor",
        ],
        "answer_states": ["SEALED", "SEALED", "SEALED"],
        "answer_unlock_preconditions": [
            "THREE_FIRST_RUN_FREEZES_EXIST",
            "THREE_FIRST_RUN_FREEZE_CHECKS_PASS",
            "THREE_FIRST_RUN_COMMITS_REMOTE_VERIFIED",
            "LOCAL_REMOTE_SHA_MATCH",
            "FORMAL_SKILL_TREE_UNCHANGED",
            "NO_UNRESOLVED_SOLUTION_EXPOSURE",
            "RAW_INPUT_HASHES_UNCHANGED",
        ],
        "artifact_type": "c_target_batch_pre_run_freeze",
        "batch_id": BATCH_ID,
        "batch_reference_unlocked": False,
        "batch_skill_frozen": True,
        "case_order": [case_id for case_id, _, _ in CASE_SPECS],
        "cases": cases,
        "created_at": iso_time(args.freeze_time),
        "environment": {
            "dependency_snapshot": dependency_snapshot(),
            "executable": ".venv/bin/python",
            "implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
        },
        "fallback_rule": input_registration["fallback_case"],
        "formal_skill": {
            "architecture": ARCHITECTURE,
            "capability": "COMPETITION_RC",
            "commit": SKILL_COMMIT,
            "deterministic_listing_sha256": hashlib.sha256(
                (listing + "\n").encode("utf-8")
            ).hexdigest(),
            "git_tree_sha1": SKILL_TREE,
            "name": "cumcm-modeling-evidence",
            "version": SKILL_VERSION,
        },
        "freeze_id": "C-TARGET-BATCH-001-PRE-RUN-FREEZE-001",
        "hard_failures": list(HARD_FAILURES),
        "input_registration": {
            "path": str(INPUT_REGISTRATION_PATH.relative_to(REPO_ROOT)),
            "sha256": file_hash(INPUT_REGISTRATION_PATH),
        },
        "manual_intervention_policy": {
            "initial_count_per_case": 0,
            "must_be_captured": True,
            "result_number_insertion": "PROHIBITED",
            "retry_until_success": "PROHIBITED",
        },
        "parallelism": {
            "case_worker_freshness": "FRESH_NATIVE_SUBAGENT_SESSION_PER_CASE",
            "maximum_concurrent_case_workers": 2,
            "peer_output_access": "PROHIBITED",
            "shared_state_writers": ["modeling_orchestrator"],
            "worker_write_scope": "OWN_CASE_DIRECTORY_ONLY",
            "worktree_use": "PROHIBITED",
        },
        "phase": PHASE,
        "raw_inputs_git_ignored": True,
        "runner": {
            "path": RUNNER_PATH,
            "sha256": file_hash(REPO_ROOT / RUNNER_PATH),
        },
        "schema_version": "1.0.0",
        "scoring_rubric": list(RUBRIC),
        "search_policy": {
            "allowed": [
                "OFFICIAL_INPUT_ACQUISITION",
                "GENERAL_DOMAIN_SOURCE",
                "GENERAL_METHOD_SOURCE",
            ],
            "path": SEARCH_POLICY_PATH,
            "prohibited_query_components": [
                "YEAR",
                "PROBLEM_NUMBER",
                "FULL_PROBLEM_TITLE",
                "UNIQUE_ATTACHMENT_FIELD",
                "SOLUTION",
                "ANSWER",
                "AWARDED_PAPER",
                "CODE",
            ],
            "sha256": file_hash(REPO_ROOT / SEARCH_POLICY_PATH),
        },
        "subject_commit": args.subject_commit,
        "subject_git_tree": git_text("rev-parse", f"{args.subject_commit}^{{tree}}"),
        "target_policy": {
            "path": TARGET_POLICY_PATH,
            "sha256": file_hash(REPO_ROOT / TARGET_POLICY_PATH),
        },
    }
    freeze["freeze_payload_sha256"] = canonical_hash(freeze)
    return freeze


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject-commit", required=True)
    parser.add_argument("--freeze-time")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        freeze = build_freeze(args)
        if not args.dry_run:
            write_json(args.output, freeze)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(
            json.dumps(
                {"reason_codes": [str(exc) or type(exc).__name__], "status": "BLOCK"},
                sort_keys=True,
            )
        )
        return 3
    print(
        json.dumps(
            {
                "case_count": len(freeze["cases"]),
                "dry_run": args.dry_run,
                "freeze_payload_sha256": freeze["freeze_payload_sha256"],
                "output": str(args.output),
                "status": "PASS",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
