"""Versioned verification for historical blobs, immutable trees, and live pointers."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from .models import file_sha256, git_file_bytes, sha256_bytes, sha256_json

POLICY_PATH = Path("rules/historical_verification_policy.yaml")
POLICY_SCHEMA_PATH = Path("contracts/historical_verification_policy.schema.json")
MODES = {
    "SUBJECT_COMMIT_BLOB",
    "CURRENT_TREE_IMMUTABLE",
    "LIVE_SEMANTIC_POINTER",
    "DERIVED_OBSERVATION",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _semantic_diff(left: Any, right: Any, prefix: str = "") -> set[str]:
    if isinstance(left, dict) and isinstance(right, dict):
        changed: set[str] = set()
        for key in sorted(set(left) | set(right)):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in left or key not in right:
                changed.add(path)
            else:
                changed.update(_semantic_diff(left[key], right[key], path))
        return changed
    if left != right:
        return {prefix or "$"}
    return set()


def load_policy(root: Path) -> dict[str, Any]:
    policy = yaml.safe_load((root / POLICY_PATH).read_text(encoding="utf-8"))
    schema = _read_json(root / POLICY_SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(policy), key=str)
    if errors:
        raise ValueError(f"HISTORICAL_POLICY_SCHEMA_INVALID:{errors[0].message}")
    seen: set[tuple[str, str]] = set()
    for entry in policy["entries"]:
        key = (entry["path"], entry["manifest_version"])
        if key in seen:
            raise ValueError(f"HISTORICAL_POLICY_DUPLICATE_ENTRY:{key[0]}:{key[1]}")
        seen.add(key)
        if entry["verification_mode"] not in MODES:
            raise ValueError(f"HISTORICAL_POLICY_UNKNOWN_MODE:{entry['verification_mode']}")
        for field in entry["allowed_live_fields"]:
            if "*" in field or field in {"$", ""} or "." not in field:
                raise ValueError(f"HISTORICAL_POLICY_BROAD_ALLOWLIST:{entry['path']}:{field}")
    return policy


def policy_entry(policy: dict[str, Any], path: str, manifest_version: str) -> dict[str, Any]:
    matches = [
        item
        for item in policy["entries"]
        if item["path"] == path and item["manifest_version"] == manifest_version
    ]
    if len(matches) != 1:
        raise ValueError(f"HISTORICAL_POLICY_ENTRY_NOT_UNIQUE:{path}:{manifest_version}")
    return matches[0]


def _validate_workflow(root: Path, value: Any, schema_path: str | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict) or not schema_path:
        return ["LIVE_POINTER_CURRENT_SCHEMA_MISSING"]
    schema_file = root / schema_path
    if not schema_file.is_file():
        return [f"LIVE_POINTER_CURRENT_SCHEMA_MISSING:{schema_path}"]
    schema = _read_json(schema_file)
    validation = sorted(Draft202012Validator(schema).iter_errors(value), key=str)
    errors.extend(f"LIVE_POINTER_CURRENT_SCHEMA_INVALID:{item.message}" for item in validation)
    delivery = value.get("git_delivery", {})
    invariants = {
        "remote_name": "origin",
        "repository": "woobowen/cumcm",
        "protected_base_branch": "main",
        "allow_force_push": False,
        "allow_agent_merge": False,
    }
    for field, expected in invariants.items():
        if delivery.get(field) != expected:
            errors.append(f"LIVE_POINTER_DELIVERY_INVARIANT_FAILED:git_delivery.{field}")
    return errors


def verify_file_entry(
    root: Path,
    entry: dict[str, Any],
    expected_subject_hash: str,
    *,
    current_bytes: bytes | None = None,
    derived_observation: bytes | None = None,
) -> list[str]:
    """Verify one path with no fallback from a missing Git object to the worktree."""
    path = entry["path"]
    mode = entry["verification_mode"]
    if mode not in MODES:
        return [f"HISTORICAL_UNKNOWN_MODE:{path}:{mode}"]
    try:
        subject = git_file_bytes(root, entry["subject_commit"], path)
    except ValueError:
        return [f"HISTORICAL_SUBJECT_READ_FAILED:{entry['subject_commit']}:{path}"]
    if sha256_bytes(subject) != expected_subject_hash:
        return [f"HISTORICAL_BLOB_HASH_MISMATCH:{path}"]
    if mode == "SUBJECT_COMMIT_BLOB":
        return []
    if mode == "DERIVED_OBSERVATION":
        if derived_observation is None:
            return [f"DERIVED_OBSERVATION_AUTHORITY_MISSING:{path}"]
        current = current_bytes if current_bytes is not None else (root / path).read_bytes()
        return [] if current == derived_observation else [f"DERIVED_OBSERVATION_STALE:{path}"]
    if current_bytes is None:
        target = root / path
        if not target.is_file():
            return [f"CURRENT_PATH_MISSING:{path}"]
        current_bytes = target.read_bytes()
    if mode == "CURRENT_TREE_IMMUTABLE":
        return [] if current_bytes == subject else [f"CURRENT_IMMUTABLE_MUTATED:{path}"]
    if mode != "LIVE_SEMANTIC_POINTER":
        return [f"HISTORICAL_UNSUPPORTED_MODE:{path}:{mode}"]
    try:
        historical_value = yaml.safe_load(subject.decode("utf-8"))
        current_value = yaml.safe_load(current_bytes.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        return [f"LIVE_POINTER_PARSE_FAILED:{path}:{type(exc).__name__}"]
    errors = _validate_workflow(root, current_value, entry.get("current_schema"))
    changed = _semantic_diff(historical_value, current_value)
    allowed = set(entry["allowed_live_fields"])
    errors.extend(
        f"LIVE_POINTER_DISALLOWED_FIELD:{path}:{field}" for field in sorted(changed - allowed)
    )
    return sorted(set(errors))


def _git_tree_file_hashes(root: Path, commit: str, relative: str) -> dict[str, str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit, "--", relative],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise ValueError(f"HISTORICAL_TREE_READ_FAILED:{commit}:{relative}")
    paths = result.stdout.splitlines()
    if not paths:
        raise ValueError(f"HISTORICAL_TREE_EMPTY:{commit}:{relative}")
    return {path: sha256_bytes(git_file_bytes(root, commit, path)) for path in paths}


def _current_tree_file_hashes(root: Path, relative: str) -> dict[str, str]:
    base = root / relative.rstrip("/")
    if not base.is_dir():
        raise ValueError(f"CURRENT_TREE_MISSING:{relative}")
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(base.rglob("*"))
        if path.is_file() and not path.name.endswith((".pyc", ".pyo"))
    }


def verify_tree_entry(
    root: Path, entry: dict[str, Any], expected_subject_tree_hash: str
) -> list[str]:
    path = entry["path"]
    if entry["verification_mode"] != "CURRENT_TREE_IMMUTABLE":
        return [f"HISTORICAL_TREE_MODE_INVALID:{path}"]
    try:
        historical = _git_tree_file_hashes(root, entry["subject_commit"], path)
    except ValueError as exc:
        return [str(exc)]
    historical_hash = sha256_json(historical)
    if historical_hash != expected_subject_tree_hash:
        return [f"HISTORICAL_TREE_HASH_MISMATCH:{path}"]
    try:
        current = _current_tree_file_hashes(root, path)
    except ValueError as exc:
        return [str(exc)]
    if current != historical:
        return [f"CURRENT_IMMUTABLE_TREE_MUTATED:{path}"]
    return []


def subject_tree_hash(root: Path, entry: dict[str, Any]) -> str:
    """Return the canonical file-hash tree at the entry's exact Git subject."""
    return sha256_json(_git_tree_file_hashes(root, entry["subject_commit"], entry["path"]))


def verify_derived_observation(
    root: Path,
    entry: dict[str, Any],
    expected_subject_hash: str,
    authority: Callable[[], bytes],
) -> list[str]:
    return verify_file_entry(
        root,
        entry,
        expected_subject_hash,
        derived_observation=authority(),
    )


__all__ = [
    "MODES",
    "POLICY_PATH",
    "load_policy",
    "policy_entry",
    "subject_tree_hash",
    "verify_derived_observation",
    "verify_file_entry",
    "verify_tree_entry",
]
