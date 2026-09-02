#!/usr/bin/env python3
"""Execute or check the complete offline Phase 002D-R2 validation ledger."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.validation import check_validation, run_validation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check the recorded ledger")
    args = parser.parse_args()
    result = check_validation(ROOT) if args.check else run_validation(ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
