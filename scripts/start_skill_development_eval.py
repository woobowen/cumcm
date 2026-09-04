#!/usr/bin/env python3
"""Register a sealed first run and initialize its private case workspace."""

from __future__ import annotations

import argparse
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
CASE_CLI = REPO_ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
SKILL_VERSION = "0.2.0-competition-rc1"
ALLOWED_SET_TYPES = {"DEVELOPMENT", "VALIDATION", "HELD_OUT", "STRESS"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def read_registry(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("cases"), list):
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


def iso_time(value: str | None) -> str:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("START_TIME_INVALID") from exc
    return value


def register(args: argparse.Namespace) -> dict[str, Any]:
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
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("case_id") != args.case_id or state.get("skill_version") != SKILL_VERSION:
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
                    "general",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise ValueError("CASE_WORKSPACE_INITIALIZATION_FAILED")
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
