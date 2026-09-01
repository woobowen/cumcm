"""Audit coverage-only hard-failure summaries against authoritative run bindings."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cumcm_skill_lab.eval.scoring import detect_hard_failures

from .attempt_ledger import load_attempts
from .models import RESULT_ROOT, check_or_write, hashed_body, read_json, sha256_json, write_json

AUDIT_PATH = RESULT_ROOT / "score_audit/audit.json"


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_score_audit(
    root: Path, *, batch_id: int, audited_at: str | None = None
) -> dict[str, Any]:
    records = []
    for attempt in load_attempts(root):
        attempt_id = attempt["attempt_id"]
        observation = read_json(root / RESULT_ROOT / "runs" / attempt_id / "observation.json")
        coverage = read_json(root / RESULT_ROOT / "scores" / f"{attempt_id}.json")
        recomputed = detect_hard_failures(
            observation,
            {
                "completion_status": attempt["completion_status"],
                "schema_valid": attempt["schema_valid"],
                "files_written": attempt["files_written"],
            },
        )
        coverage_only = coverage["hard_failures"]
        authoritative = attempt["hard_failures"]
        records.append(
            {
                "attempt_id": attempt_id,
                "anonymous_arm_id": attempt["anonymous_arm_id"],
                "attempt_hash": attempt["attempt_hash"],
                "coverage_hash": coverage["coverage_hash"],
                "attempt_hard_failures": authoritative,
                "recomputed_hard_failures": recomputed,
                "coverage_hard_failures": coverage_only,
                "authoritative_match": authoritative == recomputed,
                "coverage_binding_mismatch": coverage_only != recomputed,
                "classification": (
                    "COVERAGE_BINDING_MISMATCH" if coverage_only != recomputed else "CONSISTENT"
                ),
                "coverage_proves_correctness": False,
                "coverage_is_hard_gate_source": False,
            }
        )
    body = {
        "schema_version": "1.0.0",
        "audit_id": "PHASE-002D-COVERAGE-BINDING-AUDIT",
        "batch_id": batch_id,
        "audited_at": audited_at or _now(),
        "records": records,
        "authoritative_attempt_binding_pass": all(
            record["authoritative_match"] for record in records
        ),
        "coverage_binding_mismatch_count": sum(
            record["coverage_binding_mismatch"] for record in records
        ),
        "coverage_excluded_from_hard_gates": True,
        "original_scores_modified": False,
        "status": (
            "PASS_WITH_COVERAGE_LIMITATION"
            if any(record["coverage_binding_mismatch"] for record in records)
            else "PASS"
        ),
    }
    return hashed_body(body, "audit_hash")


def validate_score_audit(value: dict[str, Any]) -> list[str]:
    errors = []
    body = dict(value)
    recorded = body.pop("audit_hash", None)
    if sha256_json(body) != recorded:
        errors.append("SCORE_AUDIT_HASH_MISMATCH")
    if not value["records"]:
        errors.append("SCORE_AUDIT_EMPTY")
    if not value["authoritative_attempt_binding_pass"]:
        errors.append("AUTHORITATIVE_ATTEMPT_BINDING_FAILED")
    if not value["coverage_excluded_from_hard_gates"]:
        errors.append("COVERAGE_USED_AS_HARD_GATE")
    if value["original_scores_modified"]:
        errors.append("ORIGINAL_SCORE_MUTATED")
    return errors


def check_or_write_score_audit(root: Path, *, batch_id: int | None, check: bool) -> dict[str, Any]:
    existing = read_json(root / AUDIT_PATH) if (root / AUDIT_PATH).is_file() else None
    if existing is None and batch_id is None:
        raise RuntimeError("SCORE_AUDIT_BATCH_ID_REQUIRED_FOR_INITIAL_WRITE")
    selected_batch = batch_id if batch_id is not None else existing["batch_id"]
    audited_at = (
        existing["audited_at"]
        if existing is not None and existing["batch_id"] == selected_batch
        else None
    )
    expected = build_score_audit(root, batch_id=selected_batch, audited_at=audited_at)
    errors = validate_score_audit(expected)
    errors.extend(check_or_write(root / AUDIT_PATH, expected, check=check))
    snapshot = root / RESULT_ROOT / f"score_audit/batches/batch-{selected_batch:03d}.json"
    if check:
        if not snapshot.is_file() or read_json(snapshot) != expected:
            errors.append("SCORE_AUDIT_BATCH_SNAPSHOT_MISMATCH")
    elif snapshot.is_file() and read_json(snapshot) != expected:
        errors.append("SCORE_AUDIT_BATCH_SNAPSHOT_IMMUTABLE")
    elif not snapshot.is_file():
        write_json(snapshot, expected)
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "batch_id": selected_batch,
        "coverage_binding_mismatch_count": expected["coverage_binding_mismatch_count"],
        "audit_result": expected["status"],
        "audit_hash": expected["audit_hash"],
    }
