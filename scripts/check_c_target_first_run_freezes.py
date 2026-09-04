#!/usr/bin/env python3
"""Validate C-target per-case first-run freezes without reading ignored workspaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "benchmarks/case_registry.yaml"
EXPECTED_CASES = [
    "CUMCM-2022-C-DEVELOPMENT-BATCH-001",
    "CUMCM-2021-C-DEVELOPMENT-BATCH-002",
    "CUMCM-2020-C-DEVELOPMENT-BATCH-003",
]
FORMAL_SKILL_VERSION = "0.2.0-competition-rc3"
FORMAL_SKILL_COMMIT = "8a2a813ff34d8c2701c64ff9d959848e7b88c27c"
FORMAL_SKILL_TREE = "a4551c8aa0b6b119823f6ce9df3f0f948339bb33"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_FREEZE_FIELDS = {
    "case_id",
    "batch_id",
    "batch_position",
    "set_type",
    "problem_type",
    "answer_state_at_freeze",
    "model_prior_status",
    "formal_skill_version",
    "formal_skill_commit",
    "formal_skill_tree",
    "problem_hash",
    "data_hashes",
    "search_log_hash",
    "source_ledger_hash",
    "requirement_trace_hash",
    "data_audit_hash",
    "model_portfolio_hash",
    "experiment_plan_hash",
    "case_code_tree_hash",
    "run_manifest_hashes",
    "failure_hashes",
    "result_hashes",
    "robustness_hash",
    "claim_evidence_hash",
    "handoff_hash",
    "case_state",
    "timing_hash",
    "manual_intervention_count",
    "freeze_time",
    "freeze_hash",
}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def git_commit_exists(root: Path, commit: str) -> bool:
    if not HEX40.fullmatch(commit):
        return False
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    return completed.returncode == 0


def validate_freeze(freeze: dict[str, Any], record: dict[str, Any]) -> list[str]:
    case_id = str(record.get("case_id", "UNKNOWN"))
    errors: list[str] = []
    missing = sorted(REQUIRED_FREEZE_FIELDS - freeze.keys())
    if missing:
        errors.append(f"FIRST_RUN_FREEZE_FIELDS_MISSING:{case_id}:{','.join(missing)}")
    payload = dict(freeze)
    payload_hash = payload.pop("freeze_hash", None)
    if not HEX64.fullmatch(str(payload_hash or "")) or canonical_hash(payload) != payload_hash:
        errors.append(f"FIRST_RUN_FREEZE_PAYLOAD_HASH_MISMATCH:{case_id}")
    if (
        freeze.get("schema_version") != "1.0.0"
        or freeze.get("artifact_type") != "development_first_run_freeze"
        or freeze.get("case_id") != case_id
        or freeze.get("batch_id") != "C-TARGET-BATCH-001"
        or freeze.get("batch_position") != record.get("batch_position")
        or freeze.get("batch_skill_version") != FORMAL_SKILL_VERSION
        or freeze.get("set_type") != "DEVELOPMENT"
        or freeze.get("problem_type") != "C"
        or freeze.get("answer_state_at_freeze") != "SEALED"
        or freeze.get("answer_access_status") != "SEALED"
        or freeze.get("first_run_status") != "FROZEN"
        or freeze.get("model_prior_status") != "MODEL_PRIOR_EXPOSURE_UNVERIFIABLE"
        or freeze.get("formal_skill_version") != FORMAL_SKILL_VERSION
        or freeze.get("formal_skill_commit") != FORMAL_SKILL_COMMIT
        or freeze.get("formal_skill_tree") != FORMAL_SKILL_TREE
        or freeze.get("problem_hash") != record.get("problem_hash")
        or freeze.get("data_hashes") != record.get("data_hashes")
        or freeze.get("case_state")
        not in {"RUN_VALIDATED", "READY_FOR_PAPER_HANDOFF", "REJECTED", "STALE"}
        or not isinstance(freeze.get("manual_intervention_count"), int)
        or isinstance(freeze.get("manual_intervention_count"), bool)
        or freeze.get("manual_intervention_count", -1) < 0
    ):
        errors.append(f"FIRST_RUN_FREEZE_HEADER_INVALID:{case_id}")
    for field in (
        "search_log_hash",
        "source_ledger_hash",
        "requirement_trace_hash",
        "data_audit_hash",
        "model_portfolio_hash",
        "experiment_plan_hash",
        "case_code_tree_hash",
        "robustness_hash",
        "claim_evidence_hash",
        "handoff_hash",
        "timing_hash",
    ):
        if not HEX64.fullmatch(str(freeze.get(field, ""))):
            errors.append(f"FIRST_RUN_FREEZE_HASH_INVALID:{case_id}:{field}")
    for field in ("run_manifest_hashes", "failure_hashes", "result_hashes"):
        values = freeze.get(field)
        if not isinstance(values, dict) or not all(
            isinstance(path, str) and path and HEX64.fullmatch(str(digest))
            for path, digest in values.items()
        ):
            errors.append(f"FIRST_RUN_FREEZE_HASH_MAP_INVALID:{case_id}:{field}")
    if not freeze.get("run_manifest_hashes") and not freeze.get("blocked_reason_code"):
        errors.append(f"FIRST_RUN_FREEZE_RUNS_MISSING:{case_id}")
    return sorted(set(errors))


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    registry_value = yaml.safe_load(
        (root / REGISTRY_PATH.relative_to(ROOT)).read_text(encoding="utf-8")
    )
    records = {
        record.get("case_id"): record
        for record in registry_value.get("cases", [])
        if isinstance(record, dict) and record.get("case_id") in EXPECTED_CASES
    }
    if list(records) != EXPECTED_CASES:
        errors.append("FIRST_RUN_FREEZE_CASE_ORDER_INVALID")
    frozen_count = 0
    for case_id in EXPECTED_CASES:
        record = records.get(case_id, {})
        status = record.get("first_run_status")
        reference = record.get("first_run_freeze")
        if status == "IN_PROGRESS" and reference is None:
            continue
        if status != "FROZEN" or not isinstance(reference, dict):
            errors.append(f"FIRST_RUN_FREEZE_REGISTRY_STATUS_INVALID:{case_id}")
            continue
        frozen_count += 1
        relative = reference.get("path")
        path = root / str(relative)
        if not path.is_file():
            errors.append(f"FIRST_RUN_FREEZE_FILE_MISSING:{case_id}")
            continue
        actual_hash = file_hash(path)
        if reference.get("sha256") != actual_hash:
            errors.append(f"FIRST_RUN_FREEZE_FILE_HASH_MISMATCH:{case_id}")
        freeze = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(freeze, dict):
            errors.append(f"FIRST_RUN_FREEZE_DOCUMENT_INVALID:{case_id}")
            continue
        errors.extend(validate_freeze(freeze, record))
        history = record.get("first_run_freeze_history", [])
        supersedes = freeze.get("supersedes_freeze")
        if history:
            if (
                not isinstance(history, list)
                or len(history) != 1
                or not isinstance(history[0], dict)
                or not isinstance(supersedes, dict)
                or supersedes.get("path") != history[0].get("path")
                or supersedes.get("sha256") != history[0].get("sha256")
                or supersedes.get("commit") != history[0].get("freeze_commit")
                or history[0].get("status") != "SUPERSEDED_METADATA_ONLY_ORIGINAL_PRESERVED"
            ):
                errors.append(f"FIRST_RUN_FREEZE_HISTORY_INVALID:{case_id}")
            else:
                historical_path = root / str(history[0].get("path"))
                if not historical_path.is_file() or file_hash(historical_path) != history[0].get(
                    "sha256"
                ):
                    errors.append(f"FIRST_RUN_FREEZE_HISTORY_FILE_DRIFT:{case_id}")
            correction = freeze.get("metadata_correction", {})
            if (
                not isinstance(correction, dict)
                or correction.get("reason_code") != "RC_BATCH_SKILL_VERSION_SHORT_ALIAS_REJECTED"
                or correction.get("case_evidence_changed") is not False
                or correction.get("run_evidence_changed") is not False
                or correction.get("answer_state_changed") is not False
                or correction.get("original_freeze_preserved") is not True
            ):
                errors.append(f"FIRST_RUN_FREEZE_CORRECTION_INVALID:{case_id}")
        evidence = record.get("first_run_evidence", {})
        if (
            not isinstance(evidence, dict)
            or evidence.get("freeze_sha256") != actual_hash
            or evidence.get("freeze_id") != freeze.get("freeze_id")
            or evidence.get("run_manifest_hashes") != freeze.get("run_manifest_hashes")
            or evidence.get("first_run_artifact_hashes") != freeze.get("first_run_artifact_hashes")
        ):
            errors.append(f"FIRST_RUN_FREEZE_REGISTRY_EVIDENCE_DRIFT:{case_id}")
        subject = str(reference.get("subject_commit", ""))
        if subject != freeze.get("worktree_commit") or not git_commit_exists(root, subject):
            errors.append(f"FIRST_RUN_FREEZE_SUBJECT_COMMIT_INVALID:{case_id}")
    return {
        "batch_id": "C-TARGET-BATCH-001",
        "expected_case_count": len(EXPECTED_CASES),
        "frozen_count": frozen_count,
        "in_progress_count": len(EXPECTED_CASES) - frozen_count,
        "error_count": len(set(errors)),
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    result = evaluate()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
