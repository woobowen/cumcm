#!/usr/bin/env python3
"""Seal or verify normalized Phase 002D-R1 native Subagent audit outputs."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.failure_aware.native_audits import (
    check_or_seal_decision_auditor,
    check_or_seal_first_round_audits,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--post-decision", action="store_true")
    args = parser.parse_args()
    if args.post_decision:
        result = check_or_seal_decision_auditor(ROOT, check=args.check)
    else:
        result = check_or_seal_first_round_audits(ROOT, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
