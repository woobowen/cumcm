#!/usr/bin/env python3
"""Reclassify and rescore frozen Phase 002 evidence into separate channels."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.coverage_scoring import write_coverage
from cumcm_skill_lab.adjudication.eligibility import write_eligibility
from cumcm_skill_lab.adjudication.evidence_freeze import verify_manifest
from cumcm_skill_lab.adjudication.models import read_json
from cumcm_skill_lab.adjudication.oracle_scoring import write_oracles
from cumcm_skill_lab.adjudication.process_evidence import write_process
from cumcm_skill_lab.adjudication.recovery_policy import write_recovery_policy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    parser.add_argument("--config", default="adjudication/configs/phase-002a.yaml")
    args = parser.parse_args()
    manifest = read_json(ROOT / "evals/results/phase-002a/evidence_freeze_manifest.json")
    errors = verify_manifest(ROOT, manifest)
    result = write_eligibility(ROOT, check=args.check)
    errors.extend(result["errors"])
    errors.extend(write_coverage(ROOT, check=args.check))
    errors.extend(write_oracles(ROOT, check=args.check))
    errors.extend(write_process(ROOT, check=args.check))
    errors.extend(write_recovery_policy(ROOT, check=args.check))
    output = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        **{k: v for k, v in result.items() if k != "errors"},
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
