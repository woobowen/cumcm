#!/usr/bin/env python3
"""Check hidden Benchmark vault isolation without reading private values."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.vault_manifest import check_benchmark_vault


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    parser.parse_args()
    result = check_benchmark_vault(ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
