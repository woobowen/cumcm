#!/usr/bin/env python3
import argparse
import json
import sys

from _bootstrap import ROOT

from cumcm_skill_lab.eval.runner import capability_smoke, run_evaluation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="evals/configs/phase-002.yaml")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--arms", nargs="*")
    parser.add_argument("--cases", nargs="*")
    parser.add_argument("--max-new-runs", type=int)
    args = parser.parse_args()
    config_path = ROOT / args.config
    if args.smoke:
        record = capability_smoke(ROOT, config_path, ["codex"])
        print(json.dumps(record, ensure_ascii=False, sort_keys=True))
        return 0 if record["status"] == "AVAILABLE" else 1
    command = (
        [sys.executable, str(ROOT / "tests/fixtures/mock_codex.py")] if args.mock else ["codex"]
    )
    kind = "MOCK" if args.mock else "REAL"
    try:
        results = run_evaluation(
            ROOT,
            config_path,
            execution_kind=kind,
            command_prefix=command,
            arm_filter=args.arms,
            case_filter=args.cases,
            max_new_runs=args.max_new_runs,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(str(exc))
        return 1
    counts: dict[str, int] = {}
    for result in results:
        status = result["completion_status"]
        counts[status] = counts.get(status, 0) + 1
    print(f"execution_kind={kind} runs={len(results)} status={json.dumps(counts, sort_keys=True)}")
    return 0 if all(item["completion_status"] == "COMPLETED" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
