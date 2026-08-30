#!/usr/bin/env python3
from _bootstrap import ROOT

from cumcm_skill_lab.repo_validation import scan_secrets


def main() -> int:
    result = scan_secrets(ROOT)
    for item in result["errors"]:
        print(f"{item['id']}: {item['path']}")
    print(f"secret_findings={len(result['errors'])}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
