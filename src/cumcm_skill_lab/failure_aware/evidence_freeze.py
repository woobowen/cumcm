"""Freeze and verify the immutable Phase 002D evidence used by Phase 002D-R1."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import (
    HISTORICAL_ROOTS,
    RESULT_ROOT,
    SOURCE_ROOT,
    check_or_write,
    file_hashes,
    file_sha256,
    read_json,
    sha256_json,
)

FREEZE_PATH = RESULT_ROOT / "input_freeze_manifest.json"
FREEZE_ID = "PHASE-002D-R1-INPUT-FREEZE-001"
SUBJECT_COMMIT = "d59f4b8a36fa3c15e06ec0aceb948cd2bafd2abc"
CREATED_AT = "2026-09-01T23:12:32+08:00"

RULE_PATHS = (
    "rules/automated_adjudication_rules.yaml",
    "rules/dynamic_eval_rules.yaml",
    "rules/evidence_hierarchy.yaml",
    "rules/evidence_rules.yaml",
    "rules/native_subagent_audit_rules.yaml",
    "rules/phase002d_r1_workflow_rules.yaml",
    "rules/pre_adjudication_rules.yaml",
    "rules/workflow_rules.yaml",
    "adjudication/policies/phase-002d.yaml",
    "adjudication/configs/phase-002d.yaml",
)
CONTRACT_PATHS = (
    "contracts/evidence_sufficiency.schema.json",
    "contracts/expansion_attempt.schema.json",
    "contracts/expansion_budget.schema.json",
    "contracts/expansion_cost.schema.json",
    "contracts/expansion_run.schema.json",
    "contracts/expansion_schedule.schema.json",
    "contracts/primary_eligibility.schema.json",
)


def _selected_hashes(root: Path, pattern: str) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(root.glob(pattern))
        if path.is_file()
    }


def _failed_attempt_hashes(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in sorted((root / SOURCE_ROOT / "attempts").glob("*.json")):
        attempt = read_json(path)
        if (
            attempt["completion_status"] != "COMPLETED"
            or attempt["hard_failures"]
            or not attempt["primary_eligible"]
        ):
            values[path.relative_to(root).as_posix()] = file_sha256(path)
    return values


def build_input_freeze(root: Path) -> dict[str, Any]:
    source_freeze = read_json(root / SOURCE_ROOT / "input_freeze_manifest.json")
    cohort = read_json(root / SOURCE_ROOT / "cohort/cohort.json")
    budget = read_json(root / SOURCE_ROOT / "budget/frozen_budget.json")
    schedule = read_json(root / SOURCE_ROOT / "schedule/schedule.json")
    attempt_ledger = read_json(root / SOURCE_ROOT / "attempt_ledger.json")
    sufficiency = read_json(root / SOURCE_ROOT / "sufficiency/evidence_sufficiency.json")
    cost = read_json(root / SOURCE_ROOT / "cost/cost.json")

    historical_file_hashes = {
        directory.as_posix(): file_hashes(root, directory) for directory in HISTORICAL_ROOTS
    }
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "freeze_id": FREEZE_ID,
        "phase": "PHASE-EVIDENCE-EXPANSION-002D",
        "subphase": "PHASE-002D-R1-FAILURE-AWARE-OUTCOME-ADJUDICATION",
        "created_at": CREATED_AT,
        "subject_commit": SUBJECT_COMMIT,
        "source_phase002d_input_freeze_hash": file_sha256(
            root / SOURCE_ROOT / "input_freeze_manifest.json"
        ),
        "source_phase002d_freeze_id": source_freeze["freeze_id"],
        "cohort_hash": cohort["cohort_hash"],
        "model": cohort["model"],
        "reasoning_setting": cohort["reasoning_setting"],
        "transport_profile": cohort["transport_profile"],
        "budget_hash": budget["budget_hash"],
        "schedule_hash": schedule["schedule_hash"],
        "attempt_ledger_hash": attempt_ledger["ledger_hash"],
        "command_ledger_hash": file_sha256(root / SOURCE_ROOT / "closure/command_ledger.json"),
        "attempt_record_hashes": _selected_hashes(root, f"{SOURCE_ROOT}/attempts/*.json"),
        "run_record_hashes": _selected_hashes(root, f"{SOURCE_ROOT}/runs/*/*.json"),
        "failure_record_hashes": _failed_attempt_hashes(root),
        "eligibility_record_hashes": _selected_hashes(root, f"{SOURCE_ROOT}/eligibility/*.json"),
        "oracle_record_hashes": _selected_hashes(root, f"{SOURCE_ROOT}/oracle/*.json"),
        "process_evidence_hashes": _selected_hashes(root, f"{SOURCE_ROOT}/process_evidence/*.json"),
        "sufficiency_record_hash": file_sha256(
            root / SOURCE_ROOT / "sufficiency/evidence_sufficiency.json"
        ),
        "sufficiency_result": sufficiency["result"],
        "cost_record_hash": file_sha256(root / SOURCE_ROOT / "cost/cost.json"),
        "cost_hash": cost["cost_hash"],
        "runner_version_hash": file_sha256(root / "src/cumcm_skill_lab/expansion/runner.py"),
        "scorer_version_hash": file_sha256(root / "src/cumcm_skill_lab/expansion/scoring.py"),
        "rule_hashes": {path: file_sha256(root / path) for path in RULE_PATHS},
        "contract_hashes": {path: file_sha256(root / path) for path in CONTRACT_PATHS},
        "historical_tree_hashes": {
            directory: sha256_json(hashes) for directory, hashes in historical_file_hashes.items()
        },
        "phase002d_file_hashes": historical_file_hashes[SOURCE_ROOT.as_posix()],
        "historical_evidence_immutable": True,
        "original_budget_mutation_allowed": False,
    }
    body["manifest_hash"] = sha256_json(body)
    return body


def verify_input_freeze(root: Path, manifest: dict[str, Any] | None = None) -> list[str]:
    path = root / FREEZE_PATH
    if manifest is None:
        if not path.is_file():
            return ["PHASE002D_R1_INPUT_FREEZE_MISSING"]
        manifest = read_json(path)
    errors: list[str] = []
    body = dict(manifest)
    recorded_hash = body.pop("manifest_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("PHASE002D_R1_MANIFEST_HASH_MISMATCH")
    if manifest.get("subject_commit") != SUBJECT_COMMIT:
        errors.append("PHASE002D_R1_SUBJECT_COMMIT_MISMATCH")

    for directory in HISTORICAL_ROOTS:
        actual = sha256_json(file_hashes(root, directory))
        expected = manifest.get("historical_tree_hashes", {}).get(directory.as_posix())
        if actual != expected:
            errors.append(f"HISTORICAL_INPUT_MUTATED:{directory.as_posix()}")
    for group in (
        "attempt_record_hashes",
        "run_record_hashes",
        "failure_record_hashes",
        "eligibility_record_hashes",
        "oracle_record_hashes",
        "process_evidence_hashes",
        "phase002d_file_hashes",
        "rule_hashes",
        "contract_hashes",
    ):
        for relative, expected in manifest.get(group, {}).items():
            target = root / relative
            if not target.is_file() or file_sha256(target) != expected:
                errors.append(f"FROZEN_HASH_MISMATCH:{group}:{relative}")
    return sorted(set(errors))


def check_or_write_input_freeze(root: Path, *, check: bool) -> dict[str, Any]:
    if check:
        manifest = read_json(root / FREEZE_PATH) if (root / FREEZE_PATH).is_file() else {}
        errors = verify_input_freeze(root, manifest if manifest else None)
    else:
        manifest = build_input_freeze(root)
        errors = check_or_write(root / FREEZE_PATH, manifest, check=False)
        errors.extend(verify_input_freeze(root, manifest))
    return {
        "status": "PASS" if not errors else "INPUT_FREEZE_BROKEN",
        "errors": errors,
        "freeze_id": manifest.get("freeze_id"),
        "manifest_hash": manifest.get("manifest_hash"),
        "subject_commit": manifest.get("subject_commit"),
    }
