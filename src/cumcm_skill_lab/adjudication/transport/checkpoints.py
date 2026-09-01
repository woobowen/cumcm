"""Atomic tracked checkpoints with ignored exact-session recovery state."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from ..models import read_json
from .event_sanitization import hash_identifier

ROLE_SLUGS = {
    "CORRECTNESS_JUDGE": "correctness",
    "SCIENTIFIC_VALIDITY_JUDGE": "scientific_validity",
    "ENGINEERING_REPRODUCIBILITY_JUDGE": "engineering_reproducibility",
    "BLIND_DISSENT_JUDGE": "blind_dissent",
    "EVIDENCE_META_ADJUDICATOR": "meta",
    "DECISION_AUDITOR": "decision_audit",
}


class CheckpointStore:
    def __init__(self, root: Path):
        self.root = root
        self.tracked_root = root / "evals/results/phase-002b/role_checkpoints"
        self.secret_root = root / ".cache/adjudication-002b/session-secrets"

    def tracked_path(self, role_id: str) -> Path:
        return self.tracked_root / f"{ROLE_SLUGS[role_id]}.json"

    def secret_path(self, role_id: str) -> Path:
        return self.secret_root / f"{ROLE_SLUGS[role_id]}.json"

    def load_checkpoint(self, role_id: str) -> dict[str, Any] | None:
        path = self.tracked_path(role_id)
        return read_json(path) if path.is_file() else None

    def load_exact_session(self, role_id: str) -> dict[str, Any] | None:
        path = self.secret_path(role_id)
        return read_json(path) if path.is_file() else None

    def write(
        self,
        checkpoint: dict[str, Any],
        *,
        session_id: str | None,
        turn_id: str | None,
    ) -> None:
        required = {
            "role_id",
            "adapter",
            "attempt",
            "model",
            "reasoning_setting",
            "input_bundle_hash",
            "policy_hash",
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
        missing = sorted(required - checkpoint.keys())
        if missing:
            raise ValueError("CHECKPOINT_FIELDS_MISSING:" + ",".join(missing))
        tracked = dict(checkpoint)
        tracked["thread_id"] = hash_identifier(session_id)
        tracked["turn_id"] = hash_identifier(turn_id)
        tracked["identifier_representation"] = "SHA256_ONLY"
        _atomic_json_write(self.tracked_path(checkpoint["role_id"]), tracked)
        if session_id or turn_id:
            _atomic_json_write(
                self.secret_path(checkpoint["role_id"]),
                {"session_id": session_id, "turn_id": turn_id},
                mode=0o600,
            )


def _atomic_json_write(path: Path, value: Any, *, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
