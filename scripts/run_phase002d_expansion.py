#!/usr/bin/env python3
"""Run, inspect, or verify controlled Phase 002D expansion batches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cumcm_skill_lab.expansion.attempt_ledger import load_attempts
from cumcm_skill_lab.expansion.models import ANONYMOUS_ARMS, CONFIG_PATH, PRIMARY_CASES, read_json
from cumcm_skill_lab.expansion.pilot import check_pilot
from cumcm_skill_lab.expansion.runner import (
    check_runner,
    next_planned_attempts,
    run_batch,
    runner_status,
)
from cumcm_skill_lab.expansion.schedule import SCHEDULE_PATH


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=CONFIG_PATH.as_posix())
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--max-new-attempts", type=int)
    parser.add_argument("--cases", nargs="+", choices=PRIMARY_CASES)
    parser.add_argument("--arms", nargs="+", choices=ANONYMOUS_ARMS)
    parser.add_argument("--repeats", nargs="+", type=int, choices=(1, 2))
    parser.add_argument("--resume", action="store_true")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true")
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--status", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = Path.cwd()
    configured = Path(args.config)
    if configured != CONFIG_PATH:
        raise SystemExit("ALTERNATE_CONFIG_FORBIDDEN_AFTER_FREEZE")
    if (
        args.batch_size is not None
        and args.max_new_attempts is not None
        and args.batch_size != args.max_new_attempts
    ):
        raise SystemExit("BATCH_LIMIT_ARGUMENT_MISMATCH")
    limit = args.max_new_attempts or args.batch_size or 3
    if args.pilot:
        result = check_pilot(root)
    elif args.check:
        result = check_runner(root)
    elif args.status:
        result = runner_status(root)
    elif args.dry_run:
        filters = {
            "case_id": set(args.cases or ()),
            "anonymous_arm_id": set(args.arms or ()),
            "repeat_id": set(args.repeats or ()),
        }
        planned = next_planned_attempts(
            read_json(root / SCHEDULE_PATH),
            load_attempts(root),
            limit=limit,
            filters=filters,
        )
        result = {
            "status": "DRY_RUN",
            "would_resume_workflow": args.resume,
            "fresh_codex_sessions_only": True,
            "maximum_new_attempts": limit,
            "planned_attempts": planned,
            "runner": check_runner(root),
        }
    else:
        filters = {
            "case_id": set(args.cases or ()),
            "anonymous_arm_id": set(args.arms or ()),
            "repeat_id": set(args.repeats or ()),
        }
        attempts = run_batch(root, maximum_new_attempts=limit, filters=filters)
        result = {
            "status": "BATCH_COMPLETE",
            "new_attempt_ids": [attempt["attempt_id"] for attempt in attempts],
            "new_attempt_count": len(attempts),
            "runner": check_runner(root),
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result.get("check_status") == "FAIL" or result.get("status") in {
        "FAIL",
        "INPUT_FREEZE_BROKEN",
    }:
        return 1
    if isinstance(result.get("runner"), dict) and result["runner"].get("check_status") == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
