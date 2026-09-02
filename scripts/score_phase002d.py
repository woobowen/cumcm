#!/usr/bin/env python3
"""Generate or verify Phase 002D evidence and cost summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cumcm_skill_lab.expansion.cost import check_or_write_cost
from cumcm_skill_lab.expansion.runner import check_runner
from cumcm_skill_lab.expansion.score_audit import check_or_write_score_audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    score_audit = check_or_write_score_audit(root, batch_id=args.batch, check=args.check)
    cost = check_or_write_cost(root, batch_id=args.batch, check=args.check)
    result = {"cost": cost, "score_audit": score_audit, "runner": check_runner(root)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return (
        0
        if cost["status"] == "PASS"
        and score_audit["status"] == "PASS"
        and result["runner"]["check_status"] == "PASS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
