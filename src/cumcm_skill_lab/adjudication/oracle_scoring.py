"""Case-specific deterministic oracles for the frozen project-authored synthetic cases."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .models import canonical_json, check_or_write, read_json, sha256_json


def _contains_all(value: Any, terms: tuple[str, ...]) -> bool:
    text = canonical_json(value).lower()
    return all(term.lower() in text for term in terms)


def oracle_correctness(case_id: str, observation: dict, run: dict | None = None) -> dict:
    checks: dict[str, bool]
    if observation.get("completion_status") != "COMPLETED":
        checks = {"completed": False}
    elif case_id == "CASE-001":
        checks = {
            "exact_allocation": _contains_all(observation.get("baseline"), ("3 trips", "2 trips")),
            "unit_total": _contains_all(observation.get("baseline"), ("3000", "600")),
            "crew_constraint": _contains_all(observation.get("baseline"), ("7.5", "8")),
        }
    elif case_id == "CASE-002":
        checks = {
            "leakage_fields": _contains_all(
                observation.get("data_findings"), ("future_score", "target_copy")
            ),
            "duplicate": "5" in canonical_json(observation.get("data_findings")),
            "plausible_extreme_preserved": _contains_all(
                observation.get("data_findings"), ("99", "250")
            ),
        }
    elif case_id == "CASE-003":
        checks = {
            "exact_optimum": bool(
                re.search(r"(?:value|optimum)[^0-9]{0,20}19\b", canonical_json(observation), re.I)
            ),
            "selected_pair": _contains_all(observation, ("a+b", "10 credits", "7 worker-days")),
            "executed": bool(observation.get("commands_executed"))
            and bool(observation.get("tests_verified")),
        }
    elif case_id == "CASE-004":
        text = canonical_json(observation)
        checks = {
            "leakage_excluded": _contains_all(
                observation.get("formalization"), ("future_target", "target_proxy", "regime")
            ),
            "temporal_split": _contains_all(observation, ("train", "validation", "test")),
            "baseline_selected_by_validation": _contains_all(
                observation.get("claims"), ("identity baseline", "not a fitted regression")
            ),
            "no_test_selection_claim": "selected on test" not in text.lower(),
        }
    elif case_id == "CASE-005":
        checks = {
            "descendant_closure": _contains_all(observation, ("descendant", "stale")),
            "restart_stage": _contains_all(observation, ("earliest", "restart")),
            "executable_check": bool(observation.get("commands_executed"))
            and bool(observation.get("tests_verified")),
        }
    elif case_id == "CASE-006":
        checks = {
            "supported_count": _contains_all(observation.get("baseline"), ("1 of 4",)),
            "source_binding": _contains_all(observation, ("src-auth", "src-mismatch")),
            "unsupported_separated": _contains_all(
                observation.get("claims"), ("unsupported", "always wins")
            ),
        }
    else:
        checks = {"known_case": False}
    if run is not None:
        checks["run_bound"] = all(
            observation.get(key) == run.get(key)
            for key in ("evaluation_id", "case_id", "anonymous_arm_id", "run_index")
        )
        checks["schema_valid"] = bool(run.get("schema_valid"))
    return {
        "role": "DETERMINISTIC_ORACLE_CORRECTNESS",
        "checks": checks,
        "passed": bool(checks) and all(checks.values()),
        "is_coverage": False,
    }


def rescore_oracles(root: Path) -> dict:
    cells = []
    for path in sorted((root / "evals/results/phase-002/scores").rglob("*.json")):
        score = read_json(path)
        arm, case_id, index = (
            score["anonymous_arm_id"],
            score["case_id"],
            score["run_index"],
        )
        observation = read_json(
            root / "evals/results/phase-002/observations" / arm / case_id / f"run-{index:03d}.json"
        )
        run = read_json(
            root / "evals/results/phase-002/runs" / arm / case_id / f"run-{index:03d}.json"
        )
        cells.append(
            {
                "anonymous_arm_id": arm,
                "case_id": case_id,
                "run_index": index,
                **oracle_correctness(case_id, observation, run),
            }
        )
    value = {"schema_version": "1.0.0", "cells": cells}
    value["content_hash"] = sha256_json(value)
    return value


def write_oracles(root: Path, *, check: bool) -> list[str]:
    return check_or_write(
        root / "evals/results/phase-002a/oracle_correctness/oracles.json",
        rescore_oracles(root),
        check=check,
    )
