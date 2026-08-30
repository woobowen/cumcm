#!/usr/bin/env python3
from _bootstrap import ROOT

from cumcm_skill_lab.leakage_validation import scan_leakage


def main() -> int:
    result = scan_leakage(ROOT)
    for item in result["findings"]:
        print(f"{item['id']}: {item['path']}:{item['line']}")
    print(f"leakage_findings={len(result['findings'])}")
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
