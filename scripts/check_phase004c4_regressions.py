#!/usr/bin/env python3
"""Check frozen Phase 004C4 historical, auxiliary and controller regressions."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evals/results/phase-004c4/historical_and_auxiliary_regressions.json"


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    evidence = _read(root / EVIDENCE.relative_to(ROOT))
    payload = dict(evidence)
    declared_hash = payload.pop("payload_sha256", None)
    if declared_hash != _canonical_hash(payload):
        errors.append("PHASE004C4_REGRESSION_PAYLOAD_HASH_MISMATCH")
    if (
        evidence.get("implementation_commit") != "cd02e61994b906364789c65609de695b6912f1c7"
        or evidence.get("status") != "PASS"
    ):
        errors.append("PHASE004C4_REGRESSION_IDENTITY_INVALID")

    records: list[dict[str, Any]] = []
    records.append(evidence.get("current_claim_replay", {}))
    records.extend(evidence.get("preserved_evidence", {}).values())
    records.extend(
        item
        for item in evidence.get("current_skill_regressions", {}).values()
        if isinstance(item, dict) and "sha256" in item
    )
    for record in records:
        path = root / str(record.get("path", ""))
        if not path.is_file() or record.get("sha256") != _hash(path):
            errors.append(f"PHASE004C4_REGRESSION_FILE_DRIFT:{record.get('path')}")

    claim_replay = _read(root / evidence.get("current_claim_replay", {}).get("path", ""))
    cases = claim_replay.get("cases")
    if (
        claim_replay.get("status") != "PASS"
        or not isinstance(cases, list)
        or len(cases) != 6
        or any(
            item.get("status") != "PASS"
            or item.get("new_model_runs") != 0
            or item.get("old_files_unchanged") is not True
            for item in cases
        )
    ):
        errors.append("PHASE004C4_HISTORICAL_CLAIM_REPLAY_INVALID")

    synthetic = _read(root / "evals/results/phase-004c4/synthetic_e2e/result.json")
    negative = _read(root / "evals/results/phase-004c4/original_negative_results.json")
    if synthetic.get("passed") != 2 or synthetic.get("failed") != 0:
        errors.append("PHASE004C4_SYNTHETIC_E2E_INVALID")
    if any(
        negative.get(key) != value
        for key, value in (
            ("scenario_count", 30),
            ("passed", 30),
            ("failed", 0),
            ("unhandled_exceptions", 0),
            ("sensitive_values_reported", 0),
        )
    ):
        errors.append("PHASE004C4_NEGATIVE_MATRIX_INVALID")

    invariants = evidence.get("invariants", {})
    if invariants != {
        "formal_skill_count": 1,
        "historical_artifact_mutation_count": 0,
        "problem_hardcoding_count": 0,
        "answer_leakage_count": 0,
        "secret_count": 0,
        "third_party_code_execution_count": 0,
        "third_party_integrated": False,
        "heldout_2025_access_count": 0,
    }:
        errors.append("PHASE004C4_REGRESSION_INVARIANTS_INVALID")
    if len(list((root / ".agents/skills").glob("*/SKILL.md"))) != 1:
        errors.append("PHASE004C4_FORMAL_SKILL_COUNT_INVALID")
    if subprocess.run(
        ["git", "ls-files", ".cache"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.strip():
        errors.append("PHASE004C4_CACHE_TRACKING_INVALID")

    errors = sorted(set(errors))
    return {
        "status": "PASS" if not errors else "BLOCK",
        "error_count": len(errors),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    result = evaluate()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
