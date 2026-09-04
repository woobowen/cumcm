#!/usr/bin/env python3
"""Supersede a premature C first-run freeze while preserving all Run evidence."""

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
ALLOWED_CHANGED_ARTIFACTS = {
    "evidence/first_run_failures.json",
    "evidence/first_run_metrics.json",
    "evidence/first_run_stage_status.json",
    "evidence/first_run_timing.json",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        raise ValueError("FREEZE_COMMIT_EVIDENCE_UNAVAILABLE")
    return completed.stdout


def checked_time(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("CORRECTION_TIME_TIMEZONE_REQUIRED")
    return value


def changed_artifact_hashes(
    original: dict[str, Any], case_root: Path
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    original_hashes = original.get("first_run_artifact_hashes")
    if not isinstance(original_hashes, dict):
        raise ValueError("ORIGINAL_ARTIFACT_HASHES_INVALID")
    current: dict[str, str] = {}
    changed: dict[str, dict[str, str]] = {}
    for relative, old_hash in original_hashes.items():
        path = case_root / str(relative)
        if not path.is_file():
            raise ValueError(f"ORIGINAL_ARTIFACT_NOW_MISSING:{relative}")
        new_hash = file_hash(path)
        current[str(relative)] = new_hash
        if new_hash != old_hash:
            changed[str(relative)] = {"before": str(old_hash), "after": new_hash}
    if set(changed) != ALLOWED_CHANGED_ARTIFACTS:
        raise ValueError("POST_FREEZE_CHANGED_ARTIFACT_SET_INVALID")
    return current, changed


def build_corrected_freeze(
    original: dict[str, Any],
    *,
    original_path: str,
    original_sha256: str,
    original_commit: str,
    worktree_commit: str,
    correction_time: str,
    case_root: Path,
) -> dict[str, Any]:
    artifact_hashes, changed = changed_artifact_hashes(original, case_root)
    manifests = original.get("run_manifest_hashes")
    if not isinstance(manifests, dict) or not manifests:
        raise ValueError("ORIGINAL_RUN_MANIFEST_HASHES_INVALID")
    for relative, expected in manifests.items():
        if file_hash(case_root / str(relative)) != expected:
            raise ValueError(f"POST_FREEZE_RUN_MANIFEST_DRIFT:{relative}")
    state_hash = file_hash(case_root / "case_state.json")
    metrics = json.loads(
        (case_root / "evidence/first_run_metrics.json").read_text(encoding="utf-8")
    )
    content = metrics.get("content") if isinstance(metrics, dict) else None
    manual = content.get("manual_intervention_count") if isinstance(content, dict) else None
    if not isinstance(manual, int) or isinstance(manual, bool) or manual < 0:
        raise ValueError("MANUAL_INTERVENTION_COUNT_INVALID")
    corrected = copy.deepcopy(original)
    old_id = str(original.get("freeze_id", ""))
    corrected.update(
        {
            "freeze_id": f"{old_id}-EVIDENCE-CORRECTION-002",
            "freeze_time": correction_time,
            "worktree_commit": worktree_commit,
            "case_state_sha256": state_hash,
            "first_run_artifact_hashes": artifact_hashes,
            "failure_hashes": {
                path: digest
                for path, digest in artifact_hashes.items()
                if path in {"evidence/first_run_failure.json", "evidence/first_run_failures.json"}
            },
            "timing_hash": artifact_hashes["evidence/first_run_timing.json"],
            "manual_intervention_count": manual,
            "supersedes_freeze": {
                "freeze_id": old_id,
                "path": original_path,
                "sha256": original_sha256,
                "commit": original_commit,
            },
            "evidence_correction": {
                "reason_code": "RC_PREMATURE_FREEZE_SUMMARY_HASH_DRIFT",
                "correction_time": correction_time,
                "changed_artifacts": changed,
                "case_state_sha256_before": original.get("case_state_sha256"),
                "case_state_sha256_after": state_hash,
                "run_evidence_changed": False,
                "result_evidence_changed": False,
                "claim_or_handoff_evidence_changed": False,
                "answer_state_changed": False,
                "original_freeze_preserved": True,
            },
        }
    )
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
    relative = args.original_freeze.resolve().relative_to(ROOT)
    original_sha256 = file_hash(args.original_freeze)
    if reference.get("path") != str(relative) or reference.get("sha256") != original_sha256:
        raise ValueError("ORIGINAL_FREEZE_REGISTRY_MISMATCH")
    committed = git_bytes("show", f"{args.superseded_freeze_commit}:{relative}")
    if hashlib.sha256(committed).hexdigest() != original_sha256:
        raise ValueError("ORIGINAL_FREEZE_COMMIT_CONTENT_MISMATCH")
    correction_time = checked_time(args.correction_time)
    original = json.loads(args.original_freeze.read_text(encoding="utf-8"))
    corrected = build_corrected_freeze(
        original,
        original_path=str(relative),
        original_sha256=original_sha256,
        original_commit=args.superseded_freeze_commit,
        worktree_commit=args.worktree_commit,
        correction_time=correction_time,
        case_root=args.case_root,
    )
    serialized = json.dumps(corrected, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    corrected_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if not args.dry_run:
        write_json(args.output, corrected)
        history = record.setdefault("first_run_freeze_history", [])
        history.append(
            {
                **reference,
                "freeze_commit": args.superseded_freeze_commit,
                "status": "SUPERSEDED_POST_FREEZE_SUMMARY_HASH_CORRECTION_ORIGINAL_PRESERVED",
            }
        )
        output_relative = args.output.resolve().relative_to(ROOT)
        record["first_run_freeze"] = {
            "freeze_id": corrected["freeze_id"],
            "path": str(output_relative),
            "sha256": corrected_sha256,
            "subject_commit": args.worktree_commit,
        }
        record["first_run_freeze_correction_count"] = len(history)
        evidence = record.get("first_run_evidence")
        if not isinstance(evidence, dict):
            raise ValueError("FIRST_RUN_EVIDENCE_MISSING")
        evidence.update(
            {
                "case_state_sha256": corrected["case_state_sha256"],
                "first_run_artifact_hashes": corrected["first_run_artifact_hashes"],
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
        "corrected_freeze_sha256": corrected_sha256,
        "corrected_freeze_payload_sha256": corrected["freeze_hash"],
        "changed_artifacts": corrected["evidence_correction"]["changed_artifacts"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--case-root", type=Path, required=True)
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
        print(json.dumps({"status": "BLOCK", "reason_codes": [str(exc)]}, sort_keys=True))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
