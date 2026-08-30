#!/usr/bin/env python3
from _bootstrap import ROOT

from cumcm_skill_lab.repo_validation import scan_private_paths, scan_secrets


def main() -> int:
    result = scan_secrets(ROOT)
    for item in result["errors"]:
        print(f"{item['id']}: {item['path']}")
    privacy = scan_private_paths(ROOT)
    for item in privacy["errors"]:
        print(f"{item['id']}: {item['path']}")
    print(f"secret_findings={len(result['errors'])}")
    print(f"private_path_findings={len(privacy['errors'])}")
    return 1 if result["errors"] or privacy["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
