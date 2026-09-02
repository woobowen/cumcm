#!/usr/bin/env python3
"""Prepare isolated author inputs or validate Phase 002D-R2 component specifications."""

from __future__ import annotations

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.specification.component_validator import (
    build_component_author_bundles,
    seal_component_outputs,
    validate_component_author_bundles,
    validate_component_specifications,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    parser.add_argument(
        "--prepare-bundles",
        action="store_true",
        help="write deterministic peer-isolated component-author bundles",
    )
    parser.add_argument(
        "--seal-from-raw",
        action="store_true",
        help="seal saved schema-valid raw author JSON as formal specifications",
    )
    args = parser.parse_args()
    if args.prepare_bundles and args.seal_from_raw:
        parser.error("--prepare-bundles and --seal-from-raw are mutually exclusive")
    if args.seal_from_raw:
        hashes = seal_component_outputs(ROOT)
        result = validate_component_specifications(ROOT)
        result["specification_hashes"] = hashes
    elif args.prepare_bundles:
        bundles = build_component_author_bundles(ROOT)
        errors = validate_component_author_bundles(ROOT)
        result = {
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
            "bundle_hashes": {key: value["bundle_hash"] for key, value in bundles.items()},
        }
    else:
        result = validate_component_specifications(ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
