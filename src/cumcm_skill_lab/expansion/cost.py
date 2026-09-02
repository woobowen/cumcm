"""Truthful observable-cost aggregation for Phase 002D."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .attempt_ledger import load_attempts
from .models import (
    RESULT_ROOT,
    check_or_write,
    hashed_body,
    read_json,
    sha256_json,
    write_json,
)

COST_PATH = RESULT_ROOT / "cost/cost.json"
COST_SCHEMA_PATH = Path("contracts/expansion_cost.schema.json")
COST_REPORT_PATH = Path("reports/phase002d_cost_report.md")
MAINTENANCE_PATHS = (
    "src/cumcm_skill_lab/expansion/runner.py",
    "src/cumcm_skill_lab/expansion/attempt_ledger.py",
    "src/cumcm_skill_lab/expansion/eligibility.py",
    "src/cumcm_skill_lab/expansion/oracle.py",
    "src/cumcm_skill_lab/expansion/scoring.py",
    "src/cumcm_skill_lab/expansion/schedule.py",
    "scripts/run_phase002d_expansion.py",
    "scripts/generate_phase002d_schedule.py",
    "contracts/expansion_attempt.schema.json",
    "contracts/expansion_run.schema.json",
    "contracts/primary_eligibility.schema.json",
    "contracts/expansion_schedule.schema.json",
)
TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_tokens",
)
POST_EXPERIMENT_DERIVED_DIRS = frozenset(
    {
        "automated_decisions",
        "closure",
        "decision_audit",
        "subagent_audits",
        "sufficiency",
    }
)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _tokens(attempts: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [attempt.get(field) for attempt in attempts]
    observed = [value for value in values if isinstance(value, int)]
    complete = bool(attempts) and len(observed) == len(attempts)
    return {
        "status": "OBSERVED" if complete else "UNKNOWN",
        "total": sum(observed) if complete else "UNKNOWN",
        "average_per_record": (round(sum(observed) / len(attempts), 6) if complete else "UNKNOWN"),
        "observed_records": len(observed),
        "total_records": len(attempts),
    }


def _mean(value: float, count: int) -> float | str:
    return round(value / count, 6) if count else "NOT_YET_OBSERVED"


def _attempt_cost(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    duration = sum(attempt["duration_seconds"] for attempt in attempts)
    return {
        "attempt_count": len(attempts),
        "input_tokens": _tokens(attempts, "input_tokens"),
        "cached_input_tokens": _tokens(attempts, "cached_input_tokens"),
        "output_tokens": _tokens(attempts, "output_tokens"),
        "reasoning_tokens": _tokens(attempts, "reasoning_tokens"),
        "duration_seconds": round(duration, 6),
        "average_duration_seconds": _mean(duration, len(attempts)),
    }


def _maintenance_surface(root: Path) -> dict[str, Any]:
    files = [root / path for path in MAINTENANCE_PATHS]
    return {
        "tracked_file_count": len(files),
        "lines_of_code": sum(len(path.read_text(encoding="utf-8").splitlines()) for path in files),
        "paths": list(MAINTENANCE_PATHS),
    }


def _evidence_storage(root: Path) -> dict[str, int]:
    paths = [
        path
        for path in (root / RESULT_ROOT).rglob("*")
        if path.is_file()
        and "cost" not in path.relative_to(root / RESULT_ROOT).parts
        and not POST_EXPERIMENT_DERIVED_DIRS.intersection(
            path.relative_to(root / RESULT_ROOT).parts
        )
    ]
    return {
        "tracked_evidence_file_count": len(paths),
        "tracked_evidence_bytes": sum(path.stat().st_size for path in paths),
    }


def build_cost(root: Path, *, batch_id: int, calculated_at: str | None = None) -> dict[str, Any]:
    attempts = load_attempts(root)
    eligible = [attempt for attempt in attempts if attempt["primary_eligible"]]
    failures = [attempt for attempt in attempts if attempt["completion_status"] != "COMPLETED"]
    oracle_passes = [attempt for attempt in eligible if attempt["oracle_status"] == "PASS"]
    infrastructure = [
        attempt
        for attempt in attempts
        if attempt.get("failure_class")
        in {
            "TLS_HANDSHAKE_TIMEOUT",
            "RESPONSES_CONNECT_RESET",
            "WEBSOCKET_RESET",
            "HTTPS_FALLBACK_DISCONNECT",
            "PROCESS_TIMEOUT",
            "UNKNOWN_TRANSPORT_FAILURE",
        }
    ]
    arms = sorted({attempt["anonymous_arm_id"] for attempt in attempts})
    arm_costs = {
        arm: {
            **_attempt_cost(
                [attempt for attempt in attempts if attempt["anonymous_arm_id"] == arm]
            ),
            "primary_eligible": sum(
                attempt["primary_eligible"]
                for attempt in attempts
                if attempt["anonymous_arm_id"] == arm
            ),
            "oracle_passes": sum(
                attempt["oracle_status"] == "PASS"
                for attempt in attempts
                if attempt["anonymous_arm_id"] == arm
            ),
        }
        for arm in arms
    }
    by_case: dict[str, list[dict[str, Any]]] = {}
    for attempt in eligible:
        by_case.setdefault(attempt["case_id"], []).append(attempt)
    balanced_case_costs = {
        case_id: _attempt_cost(case_attempts)
        for case_id, case_attempts in sorted(by_case.items())
        if {attempt["anonymous_arm_id"] for attempt in case_attempts} == {"ARM-A", "ARM-B", "ARM-C"}
    }
    repeat_complete_cases = [
        case_id
        for case_id, case_attempts in by_case.items()
        if all(
            any(
                attempt["anonymous_arm_id"] == arm and attempt["repeat_id"] == repeat
                for attempt in case_attempts
            )
            for arm in ("ARM-A", "ARM-B", "ARM-C")
            for repeat in (1, 2)
        )
    ]
    body = {
        "schema_version": "1.0.0",
        "cost_id": "PHASE-002D-COST-CURRENT",
        "batch_id": batch_id,
        "calculated_at": calculated_at or _now(),
        "attempts": len(attempts),
        "successful_primary_records": len(eligible),
        "failed_attempts": len(failures),
        "success_rate": round(len(eligible) / len(attempts), 6) if attempts else 0,
        "oracle_passes": len(oracle_passes),
        "oracle_failures": len(eligible) - len(oracle_passes),
        "tokens": {field: _tokens(attempts, field) for field in TOKEN_FIELDS},
        "duration_seconds": round(sum(attempt["duration_seconds"] for attempt in attempts), 6),
        "retries": sum(attempt["retry_of"] is not None for attempt in attempts),
        "infrastructure_failures": len(infrastructure),
        "operator_interventions": sum(attempt["manual_intervention"] for attempt in attempts),
        "queue_delay_seconds": "UNKNOWN",
        "runner_cpu_seconds": "UNKNOWN",
        "replay_cpu_seconds": "NOT_RUN",
        "storage": _evidence_storage(root),
        "maintenance_surface": _maintenance_surface(root),
        "per_successful_primary_record": _attempt_cost(eligible),
        "marginal_balanced_case_costs": balanced_case_costs,
        "independent_repeat_marginal_cost": {
            "status": "OBSERVED" if repeat_complete_cases else "NOT_YET_OBSERVED",
            "cases": sorted(repeat_complete_cases),
        },
        "average_run_cost_by_arm": arm_costs,
        "clean_room_architecture_engineering_cost": "UNKNOWN_NOT_IMPLEMENTED",
        "retain_scaffold_minimum_engineering_cost": "UNKNOWN_NOT_ESTIMATED",
        "monetary_cost": "UNKNOWN",
        "api_key_used": False,
        "api_billing_used": False,
        "correctness_and_hard_gates_dominate_cost": True,
        "unknown_checkpoint_token_totals_not_treated_as_zero": True,
    }
    return hashed_body(body, "cost_hash")


def render_cost_report(cost: dict[str, Any]) -> str:
    tokens = cost["tokens"]
    token_text = lambda field: tokens[field]["total"]  # noqa: E731
    attempt_summary = (
        f"{cost['attempts']} / {cost['successful_primary_records']} / {cost['failed_attempts']}"
    )
    hidden_token_summary = f"{token_text('cached_input_tokens')} / {token_text('reasoning_tokens')}"
    execution_summary = (
        f"{cost['retries']} / {cost['infrastructure_failures']} / {cost['operator_interventions']}"
    )
    time_observability = (
        f"{cost['queue_delay_seconds']} / {cost['runner_cpu_seconds']} / "
        f"{cost['replay_cpu_seconds']}"
    )
    storage_summary = (
        f"{cost['storage']['tracked_evidence_bytes']} bytes in "
        f"{cost['storage']['tracked_evidence_file_count']} files"
    )
    maintenance_summary = (
        f"{cost['maintenance_surface']['lines_of_code']} lines in "
        f"{cost['maintenance_surface']['tracked_file_count']} frozen files"
    )
    arm_lines = "\n".join(
        f"| {arm} | {value['attempt_count']} | {value['primary_eligible']} | "
        f"{value['oracle_passes']} | {value['input_tokens']['total']} | "
        f"{value['output_tokens']['total']} | {value['duration_seconds']} |"
        for arm, value in cost["average_run_cost_by_arm"].items()
    )
    return f"""# Phase 002D cost report

