#!/usr/bin/env python3
import argparse

from _bootstrap import ROOT

from cumcm_skill_lab.eval.case_generation import materialize


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--seed", type=int, default=20260831)
    args = parser.parse_args()
    ok, mismatches = materialize(ROOT, seed=args.seed, check=args.check)
    if args.check:
        print(f"fixtures={'current' if ok else 'STALE'} mismatches={len(mismatches)}")
        for item in mismatches:
            print(f"FIXTURE_MISMATCH: {item}")
        return 0 if ok else 1
    print(f"fixtures=generated changed={len(mismatches)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
