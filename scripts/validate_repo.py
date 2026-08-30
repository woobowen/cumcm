#!/usr/bin/env python3
import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.repo_validation import validate_repo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    result = validate_repo(ROOT, strict=args.strict)
    status = "PASS" if result["ok"] else "FAIL"
    summary = (
        f"repository={status} errors={result['error_count']} warnings={result['warning_count']}"
    )
    print(summary)
    for item in result["errors"]:
        print(f"{item['id']}: {item.get('path', '')} {item.get('message', '')}".rstrip())
    machine = json.dumps(result, ensure_ascii=False, sort_keys=True)
    print(machine)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            handle.write(machine + "\n")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
