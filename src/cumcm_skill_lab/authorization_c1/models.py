"""Shared constants and deterministic hash helpers for the C1 continuation."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

RESULT_ROOT = Path("evals/results/phase-002d-r2a-c1")
INPUT_FREEZE_PATH = RESULT_ROOT / "input_freeze_manifest.json"
STARTING_COMMIT = "2d117985404b21abd7f0c3a10258731e06f77852"
PR_NUMBER = 5
PR_HEAD = STARTING_COMMIT
C1_SUBPHASE = "PHASE-002D-R2A-C1-HISTORICAL-COMPATIBILITY-AND-CANDIDATE-BOUND-AUTHORIZATION-CLOSURE"
C1_ROUTE = C1_SUBPHASE
C1_PLAN = "plans/active/PLAN-0002D-R2A-C1-historical-compatibility-and-candidate-binding.md"
CREATED_AT = "2026-09-03T14:26:16+08:00"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_file_bytes(root: Path, commit: str, relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"GIT_OBJECT_READ_FAILED:{commit}:{relative}:{message}")
    return result.stdout


def git_file_sha256(root: Path, commit: str, relative: str) -> str:
    return sha256_bytes(git_file_bytes(root, commit, relative))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_or_write_json(path: Path, value: Any, *, check: bool) -> list[str]:
    expected = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if check:
        if not path.is_file():
            return [f"ARTIFACT_MISSING:{path.as_posix()}"]
        if path.read_text(encoding="utf-8") != expected:
            return [f"ARTIFACT_STALE:{path.as_posix()}"]
        return []
    write_json(path, value)
    return []
