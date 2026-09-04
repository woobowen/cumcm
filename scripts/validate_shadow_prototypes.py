#!/usr/bin/env python3
"""Validate the frozen architecture set through the common shadow interface."""

from __future__ import annotations

import argparse
import json
import sys

from _bootstrap import ROOT

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cumcm_skill_lab.shadow_validation.validation import validate_prototypes
from experiments.shadow_prototypes import ARCHITECTURE_IDS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without persistent output")
    parser.add_argument(
        "--architectures",
        nargs="+",
        choices=ARCHITECTURE_IDS,
        default=list(ARCHITECTURE_IDS),
        help="architecture IDs to validate (default: all frozen arms)",
    )
    args = parser.parse_args()
    result = validate_prototypes(ROOT, tuple(args.architectures))
    result["mode"] = "CHECK" if args.check else "VALIDATE"
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
