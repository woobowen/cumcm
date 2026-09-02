"""Shared constants and deterministic helpers for Phase 002D."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    file_sha256,
    read_json,
    read_yaml,
    sha256_json,
    write_json,
)

RESULT_ROOT = Path("evals/results/phase-002d")
CONFIG_PATH = Path("adjudication/configs/phase-002d.yaml")
POLICY_PATH = Path("adjudication/policies/phase-002d.yaml")
PRIMARY_CASES = ("CASE-001", "CASE-002", "CASE-004", "CASE-006")
ANONYMOUS_ARMS = ("ARM-A", "ARM-B", "ARM-C")
HISTORICAL_PHASES = (
    Path("evals/results/phase-002"),
    Path("evals/results/phase-002a"),
    Path("evals/results/phase-002b"),
    Path("evals/results/phase-002c"),
)


def git_output(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=root, check=False, capture_output=True, text=True
    )
    if result.returncode:
        raise RuntimeError(f"GIT_COMMAND_FAILED:{' '.join(arguments)}")
    return result.stdout.strip()


def tree_file_hashes(root: Path, relative: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted((root / relative).rglob("*"))
        if path.is_file()
    }


def hashed_body(body: dict[str, Any], key: str) -> dict[str, Any]:
    result = dict(body)
    result[key] = sha256_json(body)
    return result


__all__ = [
    "ANONYMOUS_ARMS",
    "CONFIG_PATH",
    "HISTORICAL_PHASES",
    "POLICY_PATH",
    "PRIMARY_CASES",
    "RESULT_ROOT",
    "check_or_write",
    "file_sha256",
    "git_output",
    "hashed_body",
    "read_json",
    "read_yaml",
    "sha256_json",
    "tree_file_hashes",
    "write_json",
]
