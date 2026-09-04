#!/usr/bin/env python3
"""Create an immutable metadata-corrected successor to a C-target first-run freeze."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "benchmarks/case_registry.yaml"
FULL_RC3 = "0.2.0-competition-rc3"
SHORT_RC3 = "RC3"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def checked_time(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("CORRECTION_TIME_TIMEZONE_REQUIRED")
    return value


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        raise ValueError("FREEZE_COMMIT_EVIDENCE_UNAVAILABLE")
    return completed.stdout


def build_corrected_freeze(
    original: dict[str, Any],
    *,
    original_path: str,
    original_sha256: str,
    original_commit: str,
    correction_time: str,
    worktree_commit: str,
) -> dict[str, Any]:
    if original.get("batch_skill_version") != SHORT_RC3:
        raise ValueError("ORIGINAL_FREEZE_NOT_ELIGIBLE_FOR_DECLARED_CORRECTION")
    if original.get("formal_skill_version") != FULL_RC3:
        raise ValueError("ORIGINAL_FORMAL_SKILL_VERSION_INVALID")
    corrected = copy.deepcopy(original)
    old_id = str(original.get("freeze_id", ""))
    corrected["freeze_id"] = f"{old_id}-METADATA-CORRECTION-002"
    corrected["batch_skill_version"] = FULL_RC3
    corrected["worktree_commit"] = worktree_commit
    corrected["supersedes_freeze"] = {
        "freeze_id": old_id,
        "path": original_path,
        "sha256": original_sha256,
        "commit": original_commit,
    }
    corrected["metadata_correction"] = {
        "reason_code": "RC_BATCH_SKILL_VERSION_SHORT_ALIAS_REJECTED",
        "correction_time": correction_time,
        "changed_fields": ["batch_skill_version", "freeze_id", "worktree_commit"],
        "case_evidence_changed": False,
        "run_evidence_changed": False,
        "answer_state_changed": False,
        "original_freeze_preserved": True,
    }
    corrected.pop("freeze_hash", None)
    corrected["freeze_hash"] = canonical_hash(corrected)
    return corrected


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    os.replace(temporary, path)


def correct(args: argparse.Namespace) -> dict[str, Any]:
    if not HEX40.fullmatch(args.superseded_freeze_commit) or not HEX40.fullmatch(
        args.worktree_commit
    ):
        raise ValueError("CORRECTION_COMMIT_INVALID")
    git_bytes("cat-file", "-e", f"{args.worktree_commit}^{{commit}}")
    registry = yaml.safe_load(args.registry.read_text(encoding="utf-8"))
    matches = [case for case in registry.get("cases", []) if case.get("case_id") == args.case_id]
    if len(matches) != 1:
        raise ValueError("CASE_REGISTRATION_NOT_UNIQUE")
    record = matches[0]
    reference = record.get("first_run_freeze")
    if (
        record.get("first_run_status") != "FROZEN"
        or record.get("answer_access_status") != "SEALED"
        or not isinstance(reference, dict)
    ):
        raise ValueError("FIRST_RUN_FREEZE_NOT_SEALED_AND_FROZEN")
    original_path = args.original_freeze.resolve().relative_to(ROOT)
    if reference.get("path") != str(original_path):
        raise ValueError("ORIGINAL_FREEZE_REGISTRY_PATH_MISMATCH")
    original_sha256 = file_hash(args.original_freeze)
    if reference.get("sha256") != original_sha256:
        raise ValueError("ORIGINAL_FREEZE_REGISTRY_HASH_MISMATCH")
    committed = git_bytes("show", f"{args.superseded_freeze_commit}:{original_path}")
    if hashlib.sha256(committed).hexdigest() != original_sha256:
        raise ValueError("ORIGINAL_FREEZE_COMMIT_CONTENT_MISMATCH")
    original = json.loads(args.original_freeze.read_text(encoding="utf-8"))
    correction_time = checked_time(args.correction_time)
    corrected = build_corrected_freeze(
        original,
        original_path=str(original_path),
        original_sha256=original_sha256,
        original_commit=args.superseded_freeze_commit,
        correction_time=correction_time,
        worktree_commit=args.worktree_commit,
    )
    serialized = json.dumps(corrected, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    corrected_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if not args.dry_run:
        write_json(args.output, corrected)
        if file_hash(args.output) != corrected_sha256:
            raise ValueError("CORRECTED_FREEZE_FILE_HASH_MISMATCH")
        history = record.setdefault("first_run_freeze_history", [])
        history.append(
            {
                **reference,
                "freeze_commit": args.superseded_freeze_commit,
                "status": "SUPERSEDED_METADATA_ONLY_ORIGINAL_PRESERVED",
            }
        )
        output_path = args.output.resolve().relative_to(ROOT)
        record["first_run_freeze"] = {
            "freeze_id": corrected["freeze_id"],
            "path": str(output_path),
            "sha256": corrected_sha256,
            "subject_commit": args.worktree_commit,
        }
        record["first_run_freeze_correction_count"] = len(history)
        evidence = record.get("first_run_evidence")
        if not isinstance(evidence, dict):
            raise ValueError("FIRST_RUN_EVIDENCE_MISSING")
        evidence.update(
            {
                "freeze_id": corrected["freeze_id"],
                "freeze_sha256": corrected_sha256,
                "worktree_commit": args.worktree_commit,
                "supersedes_freeze": corrected["supersedes_freeze"],
            }
        )
        write_yaml(args.registry, registry)
    return {
        "status": "PASS",
        "dry_run": args.dry_run,
        "case_id": args.case_id,
        "answer_access_status": "SEALED",
        "original_freeze_preserved": True,
        "corrected_freeze": str(args.output),
        "corrected_freeze_sha256": corrected_sha256,
        "corrected_freeze_payload_sha256": corrected["freeze_hash"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--original-freeze", type=Path, required=True)
    parser.add_argument("--superseded-freeze-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--correction-time", required=True)
    parser.add_argument("--worktree-commit", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = correct(args)
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
