#!/usr/bin/env python3
"""Run or verify the four strictly serial Phase 002B blind roles."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.bundles.builder import build_all
from cumcm_skill_lab.adjudication.bundles.role_views import ROLE_ORDER
from cumcm_skill_lab.adjudication.formal_outputs import is_formal_output_valid
from cumcm_skill_lab.adjudication.role_orchestrator import RoleOrchestrator
from cumcm_skill_lab.adjudication.transport.checkpoints import CheckpointStore
from cumcm_skill_lab.adjudication.transport.runtime_budget import RunBudget

BLIND_ROLES = ROLE_ORDER[:4]


def _check() -> list[str]:
    store = CheckpointStore(ROOT)
    errors: list[str] = []
    for role in BLIND_ROLES:
        checkpoint = store.load_checkpoint(role)
        if not checkpoint or checkpoint.get("completion_status") != "COMPLETED":
            errors.append(f"ROLE_INCOMPLETE:{role}")
        elif not is_formal_output_valid(ROOT, role):
            errors.append(f"ROLE_OUTPUT_INVALID:{role}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--config", default="adjudication/configs/phase-002b-v2.yaml")
    parser.add_argument("--transport", choices=("auto",), default="auto")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--remaining-real-run-budget", type=int, default=8)
    args = parser.parse_args()
    if args.remaining_real_run_budget != 8:
        raise SystemExit("PHASE002B_REAL_RUN_BUDGET_MUST_REMAIN_8")
    if args.check:
        errors = _check()
        print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}))
        return 0 if not errors else 1
    bundle_result = build_all(ROOT, check=True, config_path=args.config)
    if bundle_result["errors"]:
        print(json.dumps({"status": "FAIL", "errors": bundle_result["errors"]}))
        return 1
    orchestrator = RoleOrchestrator(ROOT, config_path=args.config)
    outcomes = []
    for role in BLIND_ROLES:
        outcome = orchestrator.execute(role, allow_recovery=args.resume)
        outcomes.append(outcome.__dict__)
        if outcome.completion_status != "COMPLETED":
            break
    errors = _check() if len(outcomes) == len(BLIND_ROLES) else ["BLIND_CHAIN_STOPPED"]
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "outcomes": outcomes,
                "remaining_real_run_budget": RunBudget(ROOT).remaining(),
                "errors": errors,
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
