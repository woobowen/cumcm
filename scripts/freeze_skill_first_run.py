#!/usr/bin/env python3
"""Freeze a registered blind first run before any answer unlock."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "benchmarks/case_registry.yaml"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_time(value: str | None, code: str) -> str:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(code) from exc
    return value


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


def freeze(args: argparse.Namespace) -> dict[str, Any]:
    registry = read_registry(args.registry)
    matches = [case for case in registry["cases"] if case.get("case_id") == args.case_id]
    if len(matches) != 1:
        raise ValueError("CASE_REGISTRATION_NOT_UNIQUE")
    record = matches[0]
    if record.get("answer_access_status") != "SEALED":
        raise ValueError("ANSWER_ALREADY_UNLOCKED")
    if record.get("first_run_status") != "IN_PROGRESS":
        raise ValueError("FIRST_RUN_NOT_IN_PROGRESS")
    state_path = args.case_root / "case_state.json"
    if not state_path.is_file():
        raise ValueError("CASE_STATE_MISSING")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("case_id") != args.case_id:
        raise ValueError("CASE_STATE_ID_MISMATCH")
    if state.get("skill_version") != record.get("skill_version"):
        raise ValueError("CASE_STATE_SKILL_VERSION_MISMATCH")
    if (
        state.get("state") not in {"READY_FOR_PAPER_HANDOFF", "STALE", "REJECTED"}
        and not args.blocked_reason_code
    ):
        raise ValueError("FIRST_RUN_NOT_TERMINAL_OR_BLOCKED")
    manifests = sorted(args.case_root.glob("runs/*/manifest.json"))
    if not manifests:
        raise ValueError("FIRST_RUN_MANIFEST_MISSING")
    manifest_hashes: dict[str, str] = {}
    for path in manifests:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("code_commit") != record.get("skill_commit"):
            raise ValueError("RUN_SKILL_COMMIT_MISMATCH")
        manifest_hashes[str(path.relative_to(args.case_root))] = file_hash(path)
    freeze_time = iso_time(args.freeze_time, "FREEZE_TIME_INVALID")
    evidence = {
        "skill_version": record["skill_version"],
        "skill_commit": record["skill_commit"],
        "case_state": state["state"],
        "case_state_sha256": file_hash(state_path),
        "run_manifest_hashes": manifest_hashes,
        "blocked_reason_code": args.blocked_reason_code,
    }
    if not args.dry_run:
        record["first_run_status"] = "FROZEN"
        record["freeze_time"] = freeze_time
        record["first_run_evidence"] = evidence
        if args.unlock_time:
            record["unlock_time"] = iso_time(args.unlock_time, "UNLOCK_TIME_INVALID")
            record["answer_access_status"] = "UNLOCKED_AFTER_FIRST_RUN"
            if record.get("set_type") != "DEVELOPMENT":
                record["set_type"] = "DEVELOPMENT"
        write_registry(args.registry, registry)
    return {
        "status": "PASS",
        "dry_run": args.dry_run,
        "case_id": args.case_id,
        "first_run_status": "FROZEN",
        "answer_access_status": "UNLOCKED_AFTER_FIRST_RUN" if args.unlock_time else "SEALED",
        "freeze_time": freeze_time,
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--freeze-time")
    parser.add_argument("--unlock-time")
    parser.add_argument("--blocked-reason-code")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = freeze(args)
    except (OSError, ValueError, yaml.YAMLError) as exc:
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
