#!/usr/bin/env python3
"""Generate or verify the Phase 002D-R1 formal decision audit."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.failure_aware.decision_audit import check_or_write_decision_audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check_or_write_decision_audit(ROOT, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
