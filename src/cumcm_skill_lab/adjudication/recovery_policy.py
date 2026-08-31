"""Keep recovery observations as gap evidence while excluding them from rankings."""

from __future__ import annotations

from pathlib import Path

from .models import check_or_write, file_sha256, read_json, sha256_json


def recovery_gap_evidence(root: Path) -> dict:
    records = []
    for path in sorted((root / "evals/results/phase-002/recoveries").rglob("*.json")):
        item = read_json(path)
        records.append(
            {
                "recovery_path": path.relative_to(root).as_posix(),
                "recovery_sha256": file_sha256(path),
                "anonymous_arm_id": item["anonymous_arm_id"],
                "case_id": item["case_id"],
                "allowed_use": "GAP_EVIDENCE_ONLY",
                "ranking_eligible": False,
                "reason": item.get("false_positive_reason", "recovery treatment differs"),
            }
        )
    value = {
        "schema_version": "1.0.0",
        "policy": "RECOVERY_EXCLUDED_FROM_COMPARATIVE_RANKING",
        "records": records,
        "count": len(records),
    }
    value["content_hash"] = sha256_json(value)
    return value


def write_recovery_policy(root: Path, *, check: bool) -> list[str]:
    return check_or_write(
        root / "evals/results/phase-002a/recovery_gap_evidence/recovery.json",
        recovery_gap_evidence(root),
        check=check,
    )
