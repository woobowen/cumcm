#!/usr/bin/env python3
from _bootstrap import ROOT

from cumcm_skill_lab.upstream_validation import validate_upstreams


def main() -> int:
    result = validate_upstreams(ROOT)
    print(
        f"candidates={result['candidate_count']} cache_ignored={result.get('cache_ignored', False)}"
    )
    for item in result["errors"]:
        print(f"{item['id']}: {item['message']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
