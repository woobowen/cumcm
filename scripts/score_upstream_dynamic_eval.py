#!/usr/bin/env python3
import argparse

from _bootstrap import ROOT

from cumcm_skill_lab.eval.score_pipeline import freeze_scores


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="evals/configs/phase-002.yaml")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.config != "evals/configs/phase-002.yaml":
        print("CONFIG_PATH_NOT_SUPPORTED")
        return 1
    result = freeze_scores(ROOT, check=args.check)
    print(
        f"scoring={result['status']} scores={result['score_count']} errors={len(result['errors'])}"
    )
    for error in result["errors"]:
        print(error)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
