#!/usr/bin/env python3
"""Create or verify the Phase 002D-R3 shadow-validation input freeze."""

from __future__ import annotations

import argparse
import json
import sys

from _bootstrap import ROOT

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cumcm_skill_lab.shadow_validation.input_freeze import (
    FREEZE_ID,
    verify_input_freeze,
    write_input_freeze,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.add_argument("--subject-commit", help="bind the state snapshot to this Git commit")
    args = parser.parse_args()
    if args.check:
        errors = verify_input_freeze(ROOT)
        result = {
            "freeze_id": FREEZE_ID,
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
        }
    else:
        artifact = write_input_freeze(ROOT, subject_commit=args.subject_commit)
        errors = verify_input_freeze(ROOT)
        result = {
            "freeze_id": FREEZE_ID,
            "manifest_hash": artifact["manifest_hash"],
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
