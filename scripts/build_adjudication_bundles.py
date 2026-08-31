#!/usr/bin/env python3
"""Build or verify compact Phase 002B formal-role evidence bundles."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.bundles import build_all


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="adjudication/configs/phase-002a.yaml")
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()
    if args.config != "adjudication/configs/phase-002a.yaml":
        parser.error("Phase 002B is bound to adjudication/configs/phase-002a.yaml")
    result = build_all(ROOT, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
