#!/usr/bin/env python3
import argparse

from _bootstrap import ROOT

from cumcm_skill_lab.eval.reporting import summarize_evaluation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="evals/configs/phase-002.yaml")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    config = ROOT / args.config
    if not config.is_file():
        print(f"REPORT_CONFIG_MISSING:{args.config}")
        return 1
    result = summarize_evaluation(ROOT, check=args.check)
    print(
        f"reporting={result['status']} outputs={result['output_count']} "
        f"errors={len(result['errors'])}"
    )
    for error in result["errors"]:
        print(error)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
