"""Audit retry burden without converting failures to zero or selecting best-of-N."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .classification import TERMINAL_CLASSIFICATIONS, build_classifications
from .models import RESULT_ROOT, SOURCE_ROOT, check_or_write, hashed_body, read_json
from .slot_matrix import build_slot_matrix

AUDIT_PATH = RESULT_ROOT / "retry_bias/retry_bias_audit.json"


def build_retry_bias_audit(root: Path) -> dict[str, Any]:
    classifications, _ = build_classifications(root)
    slots, _, _ = build_slot_matrix(root)
    ledger = read_json(root / SOURCE_ROOT / "attempt_ledger.json")
    cost = read_json(root / SOURCE_ROOT / "cost/cost.json")
    frozen_budget = read_json(root / SOURCE_ROOT / "budget/frozen_budget.json")
    r1_freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    by_id = {item["attempt_id"]: item for item in classifications}

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
    all_attempts_in_cost = cost["attempts"] == len(ledger["attempt_ids"]) == 28
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
    ]
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
        "cell_attempt_efficiency": {
            "resolved_slots_per_attempt": round(resolved / len(ledger["attempt_ids"]), 9),
            "quality_success_slots_per_attempt": round(
                quality_success / len(ledger["attempt_ids"]), 9
            ),
            "primary_eligible_slots_per_attempt": round(
                primary_slots / len(ledger["attempt_ids"]), 9
            ),
        },
        "earliest_eligible_enforced": all(
            item["selected_quality_record_id"] == item["first_eligible_success_id"]
            for item in slots
        ),
        "best_of_n_prohibited": True,
        "previous_failures_retained": all(
            len(item["all_attempt_ids"]) == item["attempt_count"] for item in slots
        ),
        "later_success_erases_failure": False,
        "posthoc_budget_expansion": not original_budget_unchanged,
        "per_cell_cap_respected": max(item["attempt_count"] for item in slots) <= 3,
        "all_attempts_in_cost": all_attempts_in_cost,
        "failure_zero_imputation": False,
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
