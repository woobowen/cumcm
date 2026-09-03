#!/usr/bin/env python3
"""Evaluate the frozen public-only competition architecture gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _bootstrap import ROOT

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cumcm_skill_lab.shadow_validation.competition_gate import evaluate_competition_gate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="optional result path under evals/results/phase-003f",
    )
    args = parser.parse_args()
    result = evaluate_competition_gate(ROOT)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        target = args.output.resolve()
        allowed = (ROOT / "evals/results/phase-003f").resolve()
        if target != allowed and allowed not in target.parents:
            parser.error("--output must be within evals/results/phase-003f")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(target)
    print(rendered, end="")
    return 0 if result["selected_architecture"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
