#!/usr/bin/env python3
from _bootstrap import ROOT

from cumcm_skill_lab.instruction_validation import validate_instructions


def main() -> int:
    result = validate_instructions(ROOT)
    for path, size in result["sizes"].items():
        print(f"{path}: {size} bytes")
    for item in result["warnings"] + result["errors"]:
        print(f"{item['id']}: {item['message']}")
    print(f"total project AGENTS bytes: {result['total_project_bytes']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
