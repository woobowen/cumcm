#!/usr/bin/env python3
"""Create or verify the offline deterministic Phase 002C pre-adjudication gate."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.native_subagent_audits import write_first_round_bundles
from cumcm_skill_lab.adjudication.pre_adjudication import write_pre_adjudication


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = write_pre_adjudication(ROOT, check=args.check)
    if result["status"] == "PASS":
        errors = write_first_round_bundles(ROOT, check=args.check)
        result["errors"].extend(errors)
        result["status"] = "PASS" if not result["errors"] else "FAIL"
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
