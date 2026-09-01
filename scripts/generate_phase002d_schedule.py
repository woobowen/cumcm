#!/usr/bin/env python3
"""Generate, verify, show, or summarize the Phase 002D blocked schedule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cumcm_skill_lab.expansion.models import read_json
from cumcm_skill_lab.expansion.schedule import SCHEDULE_PATH, check_or_write_schedule


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("continuation", "new-cohort"), required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true")
    action.add_argument("--show", action="store_true")
    action.add_argument("--status", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if args.show:
        print(json.dumps(read_json(root / SCHEDULE_PATH), ensure_ascii=False, indent=2))
        return 0
    result = check_or_write_schedule(root, mode=args.mode, check=args.check or args.status)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
