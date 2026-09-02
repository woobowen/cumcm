"""Shared deterministic helpers and constants for Phase 002D-R1."""

from __future__ import annotations

from pathlib import Path

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    file_sha256,
    read_json,
    read_yaml,
    sha256_json,
    write_json,
)

RESULT_ROOT = Path("evals/results/phase-002d-r1")
SOURCE_ROOT = Path("evals/results/phase-002d")
HISTORICAL_ROOTS = tuple(
    Path(f"evals/results/{name}")
    for name in ("phase-002", "phase-002a", "phase-002b", "phase-002c", "phase-002d")
)
PRIMARY_CASES = ("CASE-001", "CASE-002", "CASE-004", "CASE-006")
ANONYMOUS_ARMS = ("ARM-A", "ARM-B", "ARM-C")
REPEAT_IDS = (1, 2)


def hashed_body(body: dict, key: str) -> dict:
    """Append a canonical SHA-256 without hashing the hash field itself."""
    value = dict(body)
    value[key] = sha256_json(body)
    return value


def file_hashes(root: Path, relative: Path) -> dict[str, str]:
    """Return a stable relative-path to SHA-256 mapping for one tree."""
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted((root / relative).rglob("*"))
        if path.is_file()
    }


__all__ = [
    "ANONYMOUS_ARMS",
    "HISTORICAL_ROOTS",
    "PRIMARY_CASES",
    "REPEAT_IDS",
    "RESULT_ROOT",
    "SOURCE_ROOT",
    "check_or_write",
    "file_hashes",
    "file_sha256",
    "hashed_body",
    "read_json",
    "read_yaml",
    "sha256_json",
    "write_json",
]
