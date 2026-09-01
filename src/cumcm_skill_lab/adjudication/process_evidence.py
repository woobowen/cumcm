"""Evaluate process evidence separately from structured content and mathematical oracles."""

from __future__ import annotations

from pathlib import Path

from .models import check_or_write, read_json, sha256_json


def assess_process(observation: dict, run: dict) -> dict:
    tuple_bound = all(
        observation.get(key) == run.get(key)
        for key in ("evaluation_id", "case_id", "anonymous_arm_id", "run_index")
    )
    checks = {
        "identity_tuple_bound": tuple_bound,
        "run_completed": run.get("completion_status") == "COMPLETED",
        "schema_valid": bool(run.get("schema_valid")),
        "command_recorded": bool(run.get("command")),
        "input_hashes_bound": bool(
            run.get("input_hashes")
            or (
                run.get("task_input_hash")
                and run.get("package_hash")
                and run.get("fixture_manifest_hash")
            )
        ),
        "output_hash_recorded": bool(run.get("output_sha256") or run.get("result_hashes")),
        "prohibited_action_clear": not observation.get("prohibited_actions_attempted"),
    }
    return {
        "role": "PROCESS_EVIDENCE",
        "checks": checks,
        "passed": all(checks.values()),
        "evidence_level": "E2" if all(checks.values()) else "E1",
    }


def rescore_process(root: Path) -> dict:
    cells = []
    for score_path in sorted((root / "evals/results/phase-002/scores").rglob("*.json")):
        score = read_json(score_path)
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
                **assess_process(observation, run),
            }
        )
    value = {"schema_version": "1.0.0", "cells": cells}
    value["content_hash"] = sha256_json(value)
    return value


def write_process(root: Path, *, check: bool) -> list[str]:
    return check_or_write(
        root / "evals/results/phase-002a/process_evidence/process.json",
        rescore_process(root),
        check=check,
    )
