"""Persistent run-start accounting for the eight-run Phase 002B ceiling."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..models import read_json
from .checkpoints import _atomic_json_write

PREVIOUS_MODEL_STARTS = 4
PHASE002B_MAXIMUM_STARTS = 8
PER_ROLE_MAXIMUM_STARTS = 2


class RunBudget:
    def __init__(self, root: Path, path: Path | None = None):
        self.root = root
        self.path = path or root / "evals/results/phase-002b/transport_diagnostics/run_budget.json"

    def load(self) -> dict[str, Any]:
        if self.path.is_file():
            return read_json(self.path)
        return {
            "schema_version": "1.0.0",
            "previous_model_starts": PREVIOUS_MODEL_STARTS,
            "phase002b_maximum_starts": PHASE002B_MAXIMUM_STARTS,
            "per_role_maximum_starts": PER_ROLE_MAXIMUM_STARTS,
            "starts": [],
        }

    def assert_can_start(self, role_id: str) -> int:
        ledger = self.load()
        starts = ledger["starts"]
        role_count = sum(item["role_id"] == role_id for item in starts)
        if len(starts) >= PHASE002B_MAXIMUM_STARTS:
            raise RuntimeError("TOTAL_REAL_RUN_BUDGET_EXHAUSTED")
        if role_count >= PER_ROLE_MAXIMUM_STARTS:
            raise RuntimeError(f"ROLE_REAL_RUN_BUDGET_EXHAUSTED:{role_id}")
        return role_count + 1

    def record_start(self, role_id: str, adapter: str, start_kind: str) -> dict[str, Any]:
        attempt = self.assert_can_start(role_id)
        ledger = self.load()
        ledger["starts"].append(
            {
                "run_index": len(ledger["starts"]) + 1,
                "role_id": role_id,
                "adapter": adapter,
                "start_kind": start_kind,
                "attempt": attempt,
                "started_at": datetime.now(UTC).isoformat(),
                "completion_status": "STARTED",
            }
        )
        _atomic_json_write(self.path, ledger)
        return ledger["starts"][-1]

    def record_result(self, role_id: str, attempt: int, result: str) -> None:
        ledger = self.load()
        matches = [
            item
            for item in ledger["starts"]
            if item["role_id"] == role_id and item["attempt"] == attempt
        ]
        if len(matches) != 1:
            raise ValueError("RUN_BUDGET_RECORD_NOT_FOUND")
        matches[0]["completion_status"] = result
        matches[0]["completed_at"] = datetime.now(UTC).isoformat()
        _atomic_json_write(self.path, ledger)

    def remaining(self) -> int:
        return PHASE002B_MAXIMUM_STARTS - len(self.load()["starts"])
