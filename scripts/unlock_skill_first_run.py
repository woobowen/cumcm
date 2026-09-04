#!/usr/bin/env python3
"""Unlock Development references only after a frozen commit is verified remotely."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "benchmarks/case_registry.yaml"
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parsed_time(value: str, code: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(code) from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{code.removesuffix('_INVALID')}_TIMEZONE_REQUIRED")
    return parsed


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
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    os.replace(temporary, path)


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, check=False, capture_output=True
    )
    if completed.returncode != 0:
        raise ValueError("FREEZE_COMMIT_EVIDENCE_UNAVAILABLE")
    return completed.stdout


def unlock(args: argparse.Namespace) -> dict[str, Any]:
    if not GIT_SHA.fullmatch(args.freeze_commit):
        raise ValueError("FREEZE_COMMIT_INVALID")
    registry = read_registry(args.registry)
    matches = [case for case in registry["cases"] if case.get("case_id") == args.case_id]
    if len(matches) != 1:
        raise ValueError("CASE_REGISTRATION_NOT_UNIQUE")
    record = matches[0]
    if record.get("set_type") != "DEVELOPMENT":
        raise ValueError("UNLOCK_REQUIRES_DEVELOPMENT_CASE")
    if record.get("answer_access_status") != "SEALED":
        raise ValueError("ANSWER_ALREADY_UNLOCKED")
    if record.get("first_run_status") != "FROZEN":
        raise ValueError("FIRST_RUN_NOT_FROZEN")
    binding = record.get("first_run_freeze")
    if not isinstance(binding, dict):
        raise ValueError("FIRST_RUN_FREEZE_BINDING_MISSING")
    try:
        relative = args.freeze_file.resolve().relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError("FREEZE_FILE_OUTSIDE_REPOSITORY") from exc
    if binding.get("path") != str(relative):
        raise ValueError("FREEZE_FILE_PATH_MISMATCH")
    expected_hash = str(binding.get("sha256", ""))
    if file_hash(args.freeze_file) != expected_hash:
        raise ValueError("FREEZE_FILE_HASH_MISMATCH")
    committed = git_bytes("show", f"{args.freeze_commit}:{relative}")
    if hashlib.sha256(committed).hexdigest() != expected_hash:
        raise ValueError("FREEZE_COMMIT_CONTENT_MISMATCH")
    remote_lines = git_bytes(
        "ls-remote", "--heads", args.remote, f"refs/heads/{args.branch}"
    ).decode("utf-8").splitlines()
    remote_shas = [line.split()[0] for line in remote_lines if line.split()]
    if remote_shas != [args.freeze_commit]:
        raise ValueError("FREEZE_REMOTE_SHA_MISMATCH")
    unlock_time = args.unlock_time
    if parsed_time(unlock_time, "UNLOCK_TIME_INVALID") < parsed_time(
        str(record.get("freeze_time", "")), "FREEZE_TIME_INVALID"
    ):
        raise ValueError("UNLOCK_TIME_BEFORE_FREEZE")
    freeze_artifact = json.loads(args.freeze_file.read_text(encoding="utf-8"))
    if (
        freeze_artifact.get("case_id") != args.case_id
        or freeze_artifact.get("answer_access_status") != "SEALED"
        or freeze_artifact.get("first_run_status") != "FROZEN"
    ):
        raise ValueError("FREEZE_ARTIFACT_IDENTITY_MISMATCH")
    if not args.dry_run:
        record["answer_access_status"] = "UNLOCKED_AFTER_FIRST_RUN"
        record["unlock_status"] = "UNLOCKED_AFTER_FIRST_RUN"
        record["unlock_time"] = unlock_time
        record["unlock_receipt"] = {
            "freeze_commit": args.freeze_commit,
            "remote": args.remote,
            "branch": args.branch,
            "verified_remote_sha": args.freeze_commit,
        }
        write_registry(args.registry, registry)
    return {
        "status": "PASS",
        "dry_run": args.dry_run,
        "case_id": args.case_id,
        "answer_access_status": "UNLOCKED_AFTER_FIRST_RUN",
        "freeze_commit": args.freeze_commit,
        "verified_remote_sha": args.freeze_commit,
        "unlock_time": unlock_time,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--freeze-file", type=Path, required=True)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--unlock-time", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = unlock(args)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
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
