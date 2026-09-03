#!/usr/bin/env python3
"""Normalize or check the independent C1 final authorization audit."""

import argparse
import json
from pathlib import Path

from cumcm_skill_lab.authorization_c1.final_audit import check_or_write_final_audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check_or_write_final_audit(Path.cwd(), check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
