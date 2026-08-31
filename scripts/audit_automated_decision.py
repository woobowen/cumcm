#!/usr/bin/env python3
"""Run or verify the independent Phase 002B Decision Auditor."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.bundles.builder import build_all
from cumcm_skill_lab.adjudication.bundles.role_views import ROLE_ORDER
from cumcm_skill_lab.adjudication.formal_outputs import (
    formal_output_path,
    is_formal_output_valid,
    proposal_decision_paths,
)
from cumcm_skill_lab.adjudication.models import read_json
from cumcm_skill_lab.adjudication.role_orchestrator import RoleOrchestrator
from cumcm_skill_lab.adjudication.transport.runtime_budget import RunBudget

ROLE = "DECISION_AUDITOR"


def _check() -> list[str]:
    errors = [
        f"ROLE_OUTPUT_INVALID:{role}"
        for role in ROLE_ORDER
        if not is_formal_output_valid(ROOT, role)
    ]
    if len(proposal_decision_paths(ROOT)) != 3:
        errors.append("PRE_AUDIT_DECISIONS_INCOMPLETE")
    if not errors:
        audit = read_json(formal_output_path(ROOT, ROLE))
        if audit["result"] not in {"PASS", "FAIL", "RETEST_REQUIRED"}:
            errors.append("AUDIT_RESULT_INVALID")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--config", default="adjudication/configs/phase-002b-v2.yaml")
    parser.add_argument("--transport", choices=("auto",), default="auto")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.check:
        errors = _check()
        print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}))
        return 0 if not errors else 1
    missing = [role for role in ROLE_ORDER[:5] if not is_formal_output_valid(ROOT, role)]
    if missing or len(proposal_decision_paths(ROOT)) != 3:
        errors = [f"ROLE_INCOMPLETE:{role}" for role in missing]
        if len(proposal_decision_paths(ROOT)) != 3:
            errors.append("PRE_AUDIT_DECISIONS_INCOMPLETE")
        print(json.dumps({"status": "FAIL", "errors": errors}))
        return 1
    bundle_result = build_all(ROOT, check=False, config_path=args.config)
    if bundle_result["errors"]:
        print(json.dumps({"status": "FAIL", "errors": bundle_result["errors"]}))
        return 1
    outcome = RoleOrchestrator(ROOT, config_path=args.config).execute(
        ROLE, allow_recovery=args.resume
    )
    errors = _check()
    audit_result = (
        read_json(formal_output_path(ROOT, ROLE))["result"]
        if is_formal_output_valid(ROOT, ROLE)
        else None
    )
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "audit_result": audit_result,
                "outcome": outcome.__dict__,
                "remaining_real_run_budget": RunBudget(ROOT).remaining(),
                "errors": errors,
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
