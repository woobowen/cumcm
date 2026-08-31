"""Structured coverage measurement; intentionally not a correctness score."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import check_or_write, read_json, sha256_json


def structured_coverage(observation: dict[str, Any], fields: list[str]) -> dict:
    present = [field for field in fields if observation.get(field) not in (None, "", [], {})]
    return {
        "role": "STRUCTURED_COVERAGE_ONLY",
        "covered": present,
        "missing": [field for field in fields if field not in present],
        "coverage_fraction": len(present) / len(fields) if fields else 1.0,
        "is_correctness": False,
    }


def rescore_coverage(root: Path) -> dict:
    required = [
        "requirements",
        "formalization",
        "baseline",
        "candidate_models",
        "experiment_design",
        "validation",
        "claims",
        "uncertainties",
    ]
    cells = []
    for path in sorted((root / "evals/results/phase-002/observations").rglob("*.json")):
        observation = read_json(path)
        if observation["completion_status"] != "COMPLETED":
            continue
        result = structured_coverage(observation, required)
        cells.append(
            {
                "anonymous_arm_id": observation["anonymous_arm_id"],
                "case_id": observation["case_id"],
                "run_index": observation["run_index"],
                **result,
            }
        )
    value = {
        "schema_version": "1.0.0",
        "score_type": "STRUCTURED_COVERAGE_NOT_CORRECTNESS",
        "cells": cells,
    }
    value["content_hash"] = sha256_json(value)
    return value


def write_coverage(root: Path, *, check: bool) -> list[str]:
    return check_or_write(
        root / "evals/results/phase-002a/structured_coverage/coverage.json",
        rescore_coverage(root),
        check=check,
    )
