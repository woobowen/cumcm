#!/usr/bin/env python3
"""Generate or check the C2 dependency resolution for C1 final finding 001."""

import argparse
import json
from pathlib import Path

from cumcm_skill_lab.authorization_c1.dependency_c2 import (
    check_or_write_dependency_resolution,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check_or_write_dependency_resolution(Path.cwd(), check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
