#!/usr/bin/env python3
"""Validate Phase 002B checkpoint, session-independence and run-budget records."""

import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.bundles.role_views import ROLE_ORDER
from cumcm_skill_lab.adjudication.models import read_json
from cumcm_skill_lab.adjudication.role_orchestrator import validate_role_ledger
from cumcm_skill_lab.adjudication.transport.checkpoints import CheckpointStore
from cumcm_skill_lab.adjudication.transport.runtime_budget import RunBudget

REQUIRED = {
    "role_id",
    "adapter",
    "thread_id",
    "turn_id",
    "attempt",
    "model",
    "reasoning_setting",
    "input_bundle_hash",
    "policy_hash",
    "evidence_hash",
    "output_schema_hash",
    "started_at",
    "last_event_at",
    "completion_status",
    "failure_class",
    "raw_event_hash",
    "output_hash",
    "resume_allowed",
    "supersedes",
    "notes",
}


def main() -> int:
    recovery_path = ROOT / "evals/results/phase-002b/recovery_manifest.json"
    recovery = read_json(recovery_path) if recovery_path.is_file() else None
    terminal_incomplete = bool(
        recovery and recovery.get("status") == "AUTOMATED_ADJUDICATION_INCOMPLETE"
    )
    errors = validate_role_ledger(ROOT, require_complete=not terminal_incomplete)
    store = CheckpointStore(ROOT)
    session_hashes: list[str] = []
    for role in ROLE_ORDER:
        checkpoint = store.load_checkpoint(role)
        if checkpoint is None:
            if not terminal_incomplete:
                errors.append(f"CHECKPOINT_MISSING:{role}")
            continue
        missing = sorted(REQUIRED - checkpoint.keys())
        if missing:
            errors.append(f"CHECKPOINT_FIELDS_MISSING:{role}:{','.join(missing)}")
        if checkpoint.get("role_id") != role:
            errors.append(f"CHECKPOINT_ROLE_MISMATCH:{role}")
        if not terminal_incomplete and checkpoint.get("completion_status") != "COMPLETED":
            errors.append(f"CHECKPOINT_INCOMPLETE:{role}")
        if checkpoint.get("model") != "gpt-5.6-sol":
            errors.append(f"CHECKPOINT_MODEL_MISMATCH:{role}")
        if checkpoint.get("reasoning_setting") != "medium":
            errors.append(f"CHECKPOINT_REASONING_MISMATCH:{role}")
        session_hash = checkpoint.get("thread_id")
        if isinstance(session_hash, str):
            session_hashes.append(session_hash)
        tracked_text = json.dumps(checkpoint)
        exact = store.load_exact_session(role)
        if exact and any(
            isinstance(value, str) and value and value in tracked_text for value in exact.values()
        ):
            errors.append(f"EXACT_SESSION_ID_TRACKED:{role}")
    if len(session_hashes) != len(set(session_hashes)):
        errors.append("ROLE_INDEPENDENCE_BROKEN:SHARED_THREAD")
    budget = RunBudget(ROOT).load()
    if len(budget["starts"]) > budget["phase002b_maximum_starts"]:
        errors.append("TOTAL_REAL_RUN_BUDGET_EXCEEDED")
    for role in ROLE_ORDER:
        if sum(item["role_id"] == role for item in budget["starts"]) > 2:
            errors.append(f"ROLE_REAL_RUN_BUDGET_EXCEEDED:{role}")
    if any(item.get("completion_status") == "STARTED" for item in budget["starts"]):
        errors.append("RUN_BUDGET_HAS_UNFINISHED_START")
    if (ROOT / "evals/results/phase-002b/role_ledger.json").is_file():
        read_json(ROOT / "evals/results/phase-002b/role_ledger.json")
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "roles": len(ROLE_ORDER),
                "phase002b_model_starts": len(budget["starts"]),
                "remaining": RunBudget(ROOT).remaining(),
                "terminal_incomplete": terminal_incomplete,
                "errors": errors,
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
