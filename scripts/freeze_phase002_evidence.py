#!/usr/bin/env python3
"""Create or verify the Phase 002 evidence freeze manifest."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.evidence_freeze import freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.add_argument("--config", default="adjudication/configs/phase-002a.yaml")
    args = parser.parse_args()
    result = freeze(ROOT, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
