#!/usr/bin/env python3
"""Apply or check the sole formal Phase 002D-R2 state transition."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.state_transition import check_or_write_state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    args = parser.parse_args()
    result = check_or_write_state(ROOT, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
