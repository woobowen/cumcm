#!/usr/bin/env python3
"""Create or check the Phase 002D strict-risk compatibility replay."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.phase002d_compatibility import (
    write_risk_compatibility_replay,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = write_risk_compatibility_replay(ROOT, check=args.check)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
