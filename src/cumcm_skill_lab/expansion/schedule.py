"""Fixed-seed blocked randomized schedule for Phase 002D."""

from __future__ import annotations

import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .cohort import COHORT_PATH
from .models import (
    ANONYMOUS_ARMS,
    PRIMARY_CASES,
    RESULT_ROOT,
    check_or_write,
    hashed_body,
    read_json,
    sha256_json,
)

SCHEDULE_PATH = RESULT_ROOT / "schedule/schedule.json"
SCHEDULE_SCHEMA_PATH = Path("contracts/expansion_schedule.schema.json")
SCHEDULE_SEED = 20260901


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_schedule(root: Path, *, mode: str, generated_at: str | None = None) -> dict[str, Any]:
    cohort = read_json(root / COHORT_PATH)
    expected_mode = {
        "continuation": "CONTINUATION_COHORT",
        "new-cohort": "NEW_MODEL_COHORT",
    }.get(mode)
    if expected_mode is None:
        raise ValueError(f"UNKNOWN_SCHEDULE_MODE:{mode}")
    if cohort["mode"] != expected_mode:
        raise RuntimeError("SCHEDULE_MODE_COHORT_MISMATCH")
    generator = random.Random(SCHEDULE_SEED)
    blocks: list[dict[str, Any]] = []
    primary_queue: list[str] = []
    retry_queue: list[dict[str, Any]] = []
    block_number = 0
    for case_id in PRIMARY_CASES:
        for repeat_id in range(1, cohort["minimum_repeats"] + 1):
            block_number += 1
            order = list(ANONYMOUS_ARMS)
            generator.shuffle(order)
            block_id = f"BLOCK-{block_number:03d}-{case_id}-R{repeat_id}"
            planned = []
            for position, arm_id in enumerate(order, start=1):
                cell_id = f"{case_id}-{arm_id}-R{repeat_id}"
                attempt_id = f"EXP-{case_id}-{arm_id}-R{repeat_id}-A01"
                primary_queue.append(attempt_id)
                planned.append(
                    {
                        "cell_id": cell_id,
                        "anonymous_arm_id": arm_id,
                        "schedule_order": position,
                        "primary_attempt_id": attempt_id,
                        "retry_attempt_ids": [
                            f"EXP-{case_id}-{arm_id}-R{repeat_id}-A02",
                            f"EXP-{case_id}-{arm_id}-R{repeat_id}-A03",
                        ],
                    }
                )
                for retry_index in (2, 3):
                    retry_queue.append(
                        {
                            "attempt_id": f"EXP-{case_id}-{arm_id}-R{repeat_id}-A0{retry_index}",
                            "retry_of": attempt_id,
                            "cell_id": cell_id,
                            "block_id": block_id,
                            "case_id": case_id,
                            "repeat_id": repeat_id,
                            "anonymous_arm_id": arm_id,
                            "retry_index": retry_index - 1,
                            "eligible_only_after_predecessor_failure": True,
                        }
                    )
            blocks.append(
                {
                    "block_id": block_id,
                    "block_number": block_number,
                    "case_id": case_id,
                    "repeat_id": repeat_id,
                    "anonymous_arm_order": order,
                    "planned_attempts": planned,
                }
            )
    body = {
        "schema_version": "1.0.0",
        "schedule_id": "PHASE-002D-BLOCKED-SCHEDULE-001",
        "seed": SCHEDULE_SEED,
        "cohort_id": cohort["cohort_id"],
        "cohort_hash": cohort["cohort_hash"],
        "mode": cohort["mode"],
        "generated_at": generated_at or _now(),
        "cases": list(PRIMARY_CASES),
        "repeats": cohort["minimum_repeats"],
        "anonymous_arms": list(ANONYMOUS_ARMS),
        "blocks": blocks,
        "primary_queue": primary_queue,
        "retry_queue": retry_queue,
        "primary_attempt_count": len(primary_queue),
        "maximum_retry_slots": len(retry_queue),
        "deviation_policy": {
            "complete_current_block_before_retry": True,
            "retry_queue_order_frozen": True,
            "successful_cell_never_repeated": True,
            "maximum_attempts_per_cell": 3,
            "post_result_reordering_allowed": False,
            "arm_first_execution_allowed": False,
        },
        "scored_runs_started_at_freeze": False,
    }
    return hashed_body(body, "schedule_hash")


def validate_schedule(root: Path, schedule: dict[str, Any]) -> list[str]:
    schema = read_json(root / SCHEDULE_SCHEMA_PATH)
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(schedule)]
    body = dict(schedule)
    recorded = body.pop("schedule_hash", None)
    if sha256_json(body) != recorded:
        errors.append("SCHEDULE_HASH_MISMATCH")
    if len(set(schedule["primary_queue"])) != schedule["primary_attempt_count"]:
        errors.append("PRIMARY_ATTEMPT_ID_DUPLICATE")
    for block in schedule["blocks"]:
        if set(block["anonymous_arm_order"]) != set(ANONYMOUS_ARMS):
            errors.append(f"BLOCK_ARM_SET_INVALID:{block['block_id']}")
    flattened = [arm for block in schedule["blocks"] for arm in block["anonymous_arm_order"]]
    if any(flattened[index : index + 3] == [arm] * 3 for index, arm in enumerate(flattened)):
        errors.append("ARM_CONTIGUOUS_BIAS")
    return sorted(set(errors))


def check_or_write_schedule(root: Path, *, mode: str, check: bool) -> dict[str, Any]:
    existing = read_json(root / SCHEDULE_PATH) if (root / SCHEDULE_PATH).is_file() else None
    generated_at = existing["generated_at"] if existing else None
    expected = build_schedule(root, mode=mode, generated_at=generated_at)
    errors = validate_schedule(root, expected)
    errors.extend(check_or_write(root / SCHEDULE_PATH, expected, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "schedule_id": expected["schedule_id"],
        "schedule_hash": expected["schedule_hash"],
        "blocks": len(expected["blocks"]),
        "primary_attempts": expected["primary_attempt_count"],
        "retry_slots": expected["maximum_retry_slots"],
    }
