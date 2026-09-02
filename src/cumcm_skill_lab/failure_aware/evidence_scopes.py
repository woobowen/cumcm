"""Separate quality, reliability, outcome-completeness, and component-gap evidence."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .classification import build_classifications
from .models import RESULT_ROOT, SOURCE_ROOT, check_or_write, hashed_body, read_json
from .slot_matrix import build_slot_matrix

SUMMARY_PATH = RESULT_ROOT / "evidence_scopes/evidence_scope_summary.json"


def _round_rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 9) if denominator else 0.0


def build_evidence_scope_summary(root: Path) -> dict[str, Any]:
    classifications, _ = build_classifications(root)
    slots, _, _ = build_slot_matrix(root)
    ledger = read_json(root / SOURCE_ROOT / "attempt_ledger.json")
    attempts = [
        read_json(root / SOURCE_ROOT / f"attempts/{attempt_id}.json")
        for attempt_id in ledger["attempt_ids"]
    ]

    quality_slots = [item for item in slots if item["quality_eligible"]]
    quality_by_case_arm: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    for slot in quality_slots:
        quality_by_case_arm[slot["case_id"]][slot["anonymous_arm_id"]].add(slot["repeat_id"])
    balanced_cases = sorted(
        case_id
        for case_id, arms in quality_by_case_arm.items()
        if set(arms) == {"ARM-A", "ARM-B", "ARM-C"}
    )
    quality_depth = min(
        (
            min(len(quality_by_case_arm[case_id][arm]) for arm in ("ARM-A", "ARM-B", "ARM-C"))
            for case_id in balanced_cases
        ),
        default=0,
    )

    resolved_names = {"RESOLVED_ELIGIBLE_SUCCESS", "RESOLVED_TERMINAL_NEGATIVE"}
    resolved_slots = [item for item in slots if item["outcome_resolution"] in resolved_names]
    resolved_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for slot in resolved_slots:
        resolved_by_case[slot["case_id"]].append(slot)
    resolved_cases = sorted(
        case_id for case_id, items in resolved_by_case.items() if len(items) == 6
    )
    outcome_depth = min(
        (
            min(
                len(
                    {
                        item["repeat_id"]
                        for item in resolved_by_case[case_id]
                        if item["anonymous_arm_id"] == arm
                    }
                )
                for arm in ("ARM-A", "ARM-B", "ARM-C")
            )
            for case_id in resolved_cases
        ),
        default=0,
    )

    by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in classifications:
        by_kind[item["primary_classification"]].append(item)
    oracle_gap = by_kind["VALID_OUTPUT_ORACLE_FAIL"]
    policy_gap = by_kind["TERMINAL_POLICY_FAILURE"]
    component_groups = []
    for gap_id, values in (
        ("REPEATED_ORACLE_CORRECTNESS_GAP", oracle_gap),
        ("REPEATED_POLICY_COMPLIANCE_GAP", policy_gap),
    ):
        case_ids = sorted({item["case_id"] for item in values})
        repeat_ids = sorted({item["repeat_id"] for item in values})
        if len(values) >= 2 and (len(case_ids) >= 2 or len(repeat_ids) >= 2):
            component_groups.append(
                {
                    "gap_id": gap_id,
                    "attempt_ids": [item["attempt_id"] for item in values],
                    "case_ids": case_ids,
                    "repeat_ids": repeat_ids,
                }
            )

    terminal_attempt_count = sum(
        len(by_kind[name])
        for name in (
            "VALID_OUTPUT_ORACLE_FAIL",
            "TERMINAL_POLICY_FAILURE",
            "TERMINAL_MODEL_SCHEMA_FAILURE",
            "TERMINAL_UNSUPPORTED_CLAIM_FAILURE",
        )
    )
    body = {
        "schema_version": "1.0.0",
        "scope_summary_id": "PHASE-002D-R1-EVIDENCE-SCOPES-001",
        "quality_evidence": {
            "selected_record_ids": [item["selected_quality_record_id"] for item in quality_slots],
            "balanced_cases": balanced_cases,
            "balanced_case_count": len(balanced_cases),
            "minimum_repeat_depth": quality_depth,
            "required_balanced_cases": 4,
            "required_repeat_depth": 2,
            "result": (
                "SUFFICIENT"
                if len(balanced_cases) >= 4 and quality_depth >= 2
                else "EVIDENCE_INSUFFICIENT"
            ),
        },
        "reliability_evidence": {
            "attempt_ids": ledger["attempt_ids"],
            "attempt_count": len(attempts),
            "slot_count": len(slots),
            "completion_rate": _round_rate(
                sum(item["completion_status"] == "COMPLETED" for item in attempts), len(attempts)
            ),
            "primary_eligible_rate": _round_rate(
                sum(item["primary_eligible"] for item in attempts), len(attempts)
            ),
            "terminal_failure_rate": _round_rate(terminal_attempt_count, len(attempts)),
            "policy_violation_rate": _round_rate(
                sum(item["failure_class"] == "POLICY_VIOLATION" for item in attempts),
                len(attempts),
            ),
            "infrastructure_rate": _round_rate(
                len(by_kind["INFRASTRUCTURE_CENSORED"]), len(attempts)
            ),
            "retry_burden": sum(item["retry_count"] for item in slots),
        },
        "outcome_completeness": {
            "resolved_slot_ids": [item["slot_id"] for item in resolved_slots],
            "resolved_slot_count": len(resolved_slots),
            "resolved_success_slots": sum(
                item["outcome_resolution"] == "RESOLVED_ELIGIBLE_SUCCESS" for item in slots
            ),
            "resolved_terminal_negative_slots": sum(
                item["outcome_resolution"] == "RESOLVED_TERMINAL_NEGATIVE" for item in slots
            ),
            "censored_slot_ids": [item["slot_id"] for item in slots if item["censored"]],
            "resolved_case_count": len(resolved_cases),
            "minimum_repeat_depth": outcome_depth,
        },
        "component_gap_evidence": {
            "eligible_gap_groups": component_groups,
            "excluded_isolated_failures": [
                item["attempt_id"]
                for item in classifications
                if item["primary_classification"] in {"HARNESS_CENSORED", "UNKNOWN_CENSORED"}
            ],
            "infrastructure_excluded": True,
            "recovery_excluded": True,
            "agent_votes_excluded": True,
        },
        "repeat_semantics": {
            "repeat_depth_deprecated": True,
            "quality_balanced_case_count": len(balanced_cases),
            "quality_minimum_repeat_depth": quality_depth,
            "outcome_resolved_case_count": len(resolved_cases),
            "outcome_minimum_repeat_depth": outcome_depth,
            "schedule_attempted_repeat_depth": 2,
            "reliability_observed_repeat_depth": 2,
        },
        "failure_is_not_zero_score": True,
    }
    return hashed_body(body, "summary_hash")


def check_or_write_evidence_scopes(root: Path, *, check: bool) -> dict[str, Any]:
    summary = build_evidence_scope_summary(root)
    validator = Draft202012Validator(
        read_json(root / "contracts/evidence_scope_summary.schema.json")
    )
    errors = [f"EVIDENCE_SCOPE_SCHEMA:{item.message}" for item in validator.iter_errors(summary)]
    errors.extend(check_or_write(root / SUMMARY_PATH, summary, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "quality": summary["quality_evidence"],
        "reliability": summary["reliability_evidence"],
        "outcome": summary["outcome_completeness"],
        "summary_hash": summary["summary_hash"],
    }
