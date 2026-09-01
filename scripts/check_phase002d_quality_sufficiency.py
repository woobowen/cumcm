#!/usr/bin/env python3
"""Verify the unchanged quality-only Gate without treating insufficiency as a tool error."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.failure_aware.evidence_scopes import check_or_write_evidence_scopes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check_or_write_evidence_scopes(ROOT, check=args.check)
    output = {"status": result["status"], **result["quality"], "errors": result["errors"]}
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