- Batch: `{cost["batch_id"]}`
- Attempts / primary eligible / failed: {attempt_summary}
- Primary-eligibility success rate: {cost["success_rate"]}
- Oracle PASS / FAIL among eligible records: {cost["oracle_passes"]} / {cost["oracle_failures"]}
- Input / output tokens: {token_text("input_tokens")} / {token_text("output_tokens")}
- Cached input / reasoning tokens: {hidden_token_summary}
- Total duration: {cost["duration_seconds"]} seconds
- Retries / infrastructure failures / operator interventions: {execution_summary}
- Queue delay / runner CPU / replay CPU: {time_observability}
- Evidence storage: {storage_summary}
- Maintenance surface: {maintenance_summary}
- Monetary cost: `UNKNOWN`; API key/billing used: false / false

| Arm | Attempts | Eligible | Oracle PASS | Input | Output | Duration seconds |
|---|---:|---:|---:|---:|---:|---:|
{arm_lines}

Cached-input and reasoning-token fields are `UNKNOWN`, not zero: no attempt exposed those values.
The frozen checkpoint's numeric accumulator is therefore not used for those two cost totals.
Cost cannot override correctness or any hard Gate. Clean-room and retain-scaffold engineering costs
remain unknown until separately measured; no currency amount is inferred from ChatGPT-managed use.

