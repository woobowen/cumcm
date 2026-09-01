#!/usr/bin/env python3
"""Build or verify compact Phase 002B formal-role evidence bundles."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.bundles import build_all


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="adjudication/configs/phase-002b-v2.yaml")
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()
    if args.config != "adjudication/configs/phase-002b-v2.yaml":
        parser.error("Formal Phase 002B runs are bound to phase-002b-v2 after MODEL_UNAVAILABLE")
    result = build_all(ROOT, check=args.check, config_path=args.config)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
