#!/usr/bin/env python3
"""Create or verify Phase 002D terminal reports and command ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cumcm_skill_lab.expansion.reporting import check_or_write_reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check_or_write_reports(Path.cwd(), check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
