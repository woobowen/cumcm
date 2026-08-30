#!/usr/bin/env python3
from _bootstrap import ROOT

from cumcm_skill_lab.schema_validation import validate_contracts


def main() -> int:
    result = validate_contracts(ROOT)
    summary = (
        f"schemas={result['schema_count']} valid={result['valid_fixtures']} "
        f"invalid_rejected={result['invalid_rejected']}"
    )
    print(summary)
    for item in result["errors"]:
        print(f"{item['id']}: {item.get('path', '')} {item['message']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
