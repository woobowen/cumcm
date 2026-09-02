#!/usr/bin/env python3
"""Create or verify Phase 002D-R1 quality-evidence sufficiency."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.failure_aware.decisions import check_or_write_sufficiency


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check_or_write_sufficiency(ROOT, scope="quality", check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
