"""Append-only attempt records and deterministic checkpoint summaries."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from .models import RESULT_ROOT, hashed_body, read_json, write_json

ATTEMPT_ROOT = RESULT_ROOT / "attempts"
LEDGER_PATH = RESULT_ROOT / "attempt_ledger.json"
CHECKPOINT_PATH = RESULT_ROOT / "checkpoint.json"


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(handle)
    temporary_path = Path(temporary)
    try:
        write_json(temporary_path, value)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def attempt_path(root: Path, attempt_id: str) -> Path:
    return root / ATTEMPT_ROOT / f"{attempt_id}.json"


def load_attempts(root: Path) -> list[dict[str, Any]]:
    directory = root / ATTEMPT_ROOT
    if not directory.exists():
        return []
    attempts = [read_json(path) for path in directory.glob("*.json")]
    return sorted(attempts, key=lambda item: (item["start_time"], item["attempt_id"]))


def append_attempt(root: Path, attempt: dict[str, Any]) -> None:
    path = attempt_path(root, attempt["attempt_id"])
    if path.exists():
        raise RuntimeError(f"ATTEMPT_ALREADY_EXISTS:{attempt['attempt_id']}")
    atomic_write_json(path, attempt)


def build_ledger(root: Path) -> dict[str, Any]:
    attempts = load_attempts(root)
    body = {
        "schema_version": "1.0.0",
        "ledger_id": "PHASE-002D-ATTEMPT-LEDGER",
        "append_only": True,
        "attempt_ids": [attempt["attempt_id"] for attempt in attempts],
        "attempt_hashes": {attempt["attempt_id"]: attempt["attempt_hash"] for attempt in attempts},
        "attempt_count": len(attempts),
        "primary_eligible_count": sum(attempt["primary_eligible"] for attempt in attempts),
        "failed_count": sum(attempt["completion_status"] != "COMPLETED" for attempt in attempts),
    }
    return hashed_body(body, "ledger_hash")


def write_ledger(root: Path) -> dict[str, Any]:
    ledger = build_ledger(root)
    atomic_write_json(root / LEDGER_PATH, ledger)
    return ledger
