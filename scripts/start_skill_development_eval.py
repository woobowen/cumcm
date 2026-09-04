#!/usr/bin/env python3
"""Register a sealed first run and initialize its private case workspace."""

from __future__ import annotations

import argparse
import hashlib
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
DEFAULT_PROJECT_STATE = REPO_ROOT / "state/project_state.json"
CASE_CLI = REPO_ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
SKILL_VERSION = "0.2.0-competition-rc1"
ALLOWED_SET_TYPES = {"DEVELOPMENT", "VALIDATION", "HELD_OUT", "STRESS"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


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


def parse_data_hash(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("DATA_HASH_ARGUMENT_INVALID")
        name, digest = value.split("=", 1)
        path = Path(name)
        if not name or path.is_absolute() or ".." in path.parts or not HEX64.fullmatch(digest):
            raise ValueError("DATA_HASH_ARGUMENT_INVALID")
        if name in parsed:
            raise ValueError("DATA_HASH_DUPLICATE")
        parsed[name] = digest
    return parsed


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_workspace_file(case_root: Path, relative: str) -> Path:
    path = Path(relative)
    if not relative or path.is_absolute() or ".." in path.parts:
        raise ValueError("WORKSPACE_PATH_INVALID")
    resolved = (case_root / path).resolve()
    try:
        resolved.relative_to(case_root.resolve())
    except ValueError as exc:
        raise ValueError("WORKSPACE_PATH_INVALID") from exc
    if not resolved.is_file():
        raise ValueError("WORKSPACE_INPUT_MISSING")
    return resolved


def verify_skill_commit(commit: str) -> None:
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if exists.returncode != 0:
        raise ValueError("SKILL_COMMIT_NOT_FOUND")
    current_matches = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            commit,
            "--",
            ".agents/skills/cumcm-modeling-evidence",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    if current_matches.returncode != 0:
        raise ValueError("SKILL_COMMIT_TREE_MISMATCH")


def iso_time(value: str | None) -> str:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("START_TIME_INVALID") from exc
    if parsed.utcoffset() is None:
        raise ValueError("START_TIME_TIMEZONE_REQUIRED")
    return value


def require_competition_rc_ready(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    competition = value.get("competition_rc1") if isinstance(value, dict) else None
    integration_audit = (
        competition.get("integration_audit") if isinstance(competition, dict) else None
    )
    if (
        not isinstance(value, dict)
        or value.get("technical_adjudication_status") != "COMPETITION_SKILL_RC_READY"
        or value.get("next_phase_allowed") != "PHASE-SKILL-DEVELOPMENT-EVAL-004"
        or value.get("active_skill_version") != SKILL_VERSION
        or not isinstance(competition, dict)
        or not isinstance(integration_audit, dict)
        or integration_audit.get("status") != "PASS"
    ):
        raise ValueError("COMPETITION_RC_NOT_READY_FOR_DEVELOPMENT_EVAL")


def register(args: argparse.Namespace) -> dict[str, Any]:
    require_competition_rc_ready(DEFAULT_PROJECT_STATE)
    registry = read_registry(args.registry)
    if args.set_type not in ALLOWED_SET_TYPES:
        raise ValueError("SET_TYPE_INVALID")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{2,63}", args.case_id):
        raise ValueError("CASE_ID_INVALID")
    if not HEX64.fullmatch(args.problem_hash):
        raise ValueError("PROBLEM_HASH_INVALID")
    if not GIT_SHA.fullmatch(args.skill_commit):
        raise ValueError("SKILL_COMMIT_INVALID")
    if not args.problem_source or not args.model or not args.reasoning:
        raise ValueError("REGISTRATION_FIELD_MISSING")
    data_hashes = parse_data_hash(args.data_hash)
    verify_skill_commit(args.skill_commit)
    problem_path = safe_workspace_file(args.case_root, args.problem_source)
    if file_hash(problem_path) != args.problem_hash:
        raise ValueError("PROBLEM_HASH_MISMATCH")
    for relative, expected in data_hashes.items():
        if file_hash(safe_workspace_file(args.case_root, relative)) != expected:
            raise ValueError("DATA_HASH_MISMATCH")
    if any(case.get("case_id") == args.case_id for case in registry["cases"]):
        raise ValueError("CASE_ID_ALREADY_REGISTERED")
    record = {
        "case_id": args.case_id,
        "set_type": args.set_type,
        "problem_source": args.problem_source,
        "problem_hash": args.problem_hash,
        "data_hashes": data_hashes,
        "answer_access_status": "SEALED",
        "first_run_status": "IN_PROGRESS",
        "skill_version": SKILL_VERSION,
        "skill_commit": args.skill_commit,
        "model": args.model,
        "reasoning": args.reasoning,
        "start_time": iso_time(args.start_time),
        "freeze_time": None,
        "unlock_time": None,
        "generalizable_failures": [],
        "problem_specific_findings": [],
    }
    if not args.dry_run:
        state_path = args.case_root / "case_state.json"
        if state_path.exists():
            checked = subprocess.run(
                [
                    sys.executable,
                    str(CASE_CLI),
                    "status",
                    "--case-root",
                    str(args.case_root),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if checked.returncode != 0:
                raise ValueError("CASE_WORKSPACE_STATE_INVALID")
            state = json.loads(checked.stdout)["state"]
            if (
                state.get("case_id") != args.case_id
                or state.get("skill_version") != SKILL_VERSION
                or state.get("state") != "CREATED"
            ):
                raise ValueError("CASE_WORKSPACE_BINDING_MISMATCH")
        else:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CASE_CLI),
                    "init",
                    "--case-root",
                    str(args.case_root),
                    "--case-id",
                    args.case_id,
                    "--kind",
                    args.case_kind,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise ValueError("CASE_WORKSPACE_INITIALIZATION_FAILED")
            state = json.loads(state_path.read_text(encoding="utf-8"))
        binding_relative = "state/development_eval_binding.json"
        binding_path = args.case_root / binding_relative
        if binding_path.exists():
            raise ValueError("CASE_WORKSPACE_BINDING_ALREADY_EXISTS")
        binding = {
            "case_id": args.case_id,
            "problem_source": args.problem_source,
            "problem_hash": args.problem_hash,
            "data_hashes": data_hashes,
            "skill_version": SKILL_VERSION,
            "skill_commit": args.skill_commit,
            "answer_access_status": "SEALED",
        }
        binding_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = binding_path.with_name(f".{binding_path.name}.tmp")
        temporary.write_text(
            json.dumps(binding, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, binding_path)
        bound_files = {
            args.problem_source: args.problem_hash,
            **data_hashes,
            binding_relative: file_hash(binding_path),
        }
        state["evidence_bindings"].update(bound_files)
        state["history"][0]["evidence"] = sorted(bound_files)
        temporary_state = state_path.with_name(f".{state_path.name}.tmp")
        temporary_state.write_text(
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary_state, state_path)
        registry["cases"].append(record)
        write_registry(args.registry, registry)
    return {
        "status": "PASS",
        "dry_run": args.dry_run,
        "case_id": args.case_id,
        "set_type": args.set_type,
        "answer_access_status": "SEALED",
        "first_run_status": "IN_PROGRESS",
        "skill_version": SKILL_VERSION,
        "skill_commit": args.skill_commit,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--set-type", choices=sorted(ALLOWED_SET_TYPES), required=True)
    parser.add_argument("--problem-source", required=True)
    parser.add_argument("--problem-hash", required=True)
    parser.add_argument("--data-hash", action="append", default=[])
    parser.add_argument("--skill-commit", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning", required=True)
    parser.add_argument("--start-time")
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument(
        "--case-kind",
        choices=("prediction", "optimization", "general"),
        default="general",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = register(args)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(
            json.dumps(
                {
                    "status": "BLOCK",
                    "reason_codes": [str(exc) or type(exc).__name__],
                },
                sort_keys=True,
            )
        )
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
