#!/usr/bin/env python3
"""Generate or check C2 evidence inputs, then close them after prosecution."""

import argparse
import json
from pathlib import Path

from cumcm_skill_lab.authorization_c2.candidate_evidence import (
    check_or_write_candidate_evidence,
    check_or_write_candidate_evidence_inputs,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--pre-audit",
        action="store_true",
        help="write or verify only L13-L15 before the independent prosecutor",
    )
    args = parser.parse_args()
    operation = (
        check_or_write_candidate_evidence_inputs
        if args.pre_audit
        else check_or_write_candidate_evidence
    )
    result = operation(Path.cwd(), check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
