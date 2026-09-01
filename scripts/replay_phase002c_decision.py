#!/usr/bin/env python3
"""Create or verify the offline deterministic Phase 002C replay and route."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.phase002c_replay import write_replay


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = write_replay(ROOT, check=args.check)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
