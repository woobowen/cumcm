"""Deterministic Phase 002D pre-adjudication evidence sufficiency."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .attempt_ledger import load_attempts
from .input_freeze import verify_input_freeze
from .models import RESULT_ROOT, check_or_write, read_json, sha256_json
from .runner import check_runner

SUFFICIENCY_PATH = RESULT_ROOT / "sufficiency/evidence_sufficiency.json"
SUFFICIENCY_SCHEMA_PATH = Path("contracts/evidence_sufficiency.schema.json")
SUFFICIENCY_REPORT_PATH = Path("reports/phase002d_evidence_sufficiency.md")
BALANCED_CASE_MINIMUM = 4
MINIMUM_REPEATS = 2


def _evidence_projection(attempt: dict[str, Any]) -> dict[str, Any]:
    return {
        "attempt_id": attempt["attempt_id"],
        "attempt_hash": attempt["attempt_hash"],
        "case_id": attempt["case_id"],
        "anonymous_arm_id": attempt["anonymous_arm_id"],
        "repeat_id": attempt["repeat_id"],
        "retry_of": attempt["retry_of"],
        "completion_status": attempt["completion_status"],
        "primary_eligible": attempt["primary_eligible"],
        "cohort_id": attempt["cohort_id"],
        "cohort_hash": attempt["cohort_hash"],
        "model": attempt["model"],
        "reasoning_setting": attempt["reasoning_setting"],
        "task_input_hash": attempt["task_input_hash"],
        "policy_hash": attempt["policy_hash"],
        "hard_failures": attempt["hard_failures"],
        "resume_used": attempt["resume_used"],
        "parser_recovery_used": attempt["parser_recovery_used"],
    }


def build_sufficiency(root: Path) -> dict[str, Any]:
    attempts = load_attempts(root)
    freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    cohort = read_json(root / RESULT_ROOT / "cohort/cohort.json")
    schedule = read_json(root / RESULT_ROOT / "schedule/schedule.json")
    required_arms = list(schedule["anonymous_arms"])
    selected_cohort_id = cohort["cohort_id"]
    selected_cohort_hash = cohort["cohort_hash"]

    eligible = [
        attempt
        for attempt in attempts
        if attempt["primary_eligible"] is True
        and attempt["cohort_id"] == selected_cohort_id
        and attempt["cohort_hash"] == selected_cohort_hash
    ]
    repeats: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    case_hashes: dict[str, set[str]] = defaultdict(set)
    arm_hashes: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for attempt in eligible:
        case_id = attempt["case_id"]
        arm = attempt["anonymous_arm_id"]
        repeats[case_id][arm].add(attempt["repeat_id"])
        case_hashes[case_id].add(attempt["task_input_hash"])
        arm_hashes[case_id][arm].add(attempt["task_input_hash"])

    mismatched_cases = sorted(case for case, hashes in case_hashes.items() if len(hashes) != 1)
    balanced_cases = sorted(
        case_id
        for case_id in schedule["cases"]
        if all(repeats[case_id].get(arm) for arm in required_arms)
        and len(case_hashes.get(case_id, set())) == 1
    )
    independent_repeats = min(
        (len(repeats[case_id][arm]) for case_id in balanced_cases for arm in required_arms),
        default=0,
    )
    policy_hashes = {attempt["policy_hash"] for attempt in attempts}
    eligible_gate_failures = [
        attempt["attempt_id"]
        for attempt in eligible
        if attempt["hard_failures"] or attempt["resume_used"] or attempt["parser_recovery_used"]
    ]
    runner = check_runner(root)
    frozen_evidence_valid = not verify_input_freeze(root) and runner["check_status"] == "PASS"
    mandatory_hard_gates_passed = (
        not mismatched_cases
        and not eligible_gate_failures
        and len(policy_hashes) == 1
        and all(attempt["cohort_id"] == selected_cohort_id for attempt in attempts)
        and all(attempt["cohort_hash"] == selected_cohort_hash for attempt in attempts)
        and all(attempt["model"] == cohort["model"] for attempt in attempts)
        and all(attempt["reasoning_setting"] == cohort["reasoning_setting"] for attempt in attempts)
    )
    conditions = {
        "balanced_case_minimum_met": len(balanced_cases) >= BALANCED_CASE_MINIMUM,
        "minimum_repeats_met": independent_repeats >= MINIMUM_REPEATS,
        "frozen_evidence_valid": frozen_evidence_valid,
        "mandatory_hard_gates_passed": mandatory_hard_gates_passed,
    }
    reason_codes: list[str] = []
    if not frozen_evidence_valid:
        result = "STALE"
        reason_codes.append("FROZEN_EVIDENCE_INVALID")
    else:
        if not conditions["balanced_case_minimum_met"]:
            reason_codes.append("BALANCED_CASE_MINIMUM_NOT_MET")
        if not conditions["minimum_repeats_met"]:
            reason_codes.append("MINIMUM_REPEATS_NOT_MET")
        if not mandatory_hard_gates_passed:
            reason_codes.append("MANDATORY_HARD_GATE_FAILED")
        result = "SUFFICIENT" if all(conditions.values()) else "INSUFFICIENT"
    if not reason_codes:
        reason_codes.append("FROZEN_EVIDENCE_MINIMA_MET")

    policy_hash = next(iter(policy_hashes)) if len(policy_hashes) == 1 else "0" * 64
    evidence_items = [_evidence_projection(attempt) for attempt in attempts]
    body = {
        "sufficiency_id": "EVIDENCE-SUFFICIENCY-PHASE-002D",
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["freeze_hash"],
        "policy_id": "POLICY-PHASE-002D",
        "policy_hash": policy_hash,
        "thresholds": {
            "balanced_case_minimum": BALANCED_CASE_MINIMUM,
            "minimum_repeats": MINIMUM_REPEATS,
        },
        "actual": {
            "eligible_primary_count": len(eligible),
            "balanced_cases": balanced_cases,
            "balanced_case_count": len(balanced_cases),
            "independent_repeats": independent_repeats,
            "cell_repeat_counts": {
                case_id: {arm: len(repeats[case_id].get(arm, set())) for arm in required_arms}
                for case_id in schedule["cases"]
            },
            "recovery_excluded_count": sum(
                attempt["resume_used"] or attempt["parser_recovery_used"] for attempt in attempts
            ),
            "failed_excluded_count": sum(
                attempt["completion_status"] == "FAILED" for attempt in attempts
            ),
            "superseded_excluded_count": 0,
            "not_run_excluded_count": sum(
                attempt["completion_status"] == "NOT_RUN" for attempt in attempts
            ),
        },
        "required_arms": required_arms,
        "task_hash_consistency": {
            "passed": not mismatched_cases,
            "mismatched_cases": mismatched_cases,
            "case_hashes": {
                case_id: sorted(hashes) for case_id, hashes in sorted(case_hashes.items())
            },
            "arm_hashes": {
                case_id: {arm: sorted(hashes) for arm, hashes in sorted(values.items())}
                for case_id, values in sorted(arm_hashes.items())
            },
        },
        "conditions": conditions,
        "result": result,
        "reason_codes": reason_codes,
        "semantic_judges_required": result == "SUFFICIENT",
        "ranking_allowed": result == "SUFFICIENT",
        "evidence_items_hash": sha256_json(evidence_items),
    }
    body["record_hash"] = sha256_json(body)
    return body


def validate_sufficiency(root: Path, value: dict[str, Any]) -> list[str]:
    schema = read_json(root / SUFFICIENCY_SCHEMA_PATH)
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(value)]
    body = dict(value)
    recorded = body.pop("record_hash", None)
    if sha256_json(body) != recorded:
        errors.append("SUFFICIENCY_RECORD_HASH_MISMATCH")
    if value["actual"]["balanced_case_count"] != len(value["actual"]["balanced_cases"]):
        errors.append("BALANCED_CASE_COUNT_MISMATCH")
    if value["result"] != "SUFFICIENT" and (
        value["semantic_judges_required"] or value["ranking_allowed"]
    ):
        errors.append("INSUFFICIENT_EVIDENCE_UNLOCKED_SEMANTIC_OR_RANKING")
    return errors


def render_sufficiency_report(value: dict[str, Any]) -> str:
    actual = value["actual"]
    thresholds = value["thresholds"]
    eligible_summary = (
        f"{actual['eligible_primary_count']} (target implied by frozen 4 × 3 × 2 cells: 24)"
    )
    balanced_summary = (
        f"{actual['balanced_case_count']} / {thresholds['balanced_case_minimum']} — "
        f"{', '.join(actual['balanced_cases'])}"
    )
    repeat_summary = f"{actual['independent_repeats']} / {thresholds['minimum_repeats']}"
    exclusion_summary = (
        f"{actual['failed_excluded_count']} / {actual['recovery_excluded_count']} / "
        f"{actual['superseded_excluded_count']} / {actual['not_run_excluded_count']}"
    )
    return f"""# Phase 002D evidence sufficiency

