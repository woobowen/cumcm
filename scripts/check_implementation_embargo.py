#!/usr/bin/env python3
"""Create or verify the Phase 002D-R2 implementation embargo."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.implementation_embargo import check_or_write_embargo


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create or verify the Phase 002D-R2 implementation embargo."
    )
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()
    result = check_or_write_embargo(ROOT, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
