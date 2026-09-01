#!/usr/bin/env python3
"""Generate or verify every current Phase 002A report from machine records."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.reporting import write_reports
from cumcm_skill_lab.eval.reporting import build_outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify reports without writes")
    parser.add_argument(
        "--historical-only",
        action="store_true",
        help="migrate only superseded Phase 002 proposal reports",
    )
    parser.add_argument("--config", default="adjudication/configs/phase-002a.yaml")
    args = parser.parse_args()
    errors = []
    historical_outputs, historical_errors = build_outputs(ROOT)
    errors.extend(historical_errors)
    for relative in (
        "reports/base_selection_proposal.md",
        "reports/component_portfolio_proposal.md",
        "reports/archive/phase-002-human-gate-base-selection.md",
    ):
        path = ROOT / relative
        expected = historical_outputs[relative]
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                errors.append(f"REPORT_MISMATCH:{relative}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    if not args.historical_only:
        errors.extend(write_reports(ROOT, check=args.check))
    print(
        json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, sort_keys=True)
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