- Result: `{value["result"]}`
- Eligible records: {eligible_summary}
- Balanced cases: {balanced_summary}
- Independent repeats among balanced cells: {repeat_summary}
- Failed / recovery / superseded / NOT_RUN exclusions: {exclusion_summary}
- Task-input hash consistency: {value["task_hash_consistency"]["passed"]}
- Frozen evidence valid: {value["conditions"]["frozen_evidence_valid"]}
- Mandatory hard Gates over eligible evidence: {value["conditions"]["mandatory_hard_gates_passed"]}
- Semantic Subagents required/unlocked: {value["semantic_judges_required"]}
- Comparative ranking allowed: {value["ranking_allowed"]}
- Reason codes: {", ".join(value["reason_codes"])}
- Record hash: `{value["record_hash"]}`

Retry attempts do not increase independent-repeat depth unless they fill a previously missing
`case × arm × repeat` cell. The runner checkpoint's global schedule repeat depth is 0 because
CASE-006 has no complete repeat; this sufficiency record reports 1 across the three balanced cases.
Neither metric meets the frozen minimum of 2. Native semantic Subagents remain locked.
"""


def check_or_write_sufficiency(root: Path, *, check: bool) -> dict[str, Any]:
    expected = build_sufficiency(root)
    errors = validate_sufficiency(root, expected)
    errors.extend(check_or_write(root / SUFFICIENCY_PATH, expected, check=check))
    report = render_sufficiency_report(expected)
    report_path = root / SUFFICIENCY_REPORT_PATH
    if check:
        if not report_path.is_file() or report_path.read_text(encoding="utf-8") != report:
            errors.append("SUFFICIENCY_REPORT_MISMATCH")
    else:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "result": expected["result"],
        "eligible_primary_count": expected["actual"]["eligible_primary_count"],
        "balanced_case_count": expected["actual"]["balanced_case_count"],
        "independent_repeats": expected["actual"]["independent_repeats"],
        "semantic_subagents_unlocked": expected["semantic_judges_required"],
        "record_hash": expected["record_hash"],
    }
