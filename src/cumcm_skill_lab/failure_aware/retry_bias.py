"""Audit retry burden without converting failures to zero or selecting best-of-N."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .classification import TERMINAL_CLASSIFICATIONS, build_classifications
from .models import RESULT_ROOT, SOURCE_ROOT, check_or_write, hashed_body, read_json
from .slot_matrix import build_slot_matrix

AUDIT_PATH = RESULT_ROOT / "retry_bias/retry_bias_audit.json"


def _cost_reconciliation(attempts: list[dict[str, Any]], cost: dict[str, Any]) -> dict[str, Any]:
    primary_eligible = [item for item in attempts if item["primary_eligible"]]
    recomputed = {
        "attempts": len(attempts),
        "duration_seconds": round(sum(item["duration_seconds"] for item in attempts), 6),
        "input_tokens": sum(item["input_tokens"] or 0 for item in attempts),
        "output_tokens": sum(item["output_tokens"] or 0 for item in attempts),
        "retries": sum(item["retry_of"] is not None for item in attempts),
        "failed_attempts": sum(item["completion_status"] != "COMPLETED" for item in attempts),
        "infrastructure_failures": sum(
            item["failure_class"] in {"HTTPS_FALLBACK_DISCONNECT"} for item in attempts
        ),
        "oracle_passes": sum(item["oracle_status"] == "PASS" for item in primary_eligible),
        "oracle_failures": sum(item["oracle_status"] == "FAIL" for item in primary_eligible),
        "successful_primary_records": len(primary_eligible),
    }
    recorded = {
        "attempts": cost["attempts"],
        "duration_seconds": cost["duration_seconds"],
        "input_tokens": cost["tokens"]["input_tokens"]["total"],
        "output_tokens": cost["tokens"]["output_tokens"]["total"],
        "retries": cost["retries"],
        "failed_attempts": cost["failed_attempts"],
        "infrastructure_failures": cost["infrastructure_failures"],
        "oracle_passes": cost["oracle_passes"],
        "oracle_failures": cost["oracle_failures"],
        "successful_primary_records": cost["successful_primary_records"],
    }
    exact_match = recomputed == recorded
    return {
        "recomputed": recomputed,
        "recorded": recorded,
        "exact_match": exact_match,
        "unknown_costs_preserved": (
            cost["monetary_cost"] == "UNKNOWN"
            and cost["tokens"]["cached_input_tokens"]["status"] == "UNKNOWN"
            and cost["tokens"]["reasoning_tokens"]["status"] == "UNKNOWN"
        ),
    }


def build_retry_bias_audit(root: Path) -> dict[str, Any]:
    classifications, _ = build_classifications(root)
    slots, _, _ = build_slot_matrix(root)
    ledger = read_json(root / SOURCE_ROOT / "attempt_ledger.json")
    cost = read_json(root / SOURCE_ROOT / "cost/cost.json")
    frozen_budget = read_json(root / SOURCE_ROOT / "budget/frozen_budget.json")
    schedule = read_json(root / SOURCE_ROOT / "schedule/schedule.json")
    command_ledger = read_json(root / SOURCE_ROOT / "closure/command_ledger.json")
    r1_freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    by_id = {item["attempt_id"]: item for item in classifications}
    attempts = [
        read_json(root / SOURCE_ROOT / f"attempts/{attempt_id}.json")
        for attempt_id in ledger["attempt_ids"]
    ]

    attempts_to_first: list[dict[str, Any]] = []
    success_after_retry: list[str] = []
    primary_after_retry: list[str] = []
    terminal_before_success: list[str] = []
    for slot in slots:
        first_primary = next(
            (
                (index, attempt_id)
                for index, attempt_id in enumerate(slot["all_attempt_ids"], start=1)
                if by_id[attempt_id]["observed"]["primary_eligible"]
            ),
            None,
        )
        if first_primary:
            attempts_to_first.append(
                {
                    "slot_id": slot["slot_id"],
                    "attempt_number": first_primary[0],
                    "attempt_id": first_primary[1],
                }
            )
            if first_primary[0] > 1:
                primary_after_retry.append(slot["slot_id"])
        success_index = next(
            (
                index
                for index, attempt_id in enumerate(slot["all_attempt_ids"], start=1)
                if by_id[attempt_id]["primary_classification"] == "ELIGIBLE_SUCCESS"
            ),
            None,
        )
        if success_index and success_index > 1:
            success_after_retry.append(slot["slot_id"])
            earlier = slot["all_attempt_ids"][: success_index - 1]
            if any(
                by_id[item]["primary_classification"] in TERMINAL_CLASSIFICATIONS
                for item in earlier
            ):
                terminal_before_success.append(slot["slot_id"])

    retry_queue_order = {
        item["attempt_id"]: index for index, item in enumerate(schedule["retry_queue"], start=1)
    }
    retry_queue_positions = []
    retry_after_terminal: list[str] = []
    for ledger_position, attempt in enumerate(attempts, start=1):
        if attempt["retry_of"] is None:
            continue
        predecessor_classification = by_id[attempt["retry_of"]]["primary_classification"]
        allowed = predecessor_classification not in TERMINAL_CLASSIFICATIONS
        retry_queue_positions.append(
            {
                "attempt_id": attempt["attempt_id"],
                "ledger_position": ledger_position,
                "queue_position": retry_queue_order[attempt["attempt_id"]],
                "retry_of": attempt["retry_of"],
                "predecessor_classification": predecessor_classification,
                "allowed_after_predecessor": allowed,
            }
        )
        if not allowed:
            retry_after_terminal.append(attempt["attempt_id"])

    queue_positions = [item["queue_position"] for item in retry_queue_positions]
    retry_queue_monotonic = queue_positions == sorted(queue_positions)
    cost_reconciliation = _cost_reconciliation(attempts, cost)
    scored_commands = [
        item for item in command_ledger["entries"] if item["execution_type"] == "REAL_CODEX_SCORED"
    ]
    elapsed_before_last_start = round(
        sum(item["duration_seconds"] for item in scored_commands[:-1]), 6
    )
    elapsed_after_last_finish = round(sum(item["duration_seconds"] for item in scored_commands), 6)
    elapsed_cap = frozen_budget["maximum_total_elapsed_seconds"]
    elapsed_budget_boundary = {
        "semantics": "START_ADMISSION_CHECK_THEN_STOP_AFTER_COMPLETION",
        "elapsed_before_last_start": elapsed_before_last_start,
        "elapsed_after_last_finish": elapsed_after_last_finish,
        "maximum_total_elapsed_seconds": elapsed_cap,
        "last_start_admitted_below_cap": elapsed_before_last_start < elapsed_cap,
        "stopped_after_cap_reached": elapsed_after_last_finish >= elapsed_cap,
    }

    resolved = sum(not item["censored"] for item in slots)
    quality_success = sum(item["quality_eligible"] for item in slots)
    primary_slots = sum(
        any(
            by_id[attempt_id]["observed"]["primary_eligible"]
            for attempt_id in slot["all_attempt_ids"]
        )
        for slot in slots
    )
    original_budget_unchanged = r1_freeze["budget_hash"] == frozen_budget["budget_hash"]
    all_attempts_in_cost = cost_reconciliation["exact_match"]
    findings = [
        {
            "finding_id": "RETRY-BIAS-001",
            "severity": "WARNING",
            "evidence_ids": primary_after_retry or ["NONE"],
            "statement": (
                "Primary eligibility occurred after retry in one slot; prior failures remain "
                "in reliability and cost."
            ),
        },
        {
            "finding_id": "RETRY-BIAS-002",
            "severity": "INFO",
            "evidence_ids": [item["slot_id"] for item in slots if item["retry_count"]],
            "statement": (
                "No oracle-PASS quality success occurred after retry and no best-of-N quality "
                "selection was used."
            ),
        },
        {
            "finding_id": "RETRY-BIAS-003",
            "severity": "ERROR",
            "evidence_ids": retry_after_terminal,
            "statement": (
                "Two historical retries followed terminal predecessors; the deviations remain "
                "counted but cannot authorize later success or future supplemental execution."
            ),
        },
        {
            "finding_id": "RETRY-BIAS-004",
            "severity": "WARNING",
            "evidence_ids": [item["attempt_id"] for item in retry_queue_positions],
            "statement": (
                "Historical retry execution order was not monotonic in the frozen retry queue."
            ),
        },
    ]
    earliest_eligible_enforced = all(
        item["selected_quality_record_id"] in (None, item["first_eligible_success_id"])
        for item in slots
    )
    previous_failures_retained = sorted(
        attempt_id for item in slots for attempt_id in item["all_attempt_ids"]
    ) == sorted(ledger["attempt_ids"])
    failure_zero_imputation = any(
        item["selected_quality_record_id"] is not None
        and by_id[item["selected_quality_record_id"]]["primary_classification"]
        != "ELIGIBLE_SUCCESS"
        for item in slots
    )
    later_success_erases_failure = any(
        item["slot_id"] in terminal_before_success and item["quality_eligible"] for item in slots
    )
    body = {
        "schema_version": "1.0.0",
        "audit_id": "PHASE-002D-R1-RETRY-BIAS-AUDIT-001",
        "attempt_count": len(ledger["attempt_ids"]),
        "slot_count": len(slots),
        "retry_burden": sum(item["retry_count"] for item in slots),
        "slots_with_retry": [item["slot_id"] for item in slots if item["retry_count"]],
        "attempt_to_first_eligible": attempts_to_first,
        "terminal_failure_before_success": terminal_before_success,
        "success_after_retry": success_after_retry,
        "primary_eligible_after_retry": primary_after_retry,
        "retry_queue_positions": retry_queue_positions,
        "retry_queue_monotonic": retry_queue_monotonic,
        "retry_after_terminal": retry_after_terminal,
        "historical_protocol_deviations": [
            "RETRY_QUEUE_EXECUTION_ORDER_NON_MONOTONIC",
            "RETRY_STARTED_AFTER_TERMINAL_PREDECESSOR",
        ],
        "cell_attempt_efficiency": {
            "resolved_slots_per_attempt": round(resolved / len(ledger["attempt_ids"]), 9),
            "quality_success_slots_per_attempt": round(
                quality_success / len(ledger["attempt_ids"]), 9
            ),
            "primary_eligible_slots_per_attempt": round(
                primary_slots / len(ledger["attempt_ids"]), 9
            ),
        },
        "earliest_eligible_enforced": earliest_eligible_enforced,
        "best_of_n_prohibited": earliest_eligible_enforced,
        "previous_failures_retained": previous_failures_retained,
        "later_success_erases_failure": later_success_erases_failure,
        "posthoc_budget_expansion": not original_budget_unchanged,
        "per_cell_cap_respected": max(item["attempt_count"] for item in slots) <= 3,
        "all_attempts_in_cost": all_attempts_in_cost,
        "failure_zero_imputation": failure_zero_imputation,
        "cost_reconciliation": cost_reconciliation,
        "elapsed_budget_boundary": elapsed_budget_boundary,
        "findings": findings,
    }
    return hashed_body(body, "audit_hash")


def check_or_write_retry_bias(root: Path, *, check: bool) -> dict[str, Any]:
    audit = build_retry_bias_audit(root)
    validator = Draft202012Validator(read_json(root / "contracts/retry_bias_audit.schema.json"))
    errors = [f"RETRY_BIAS_SCHEMA:{item.message}" for item in validator.iter_errors(audit)]
    errors.extend(check_or_write(root / AUDIT_PATH, audit, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "retry_burden": audit["retry_burden"],
        "slots_with_retry": audit["slots_with_retry"],
        "success_after_retry": audit["success_after_retry"],
        "audit_hash": audit["audit_hash"],
    }
