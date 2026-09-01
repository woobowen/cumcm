"""Classify Phase 002 cells without allowing recovery evidence into ranking."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .models import check_or_write, read_json, sha256_json


def classify_cells(root: Path) -> dict:
    recovery_keys = {
        tuple(path.relative_to(root / "evals/results/phase-002/recoveries").parts[:2])
        for path in (root / "evals/results/phase-002/recoveries").rglob("*.recovery.json")
    }
    cells: list[dict] = []
    primary_by_arm: dict[str, set[str]] = defaultdict(set)
    for path in sorted((root / "evals/results/phase-002/scores").rglob("*.json")):
        score = read_json(path)
        key = (score["anonymous_arm_id"], score["case_id"])
        classification = "RECOVERY_AFFECTED" if key in recovery_keys else "PRIMARY_COMPLETE"
        if classification == "PRIMARY_COMPLETE":
            primary_by_arm[key[0]].add(key[1])
        cells.append(
            {
                "anonymous_arm_id": key[0],
                "case_id": key[1],
                "run_index": score["run_index"],
                "classification": classification,
                "ranking_eligible": classification == "PRIMARY_COMPLETE",
                "score_path": path.relative_to(root).as_posix(),
            }
        )
    failed_attempts = []
    for path in sorted((root / "evals/results/phase-002/runs").rglob("*.json")):
        run = read_json(path)
        if run["completion_status"] == "FAILED":
            failed_attempts.append(path.relative_to(root).as_posix())
    balanced = sorted(set.intersection(*primary_by_arm.values()))
    return {
        "schema_version": "1.0.0",
        "classification_id": "ELIGIBILITY-PHASE-002A",
        "cells": cells,
        "failed_attempts": failed_attempts,
        "summary": {
            "scored_cells": len(cells),
            "primary_complete": sum(c["ranking_eligible"] for c in cells),
            "recovery_affected": sum(not c["ranking_eligible"] for c in cells),
            "failed_attempts": len(failed_attempts),
            "balanced_cases": balanced,
            "balanced_case_count": len(balanced),
            "repeats": 1,
            "minimum_balanced_cases": 4,
            "minimum_repeats": 2,
            "comparative_sufficiency": "INSUFFICIENT",
        },
    }


def write_eligibility(root: Path, *, check: bool) -> dict:
    value = classify_cells(root)
    value["content_hash"] = sha256_json(value)
    path = root / "evals/results/phase-002a/eligibility/classification.json"
    errors = check_or_write(path, value, check=check)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, **value["summary"]}
