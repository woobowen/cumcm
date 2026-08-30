#!/usr/bin/env python3
import argparse

from _bootstrap import ROOT

from cumcm_skill_lab.report_generation import generate_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    ok, _ = generate_status(ROOT, check=args.check)
    if args.check:
        print("status_report=current" if ok else "STATUS_REPORT_STALE")
    else:
        print("status_report=generated")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
