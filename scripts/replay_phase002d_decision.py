#!/usr/bin/env python3
"""Replay the deterministic Phase 002D incomplete route without decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cumcm_skill_lab.expansion.closure import check_or_write_closure


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check_or_write_closure(Path.cwd(), check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
