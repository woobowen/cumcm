#!/usr/bin/env python3
import argparse

from _bootstrap import ROOT

from cumcm_skill_lab.skill_validation import validate_skills


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-name", default="cumcm-modeling-evidence")
    parser.add_argument("--expected-count", type=int, default=1)
    args = parser.parse_args()
    result = validate_skills(ROOT, args.expected_name, args.expected_count)
    print(f"skills={result['skills']} names={result['names']}")
    for item in result["errors"]:
        print(f"{item['id']}: {item['message']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
