#!/usr/bin/env python3
"""Generate or verify all Phase 002B authoritative reports."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.phase002b_reporting import write_reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--config", default="adjudication/configs/phase-002b-v2.yaml")
    args = parser.parse_args()
    errors = write_reports(ROOT, check=args.check)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
