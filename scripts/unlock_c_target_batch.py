#!/usr/bin/env python3
"""Atomically unlock C-target references after all remote first-run freezes pass."""

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

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "benchmarks/case_registry.yaml"
STATE_PATH = ROOT / "state/project_state.json"
RECEIPT_PATH = ROOT / "evals/results/phase-004c-c-batch/batch_reference_unlock.json"
BRANCH = "feat/phase004c-c-target-batch-generalization"
SKILL_PATH = ".agents/skills/cumcm-modeling-evidence"
SKILL_TREE = "a4551c8aa0b6b119823f6ce9df3f0f948339bb33"
FULL_RC3 = "0.2.0-competition-rc3"
CASE_ROOTS = {
    "CUMCM-2022-C-DEVELOPMENT-BATCH-001": ".cache/official_inputs/CUMCM-2022-C-BATCH-001",
    "CUMCM-2021-C-DEVELOPMENT-BATCH-002": ".cache/official_inputs/CUMCM-2021-C-BATCH-002",
    "CUMCM-2020-C-DEVELOPMENT-BATCH-003": ".cache/official_inputs/CUMCM-2020-C-BATCH-003",
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
        raise ValueError("GIT_EVIDENCE_UNAVAILABLE")
    return completed.stdout


def checked_time(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("UNLOCK_TIME_TIMEZONE_REQUIRED")
    return value


def parse_commit_bindings(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        case_id, separator, commit = value.partition("=")
        if not separator or case_id in result or not HEX40.fullmatch(commit):
            raise ValueError("FREEZE_COMMIT_BINDING_INVALID")
        result[case_id] = commit
    if set(result) != set(CASE_ROOTS):
        raise ValueError("FREEZE_COMMIT_BINDING_SET_INVALID")
    return result


def validate_search_log(path: Path) -> int:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise ValueError("PRE_FREEZE_SEARCH_LOG_EMPTY")
    for row in rows:
        if (
            not isinstance(row, dict)
            or row.get("no_solution_exposure") is not True
            or row.get("answer_state") != "SEALED"
            or any(
                token in str(row.get("access_class", "")).upper()
                for token in ("SOLUTION", "ANSWER", "REFERENCE_PAPER")
            )
        ):
            raise ValueError("PRE_FREEZE_SEARCH_LOG_EXPOSURE_UNRESOLVED")
    return len(rows)


def verify_live_case(
    record: dict[str, Any], freeze: dict[str, Any], case_root: Path
) -> dict[str, Any]:
    if file_hash(case_root / "case_state.json") != freeze.get("case_state_sha256"):
        raise ValueError("CASE_STATE_HASH_DRIFT")
    artifacts = freeze.get("first_run_artifact_hashes")
    manifests = freeze.get("run_manifest_hashes")
    if not isinstance(artifacts, dict) or not isinstance(manifests, dict) or not manifests:
        raise ValueError("FIRST_RUN_EVIDENCE_MAP_INVALID")
    for relative, expected in {**artifacts, **manifests}.items():
        path = case_root / str(relative)
        if not path.is_file() or file_hash(path) != expected:
            raise ValueError(f"FIRST_RUN_LIVE_EVIDENCE_DRIFT:{relative}")
    raw_hashes = {
        str(record.get("problem_source")): str(record.get("problem_hash")),
        **{str(path): str(digest) for path, digest in record.get("data_hashes", {}).items()},
    }
    for relative, expected in raw_hashes.items():
        path = case_root / relative
        if not path.is_file() or file_hash(path) != expected:
            raise ValueError(f"ORIGINAL_INPUT_HASH_DRIFT:{relative}")
    search = case_root / "research/pre_freeze_search_log.jsonl"
    if file_hash(search) != freeze.get("search_log_hash"):
        raise ValueError("PRE_FREEZE_SEARCH_LOG_HASH_DRIFT")
    return {
        "case_state": freeze.get("case_state"),
        "case_state_sha256": freeze.get("case_state_sha256"),
        "run_manifest_count": len(manifests),
        "search_log_event_count": validate_search_log(search),
        "original_input_count": len(raw_hashes),
        "live_evidence_verified": True,
    }


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


def unlock(args: argparse.Namespace) -> dict[str, Any]:
    unlock_time = checked_time(args.unlock_time)
    bindings = parse_commit_bindings(args.freeze_commit)
    local_head = git_bytes("rev-parse", "HEAD").decode().strip()
    remote_lines = (
        git_bytes("ls-remote", "--heads", args.remote, f"refs/heads/{args.branch}")
        .decode()
        .splitlines()
    )
    remote_heads = [line.split()[0] for line in remote_lines if line.split()]
    if remote_heads != [local_head]:
        raise ValueError("LOCAL_REMOTE_HEAD_MISMATCH")
    remote_head = remote_heads[0]
    current_tree = git_bytes("rev-parse", f"HEAD:{SKILL_PATH}").decode().strip()
    if current_tree != SKILL_TREE:
        raise ValueError("FORMAL_SKILL_TREE_DRIFT")
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    records = {
        case.get("case_id"): case
        for case in registry.get("cases", [])
        if isinstance(case, dict) and case.get("case_id") in CASE_ROOTS
    }
    if set(records) != set(CASE_ROOTS):
        raise ValueError("BATCH_CASE_SET_INVALID")
    case_receipts: list[dict[str, Any]] = []
    for case_id, relative_root in CASE_ROOTS.items():
        record = records[case_id]
        reference = record.get("first_run_freeze")
        if (
            record.get("first_run_status") != "FROZEN"
            or record.get("answer_access_status") != "SEALED"
            or record.get("reference_unlock") != "LOCKED"
            or not isinstance(reference, dict)
        ):
            raise ValueError(f"CASE_NOT_ELIGIBLE_FOR_BATCH_UNLOCK:{case_id}")
        freeze_path = ROOT / str(reference.get("path"))
        if not freeze_path.is_file() or file_hash(freeze_path) != reference.get("sha256"):
            raise ValueError(f"CURRENT_FREEZE_HASH_DRIFT:{case_id}")
        freeze_commit = bindings[case_id]
        committed = git_bytes("show", f"{freeze_commit}:{reference['path']}")
        if hashlib.sha256(committed).hexdigest() != reference.get("sha256"):
            raise ValueError(f"FREEZE_COMMIT_CONTENT_MISMATCH:{case_id}")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", freeze_commit, remote_head],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if ancestor.returncode != 0:
            raise ValueError(f"FREEZE_COMMIT_NOT_ON_REMOTE_BRANCH:{case_id}")
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        if (
            freeze.get("case_id") != case_id
            or freeze.get("answer_state_at_freeze") != "SEALED"
            or freeze.get("batch_skill_version") != FULL_RC3
            or freeze.get("formal_skill_tree") != SKILL_TREE
        ):
            raise ValueError(f"CURRENT_FREEZE_IDENTITY_INVALID:{case_id}")
        live = verify_live_case(record, freeze, ROOT / relative_root)
        case_receipts.append(
            {
                "case_id": case_id,
                "freeze_id": freeze.get("freeze_id"),
                "freeze_path": reference["path"],
                "freeze_sha256": reference["sha256"],
                "freeze_commit": freeze_commit,
                **live,
            }
        )
    receipt = {
        "schema_version": "1.0.0",
        "artifact_type": "c_target_batch_reference_unlock",
        "batch_id": "C-TARGET-BATCH-001",
        "status": "UNLOCKED_AFTER_ALL_FIRST_RUN_FREEZES",
        "unlock_time": unlock_time,
        "branch": args.branch,
        "remote": args.remote,
        "local_head": local_head,
        "remote_head": remote_head,
        "formal_skill_version": FULL_RC3,
        "formal_skill_tree": current_tree,
        "all_answers_sealed_at_freeze": True,
        "all_freeze_checks_passed": True,
        "all_freeze_commits_remote_ancestors": True,
        "cases": case_receipts,
    }
    receipt["unlock_payload_sha256"] = canonical_hash(receipt)
    serialized = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    receipt_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if not args.dry_run:
        write_json(RECEIPT_PATH, receipt)
        for case in records.values():
            case["answer_access_status"] = "UNLOCKED_AFTER_FIRST_RUN"
            case["reference_unlock"] = "UNLOCKED_AFTER_ALL_FIRST_RUN_FREEZES"
            case["unlock_status"] = "UNLOCKED_AFTER_FIRST_RUN"
            case["unlock_time"] = unlock_time
            case["unlock_receipt"] = {
                "path": str(RECEIPT_PATH.relative_to(ROOT)),
                "sha256": receipt_sha256,
                "verified_remote_sha": remote_head,
            }
        write_yaml(REGISTRY_PATH, registry)
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        state["technical_adjudication_status"] = "C_TARGET_BATCH_POSTMORTEM_IN_PROGRESS"
        state["subphase"] = "C-TARGET-UNIFIED-REFERENCE-REVIEW-AND-POSTMORTEM"
        state["batch_reference_unlocked"] = True
        write_json(STATE_PATH, state)
    return {
        "status": "PASS",
        "dry_run": args.dry_run,
        "batch_id": "C-TARGET-BATCH-001",
        "case_count": len(case_receipts),
        "answer_access_status": "UNLOCKED_AFTER_FIRST_RUN",
        "receipt_sha256": receipt_sha256,
        "unlock_payload_sha256": receipt["unlock_payload_sha256"],
        "remote_head": remote_head,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-commit", action="append", default=[], required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default=BRANCH)
    parser.add_argument("--unlock-time", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = unlock(args)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "BLOCK", "reason_codes": [str(exc)]}, sort_keys=True))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
