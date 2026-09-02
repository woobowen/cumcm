#!/usr/bin/env python3
"""Generate or check the synthetic prospective Phase 002D-R2 Benchmark."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.benchmark_generator import (
    materialize_benchmark,
    refresh_tracked_benchmark,
)
from cumcm_skill_lab.specification.benchmark_integrity import validate_prospective_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    parser.add_argument(
        "--initialize-vault",
        action="store_true",
        help="create one ignored hidden-seed vault; refuses overwrite",
    )
    args = parser.parse_args()
    if args.check and args.initialize_vault:
        parser.error("--check never initializes hidden material")
    if args.check:
        result = validate_prospective_benchmark(ROOT)
    elif args.initialize_vault:
        result = materialize_benchmark(ROOT, initialize_vault=True)
    else:
        result = refresh_tracked_benchmark(ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
