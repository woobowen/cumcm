#!/usr/bin/env python3
"""Write or verify sanitized terminal records for incomplete Phase 002B recovery."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.recovery_record import (
    check_incomplete_recovery,
    write_incomplete_recovery,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        write_incomplete_recovery(ROOT)
    errors = check_incomplete_recovery(ROOT)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
