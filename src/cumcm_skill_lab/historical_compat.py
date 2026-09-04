"""Read frozen predecessor inputs from their last known-good Git checkpoint."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

RC1_START_COMMIT = "131823092a2e8c33c677419d45ed54b381a9948e"
RC1_SUCCESSOR_STATUS = "COMPETITION_SKILL_RC_READY"
DEVELOPMENT_EVAL_STATUSES = {
    "DEVELOPMENT_FIRST_RUN_IN_PROGRESS",
    "DEVELOPMENT_EVAL_RC2_READY",
    "DEVELOPMENT_EVAL_RC3_READY",
    "DEVELOPMENT_EVAL_COMPLETE_NO_SKILL_CHANGE",
    "DEVELOPMENT_EVAL_INCOMPLETE",
    "OFFICIAL_INPUTS_REQUIRED",
    "FIRST_RUN_CONTAMINATION_SUSPECTED",
    "INFRASTRUCTURE_BLOCKED",
}


def git_file_bytes(root: Path, relative: str, *, commit: str = RC1_START_COMMIT) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def git_file_sha256(root: Path, relative: str, *, commit: str = RC1_START_COMMIT) -> str:
    return hashlib.sha256(git_file_bytes(root, relative, commit=commit)).hexdigest()


def git_json(root: Path, relative: str, *, commit: str = RC1_START_COMMIT) -> dict[str, Any]:
    value = json.loads(git_file_bytes(root, relative, commit=commit))
    if not isinstance(value, dict):
        raise ValueError(f"HISTORICAL_JSON_NOT_OBJECT:{relative}")
    return value


def competition_rc_successor(root: Path) -> bool:
    try:
        state = json.loads((root / "state/project_state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    rc1_ready = (
        isinstance(state, dict)
        and state.get("technical_adjudication_status") == RC1_SUCCESSOR_STATUS
        and state.get("active_skill_version") == "0.2.0-competition-rc1"
    )
    development_successor = (
        isinstance(state, dict)
        and state.get("phase") == "PHASE-SKILL-DEVELOPMENT-EVAL-004"
        and state.get("technical_adjudication_status") in DEVELOPMENT_EVAL_STATUSES
        and state.get("active_skill_version")
        in {
            "0.2.0-competition-rc1",
            "0.2.0-competition-rc2",
            "0.2.0-competition-rc3",
        }
    )
    return rc1_ready or development_successor


def historical_file_hash_matches(root: Path, relative: str, expected: str) -> bool:
    """Accept a frozen predecessor hash only from live bytes or the RC1 start checkpoint."""
    path = root / relative
    if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
        return True
    if not competition_rc_successor(root):
        return False
    try:
        return git_file_sha256(root, relative) == expected
    except subprocess.CalledProcessError:
        return False


def git_repository_file_hashes(
    root: Path,
    roots: Iterable[Path],
    *,
    commit: str = RC1_START_COMMIT,
    excluded_prefixes: tuple[str, ...] = (),
) -> dict[str, str]:
    prefixes = tuple(item.as_posix().rstrip("/") for item in roots)
    completed = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit, "--", *prefixes],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    paths = [
        line
        for line in completed.stdout.splitlines()
        if line
        and not line.endswith((".pyc", ".pyo"))
        and not any(line.startswith(prefix) for prefix in excluded_prefixes)
    ]
    return {relative: git_file_sha256(root, relative, commit=commit) for relative in sorted(paths)}


def historical_json_if_successor(root: Path, relative: str) -> dict[str, Any]:
    if competition_rc_successor(root):
        return git_json(root, relative)
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_NOT_OBJECT:{relative}")
    return value