Cost hash: `{cost["cost_hash"]}`.
"""


def validate_cost(root: Path, value: dict[str, Any]) -> list[str]:
    schema = read_json(root / COST_SCHEMA_PATH)
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(value)]
    body = dict(value)
    recorded = body.pop("cost_hash", None)
    if sha256_json(body) != recorded:
        errors.append("COST_HASH_MISMATCH")
    return errors


def check_or_write_cost(root: Path, *, batch_id: int | None, check: bool) -> dict[str, Any]:
    existing = read_json(root / COST_PATH) if (root / COST_PATH).is_file() else None
    if existing is None and batch_id is None:
        raise RuntimeError("COST_BATCH_ID_REQUIRED_FOR_INITIAL_WRITE")
    selected_batch = batch_id if batch_id is not None else existing["batch_id"]
    calculated_at = (
        existing["calculated_at"]
        if existing is not None and existing["batch_id"] == selected_batch
        else None
    )
    expected = build_cost(root, batch_id=selected_batch, calculated_at=calculated_at)
    errors = validate_cost(root, expected)
    errors.extend(check_or_write(root / COST_PATH, expected, check=check))
    snapshot_path = root / RESULT_ROOT / f"cost/batches/batch-{selected_batch:03d}.json"
    report = render_cost_report(expected)
    if check:
        if not snapshot_path.is_file() or read_json(snapshot_path) != expected:
            errors.append("COST_BATCH_SNAPSHOT_MISMATCH")
        if (
            not (root / COST_REPORT_PATH).is_file()
            or (root / COST_REPORT_PATH).read_text(encoding="utf-8") != report
        ):
            errors.append("COST_REPORT_STALE")
    else:
        if snapshot_path.is_file() and read_json(snapshot_path) != expected:
            errors.append("COST_BATCH_SNAPSHOT_IMMUTABLE")
        elif not snapshot_path.is_file():
            write_json(snapshot_path, expected)
        (root / COST_REPORT_PATH).write_text(report, encoding="utf-8")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "batch_id": selected_batch,
        "attempts": expected["attempts"],
        "successful_primary_records": expected["successful_primary_records"],
        "oracle_passes": expected["oracle_passes"],
        "cost_hash": expected["cost_hash"],
    }
