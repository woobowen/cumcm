"""Hash-bound, append-only recovery for pre-score harness false positives."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from .anonymization import assert_identity_free
from .models import file_sha256, load_json, validate_json, write_json
from .runner import (
    PRIVATE_PATH,
    SECRET_TEXT,
    _artifact_reference_errors,
    _meaningful_entries,
)

FORBIDDEN_ERRORS = (
    "PRIVATE_PATH_IN_OBSERVATION",
    "SECRET_IN_OBSERVATION",
    "FROZEN_INPUT_MUTATION",
    "FORBIDDEN_NETWORK_COMMAND",
    "FORBIDDEN_MCP_EVENT",
)


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _latest_runs(root: Path) -> dict[tuple[str, str], Path]:
    latest: dict[tuple[str, str], Path] = {}
    for path in sorted((root / "evals/results/phase-002/runs").rglob("*.json")):
        run = load_json(path)
        key = (run["anonymous_arm_id"], run["case_id"])
        current = latest.get(key)
        if current is None or run["run_index"] > load_json(current)["run_index"]:
            latest[key] = path
    return latest


def _recovery_reasons(run: dict) -> list[str]:
    error = run.get("error_summary") or ""
    reasons: list[str] = []
    if "NONEXISTENT_ARTIFACT_REFERENCE:code_artifacts:" in error:
        reasons.append("ARTIFACT_DESCRIPTION_FALSE_POSITIVE")
    if "PROHIBITED_ACTION_REPORTED" in error:
        reasons.append("NEGATED_PROHIBITED_ACTION_FALSE_POSITIVE")
    return reasons


def _paths(root: Path, run: dict) -> tuple[Path, Path, Path]:
    relative = Path(run["anonymous_arm_id"]) / run["case_id"] / f"run-{run['run_index']:03d}.json"
    raw = root / ".cache/upstream-eval/raw-outputs" / run["evaluation_id"] / relative
    observation = root / "evals/results/phase-002/observations" / relative
    recovery = (
        root
        / "evals/results/phase-002/recoveries"
        / run["anonymous_arm_id"]
        / run["case_id"]
        / f"run-{run['run_index']:03d}.recovery.json"
    )
    return raw, observation, recovery


def recover_observations(
    root: Path,
    *,
    check: bool = False,
    recovered_at: str | None = None,
) -> dict:
    candidate_ids = [
        item["candidate_id"]
        for item in load_json(
            root / "research/upstream_candidates/dynamic_reviews/package_safety_review.json"
        )["arms"]
        if item["candidate_id"]
    ]
    implementation_commit = _git_commit(root)
    errors: list[str] = []
    recovered: list[str] = []
    for _, run_path in sorted(_latest_runs(root).items()):
        run = load_json(run_path)
        raw_path, observation_path, recovery_path = _paths(root, run)
        if run["completion_status"] == "COMPLETED":
            continue
        reasons = _recovery_reasons(run)
        error_summary = run.get("error_summary") or ""
        if (
            run["completion_status"] != "FAILED"
            or run["exit_code"] != 0
            or not reasons
            or any(item in error_summary for item in FORBIDDEN_ERRORS)
        ):
            errors.append(f"RECOVERY_INELIGIBLE:{run_path.relative_to(root)}")
            continue
        if not raw_path.is_file():
            if not check:
                errors.append(f"RECOVERY_RAW_OUTPUT_MISSING:{raw_path.relative_to(root)}")
                continue
            if not recovery_path.is_file() or not observation_path.is_file():
                errors.append(f"RECOVERY_EVIDENCE_MISSING:{run_path.relative_to(root)}")
                continue
            observation = load_json(observation_path)
            raw_hash = load_json(recovery_path)["raw_output_hash"]
        else:
            try:
                observation = json.loads(raw_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"RECOVERY_RAW_JSON_INVALID:{run_path.relative_to(root)}:{exc}")
                continue
            raw_hash = file_sha256(raw_path)
        observation_errors = validate_json(
            observation, root / "contracts/eval_observation.schema.json"
        )
        assert_identity_free(observation, candidate_ids)
        serialized = json.dumps(observation, ensure_ascii=False, sort_keys=True)
        workspace = (
            root
            / ".cache/upstream-eval/workspaces"
            / run["evaluation_id"]
            / run["anonymous_arm_id"]
            / run["case_id"]
            / f"run-{run['run_index']:03d}"
        )
        semantic_errors = _artifact_reference_errors(observation, workspace)
        if _meaningful_entries(observation.get("prohibited_actions_attempted", [])):
            semantic_errors.append("PROHIBITED_ACTION_REPORTED")
        if PRIVATE_PATH.search(serialized):
            semantic_errors.append("PRIVATE_PATH_IN_OBSERVATION")
        if SECRET_TEXT.search(serialized):
            semantic_errors.append("SECRET_IN_OBSERVATION")
        if observation_errors or semantic_errors:
            errors.append(
                f"RECOVERY_OBSERVATION_INVALID:{run_path.relative_to(root)}:"
                f"{observation_errors + semantic_errors}"
            )
            continue
        if not check:
            if observation_path.exists() or recovery_path.exists():
                errors.append(f"RECOVERY_WOULD_OVERWRITE:{run_path.relative_to(root)}")
                continue
            write_json(observation_path, observation)
        if not observation_path.is_file():
            errors.append(f"RECOVERY_OBSERVATION_MISSING:{observation_path.relative_to(root)}")
            continue
        record = {
            "schema_version": "1.0.0",
            "recovery_id": (
                f"RECOVERY-{run['anonymous_arm_id']}-{run['case_id']}-RUN-{run['run_index']:03d}"
            ),
            "evaluation_id": run["evaluation_id"],
            "case_id": run["case_id"],
            "anonymous_arm_id": run["anonymous_arm_id"],
            "run_index": run["run_index"],
            "source_run_path": run_path.relative_to(root).as_posix(),
            "source_run_hash": file_sha256(run_path),
            "raw_output_hash": raw_hash,
            "observation_path": observation_path.relative_to(root).as_posix(),
            "observation_hash": file_sha256(observation_path),
            "original_completion_status": run["completion_status"],
            "original_schema_valid": run["schema_valid"],
            "recovery_status": "RECOVERED_FOR_SCORING",
            "recovery_reasons": reasons,
            "recovery_implementation_commit": implementation_commit,
            "recovered_at": recovered_at or _now(),
            "original_run_preserved": True,
            "affected_by_run_failure": True,
            "identity_revealed": False,
        }
        if check:
            if not recovery_path.is_file():
                errors.append(f"RECOVERY_RECORD_MISSING:{recovery_path.relative_to(root)}")
                continue
            current = load_json(recovery_path)
            for key in record:
                if key in {"recovery_implementation_commit", "recovered_at"}:
                    continue
                if current.get(key) != record[key]:
                    errors.append(
                        f"RECOVERY_RECORD_MISMATCH:{recovery_path.relative_to(root)}:{key}"
                    )
            errors.extend(
                f"RECOVERY_SCHEMA_INVALID:{recovery_path.relative_to(root)}:{item}"
                for item in validate_json(current, root / "contracts/eval_recovery.schema.json")
            )
        else:
            write_json(recovery_path, record)
        recovered.append(record["recovery_id"])
    return {"status": "PASS" if not errors else "FAIL", "recovered": recovered, "errors": errors}
