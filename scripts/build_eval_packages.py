#!/usr/bin/env python3
import argparse

from _bootstrap import ROOT

from cumcm_skill_lab.eval.package_builder import build_packages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        ok, mismatches, manifests = build_packages(ROOT, check=args.check)
    except RuntimeError as exc:
        print(str(exc))
        return 1
    for manifest in manifests:
        print(
            f"arm={manifest['arm_id']} status={manifest['status']} "
            f"package_hash={manifest['package_hash']}"
        )
    if args.check:
        print(f"packages={'current' if ok else 'STALE'} mismatches={len(mismatches)}")
        return 0 if ok and all(item["status"] == "PACKAGE_SAFE" for item in manifests) else 1
    print(f"packages=generated changed={len(mismatches)}")
    return 0 if all(item["status"] == "PACKAGE_SAFE" for item in manifests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
