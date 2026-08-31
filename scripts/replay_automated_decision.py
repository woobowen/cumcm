#!/usr/bin/env python3
"""Finalize and verify Phase 002B automated decisions with offline replay."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.formal_outputs import DECISION_FILENAMES
from cumcm_skill_lab.adjudication.models import write_json
from cumcm_skill_lab.adjudication.phase002b_replay import (
    build_replay,
    existing_replay_errors,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--config", default="adjudication/configs/phase-002b-v2.yaml")
    args = parser.parse_args()
    if args.check:
        errors = existing_replay_errors(ROOT)
        print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}))
        return 0 if not errors else 1
    decisions, replay = build_replay(ROOT)
    decision_dir = ROOT / "evals/results/phase-002b/automated_decisions"
    by_type = {item["decision_type"]: item for item in decisions}
    for filename, decision_type in zip(
        DECISION_FILENAMES, ("ARCHITECTURE", "RECOVERY_POLICY", "COMPONENTS"), strict=True
    ):
        write_json(decision_dir / filename, by_type[decision_type])
    write_json(ROOT / "evals/results/phase-002b/replay/replay.json", replay)
    errors = existing_replay_errors(ROOT)
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "stable": replay["stable"],
                "variants": replay["variants"],
                "errors": errors,
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
