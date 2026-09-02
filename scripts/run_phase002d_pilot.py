#!/usr/bin/env python3
"""Run or verify the non-scored Phase 002D calibration pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cumcm_skill_lab.expansion.pilot import check_pilot, run_pilot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if not args.check:
        run_pilot(root)
    result = check_pilot(root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
