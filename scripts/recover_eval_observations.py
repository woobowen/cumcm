#!/usr/bin/env python3
import argparse

from _bootstrap import ROOT

from cumcm_skill_lab.eval.recovery import recover_observations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = recover_observations(ROOT, check=args.check)
    print(
        f"recovery={result['status']} recovered={len(result['recovered'])} "
        f"errors={len(result['errors'])}"
    )
    for error in result["errors"]:
        print(error)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
