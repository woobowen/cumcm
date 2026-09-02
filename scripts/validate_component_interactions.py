#!/usr/bin/env python3
"""Validate the frozen Phase 002D-R2 component interaction contract."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.interaction_validator import validate_component_interactions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    parser.parse_args()
    result = validate_component_interactions(ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
