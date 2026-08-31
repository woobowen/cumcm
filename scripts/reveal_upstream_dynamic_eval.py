#!/usr/bin/env python3
import argparse

from _bootstrap import ROOT

from cumcm_skill_lab.eval.reveal import reveal_identities


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = reveal_identities(ROOT, check=args.check)
    print(f"reveal={result['status']} errors={len(result['errors'])}")
    for error in result["errors"]:
        print(error)
    if result["status"] == "PASS" and not args.check:
        for anonymous, actual in sorted(result["record"]["anonymous_to_actual"].items()):
            print(f"{anonymous}={actual}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
