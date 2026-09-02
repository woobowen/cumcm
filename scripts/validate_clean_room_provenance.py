#!/usr/bin/env python3
"""Create or check Phase 002D-R2 clean-room provenance evidence."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.provenance_validator import validate_clean_room_provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    args = parser.parse_args()
    result = validate_clean_room_provenance(ROOT, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
