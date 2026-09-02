#!/usr/bin/env python3
"""Validate the frozen experimental-only shadow prototype scope without implementing it."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.authorization.scope import validate_shadow_prototype_scope


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.parse_args()
    result = validate_shadow_prototype_scope(ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
