#!/usr/bin/env python3
"""Freeze or check pre-implementation Phase 002D-R2 metrics and thresholds."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.threshold_validator import freeze_thresholds, validate_thresholds


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    args = parser.parse_args()
    result = validate_thresholds(ROOT) if args.check else freeze_thresholds(ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
