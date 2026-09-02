#!/usr/bin/env python3
"""Prepare, seal or check the independent Phase 002D-R2 Decision Audit."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.decision_audit import (
    check_or_write_auditor_bundle,
    check_or_write_decision_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    parser.add_argument(
        "--prepare-bundle",
        action="store_true",
        help="write only the identity-blind read-only Auditor bundle",
    )
    args = parser.parse_args()
    if args.check and args.prepare_bundle:
        parser.error("--check and --prepare-bundle are mutually exclusive")
    result = (
        check_or_write_auditor_bundle(ROOT, check=False)
        if args.prepare_bundle
        else check_or_write_decision_audit(ROOT, check=args.check)
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
