"""Shared constants and pure helpers for the R2A authorization closure."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path

from cumcm_skill_lab.adjudication.models import file_sha256, sha256_bytes, sha256_json

RESULT_ROOT = Path("evals/results/phase-002d-r2a")
R2_ROOT = Path("evals/results/phase-002d-r2")
FREEZE_PATH = RESULT_ROOT / "input_freeze_manifest.json"
DEPENDENCY_PATH = RESULT_ROOT / "authorization_dependency_graph.json"
FREEZE_ID = "PHASE-002D-R2A-INPUT-FREEZE-001"
DAG_ID = "PHASE-002D-R2A-AUTHORIZATION-DAG-001"
SUBJECT_COMMIT = "7769a1478940305069aab07d71290a06025206d2"
CREATED_AT = "2026-09-03T02:00:00+08:00"
OLD_AUTHORIZATION_ID = "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2"
NEW_AUTHORIZATION_ID = "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A"

IMMUTABLE_ROOTS = (
    Path("evals/results/phase-002"),
    Path("evals/results/phase-002a"),
    Path("evals/results/phase-002b"),
    Path("evals/results/phase-002c"),
    Path("evals/results/phase-002d"),
    Path("evals/results/phase-002d-r1"),
    R2_ROOT,
    Path("specifications/components"),
    Path("specifications/interactions"),
    Path("specifications/architectures"),
    Path("evals/prospective/phase-002d-r2"),
)


def repository_file_hashes(root: Path, roots: Iterable[Path]) -> dict[str, str]:
    """Hash every regular non-bytecode file below the given repository-relative roots."""
    values: dict[str, str] = {}
    for relative in roots:
        base = root / relative
        paths = [base] if base.is_file() else sorted(base.rglob("*"))
        for path in paths:
            if not path.is_file() or path.name.endswith((".pyc", ".pyo")):
                continue
            values[path.relative_to(root).as_posix()] = file_sha256(path)
    return dict(sorted(values.items()))


def git_file_bytes(root: Path, commit: str, relative: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout


def git_file_sha256(root: Path, commit: str, relative: str) -> str:
    return sha256_bytes(git_file_bytes(root, commit, relative))


def git_tree_hash(root: Path, commit: str, relative: str) -> str:
    """Hash path/blob bindings from a committed tree without consulting the worktree."""
    output = subprocess.run(
        ["git", "ls-tree", "-r", "--full-tree", commit, "--", relative],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    bindings: dict[str, str] = {}
    for line in output.splitlines():
        metadata, path = line.split("\t", 1)
        bindings[path] = metadata.split()[2]
    return sha256_json(bindings)


def tree_hash(values: dict[str, str]) -> str:
    return sha256_json(values)
