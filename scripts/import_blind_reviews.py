#!/usr/bin/env python3
import argparse
from pathlib import Path

from _bootstrap import ROOT

from cumcm_skill_lab.eval.review_import import import_reviews


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = args.input
    if source is not None and not source.is_absolute():
        source = ROOT / source
    result = import_reviews(ROOT, source, check=args.check)
    print(
        f"reviews={result['status']} count={result['review_count']} errors={len(result['errors'])}"
    )
    for error in result["errors"]:
        print(error)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
