"""Compute comparative evidence sufficiency from frozen run records."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .models import read_json, sha256_json

PRIMARY_COMPLETE = "PRIMARY_COMPLETE"
RECOVERY_AFFECTED = "RECOVERY_AFFECTED"
FAILED = "FAILED"
SUPERSEDED = "SUPERSEDED"
NOT_RUN = "NOT_RUN"


def collect_evidence_items(root: Path) -> list[dict[str, Any]]:
    """Project each historical attempt into an explicit non-overlapping eligibility view."""
    classification = read_json(root / "evals/results/phase-002a/eligibility/classification.json")
    current = {
        (item["anonymous_arm_id"], item["case_id"], item["run_index"]): item["classification"]
        for item in classification["cells"]
    }
    current_by_cell = {
        (item["anonymous_arm_id"], item["case_id"]): item["run_index"]
        for item in classification["cells"]
    }
    items: list[dict[str, Any]] = []
    run_root = root / "evals/results/phase-002/runs"
    for path in sorted(run_root.rglob("*.json")):
        run = read_json(path)
        arm = run["anonymous_arm_id"]
        case = run["case_id"]
        index = run["run_index"]
        status = run["completion_status"]
        key = (arm, case, index)
        if key in current:
            eligibility = current[key]
        elif current_by_cell.get((arm, case)) != index:
            eligibility = SUPERSEDED
        elif status == "FAILED":
            eligibility = FAILED
        elif status == "NOT_RUN":
            eligibility = NOT_RUN
        else:
            eligibility = "INELIGIBLE"
        ranking_eligible = bool(
            eligibility == PRIMARY_COMPLETE
            and status == "COMPLETED"
            and run.get("schema_valid") is True
        )
        exclusion_reasons = []
        if not ranking_eligible:
            exclusion_reasons.append(eligibility)
        if status == "FAILED":
            exclusion_reasons.append(FAILED)
        elif status == "NOT_RUN":
            exclusion_reasons.append(NOT_RUN)
        items.append(
            {
                "evidence_id": f"RUN:{arm}:{case}:run-{index:03d}",
                "anonymous_arm_id": arm,
                "case_id": case,
                "run_index": index,
                "completion_status": status,
                "schema_valid": bool(run.get("schema_valid")),
                "task_input_hash": run.get("task_input_hash"),
                "classification": eligibility,
                "ranking_eligible": ranking_eligible,
                "exclusion_reasons": sorted(set(exclusion_reasons)),
                "run_path": path.relative_to(root).as_posix(),
            }
        )
    return items


def compute_evidence_sufficiency(
    items: list[dict[str, Any]],
    *,
    balanced_case_minimum: int,
    minimum_repeats: int,
    required_arms: list[str] | None = None,
    frozen_evidence_valid: bool = True,
    mandatory_hard_gates_passed: bool = True,
    input_freeze_id: str = "TEST-FREEZE",
    input_freeze_hash: str = "0" * 64,
    policy_id: str = "TEST-POLICY",
    policy_hash: str = "0" * 64,
) -> dict[str, Any]:
    """Apply frozen quantitative minima without scores, votes, or semantic inference."""
    if balanced_case_minimum < 1 or minimum_repeats < 1:
        raise ValueError("INVALID_FROZEN_THRESHOLD")
    arms = required_arms or sorted(
        {
            item["anonymous_arm_id"]
            for item in items
            if isinstance(item.get("anonymous_arm_id"), str)
        }
    )
    if not arms:
        raise ValueError("REQUIRED_ARMS_MISSING")
    identities = [
        (item.get("anonymous_arm_id"), item.get("case_id"), item.get("run_index")) for item in items
    ]
    duplicate_identities = sorted(
        identity for identity, count in Counter(identities).items() if count > 1
    )
    if duplicate_identities:
        raise ValueError(f"DUPLICATE_EVIDENCE_ID:{duplicate_identities[0]}")
    eligible = [item for item in items if item.get("ranking_eligible") is True]
    by_case_arm: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    case_hashes: dict[str, set[str]] = defaultdict(set)
    arm_hashes: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    missing_hash_cases: set[str] = set()
    for item in eligible:
        case_id = item.get("case_id")
        task_hash = item.get("task_input_hash")
        if isinstance(case_id, str) and isinstance(task_hash, str) and task_hash:
            case_hashes[case_id].add(task_hash)
            arm_hashes[case_id][item["anonymous_arm_id"]].add(task_hash)
        elif isinstance(case_id, str):
            missing_hash_cases.add(case_id)
    for item in eligible:
        by_case_arm[item["case_id"]][item["anonymous_arm_id"]].append(item)

    balanced_cases = sorted(
        case_id
        for case_id, arm_rows in by_case_arm.items()
        if all(arm_rows.get(arm) for arm in arms)
        and len(case_hashes.get(case_id, set())) == 1
        and case_id not in missing_hash_cases
    )
    independent_repeats = min(
        (len(by_case_arm[case_id][arm]) for case_id in balanced_cases for arm in arms),
        default=0,
    )
    mismatched_cases = sorted(
        {case for case, hashes in case_hashes.items() if len(hashes) != 1} | missing_hash_cases
    )
    status_counts = Counter(item.get("completion_status") for item in items)
    class_counts = Counter(item.get("classification") for item in items)
    conditions = {
        "balanced_case_minimum_met": len(balanced_cases) >= balanced_case_minimum,
        "minimum_repeats_met": independent_repeats >= minimum_repeats,
        "frozen_evidence_valid": frozen_evidence_valid,
        "mandatory_hard_gates_passed": (mandatory_hard_gates_passed and not mismatched_cases),
    }
    reasons: list[str] = []
    if not frozen_evidence_valid:
        result = "STALE"
        reasons.append("FROZEN_EVIDENCE_INVALID")
    else:
        if not conditions["balanced_case_minimum_met"]:
            reasons.append("BALANCED_CASE_MINIMUM_NOT_MET")
        if not conditions["minimum_repeats_met"]:
            reasons.append("MINIMUM_REPEATS_NOT_MET")
        if mismatched_cases:
            reasons.append("TASK_INPUT_HASH_MISMATCH")
        if not mandatory_hard_gates_passed:
            reasons.append("MANDATORY_HARD_GATE_FAILED")
        result = "SUFFICIENT" if all(conditions.values()) else "INSUFFICIENT"
    if not reasons:
        reasons.append("FROZEN_EVIDENCE_MINIMA_MET")
    record = {
        "sufficiency_id": "EVIDENCE-SUFFICIENCY-PHASE-002C",
        "input_freeze_id": input_freeze_id,
        "input_freeze_hash": input_freeze_hash,
        "policy_id": policy_id,
        "policy_hash": policy_hash,
        "thresholds": {
            "balanced_case_minimum": balanced_case_minimum,
            "minimum_repeats": minimum_repeats,
        },
        "actual": {
            "eligible_primary_count": len(eligible),
            "balanced_cases": balanced_cases,
            "balanced_case_count": len(balanced_cases),
            "independent_repeats": independent_repeats,
            "cell_repeat_counts": {
                case_id: {arm: len(by_case_arm[case_id].get(arm, [])) for arm in arms}
                for case_id in sorted(by_case_arm)
            },
            "recovery_excluded_count": class_counts[RECOVERY_AFFECTED],
            "failed_excluded_count": status_counts["FAILED"],
            "superseded_excluded_count": class_counts[SUPERSEDED],
            "not_run_excluded_count": status_counts["NOT_RUN"],
        },
        "required_arms": arms,
        "task_hash_consistency": {
            "passed": not mismatched_cases,
            "mismatched_cases": mismatched_cases,
            "case_hashes": {case: sorted(hashes) for case, hashes in sorted(case_hashes.items())},
            "arm_hashes": {
                case: {arm: sorted(hashes) for arm, hashes in sorted(values.items())}
                for case, values in sorted(arm_hashes.items())
            },
        },
        "conditions": conditions,
        "result": result,
        "reason_codes": reasons,
        "semantic_judges_required": result == "SUFFICIENT",
        "ranking_allowed": result == "SUFFICIENT",
        "evidence_items_hash": sha256_json(sorted(items, key=sha256_json)),
    }
    record["record_hash"] = sha256_json(record)
    return record
