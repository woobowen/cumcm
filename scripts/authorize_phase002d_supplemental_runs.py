#!/usr/bin/env python3
"""Create or verify the Phase 002D-R1 supplemental authorization and zero budget."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.failure_aware.supplemental import check_or_write_supplemental


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check_or_write_supplemental(ROOT, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
