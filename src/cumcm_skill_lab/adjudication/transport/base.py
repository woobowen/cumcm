"""Shared transport request, result and Adapter contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..models import read_json
from .checkpoints import CheckpointStore
from .event_sanitization import summarize_events
from .failure_classification import FailureInfo, classify_failure


class TransportStatus(StrEnum):
    PENDING = "PENDING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    TRANSPORT_FAILED_RESUMABLE = "TRANSPORT_FAILED_RESUMABLE"
    TRANSPORT_FAILED_NONRESUMABLE = "TRANSPORT_FAILED_NONRESUMABLE"
    AUTH_BLOCKED = "AUTH_BLOCKED"
    QUOTA_BLOCKED = "QUOTA_BLOCKED"
    SCHEMA_FAILED = "SCHEMA_FAILED"
    POLICY_FAILED = "POLICY_FAILED"
    EXHAUSTED = "EXHAUSTED"
    STALE = "STALE"


@dataclass(frozen=True)
class RoleRunRequest:
    role_id: str
    workspace: Path
    prompt: str
    output_schema_path: Path
    output_path: Path
    raw_event_path: Path
    checkpoint_store: CheckpointStore
    model: str
    reasoning_setting: str
    input_bundle_hash: str
    policy_hash: str
    evidence_hash: str
    attempt: int
    timeout_seconds: int = 1200
    supersedes: str | None = None


@dataclass
class TransportResult:
    role_id: str
    adapter: str
    status: TransportStatus
    attempt: int
    model: str
    reasoning_setting: str
    duration_seconds: float
    return_code: int | None
    output: dict[str, Any] | None = None
    session_id: str | None = None
    turn_id: str | None = None
    failure: FailureInfo | None = None
    raw_event_hash: str | None = None
    stderr_hash: str | None = None
    event_summary: dict[str, Any] = field(default_factory=dict)
    token_usage: dict[str, int] = field(default_factory=dict)


class TransportAdapter(ABC):
    name: str

    @abstractmethod
    def start_role(self, request: RoleRunRequest) -> TransportResult:
        """Start one new formal role turn."""

    @abstractmethod
    def resume_role(self, request: RoleRunRequest) -> TransportResult:
        """Continue the exact role session stored in its checkpoint."""

    @abstractmethod
    def poll_role(self) -> TransportResult | None:
        """Return the last observable role result."""

    @abstractmethod
    def cancel_role(self) -> None:
        """Interrupt the active role without deleting its checkpoint."""

    def load_checkpoint(self, request: RoleRunRequest) -> dict[str, Any] | None:
        return request.checkpoint_store.load_checkpoint(request.role_id)

    @staticmethod
    def validate_output(output_path: Path, schema_path: Path) -> dict[str, Any]:
        if not output_path.is_file():
            raise ValueError("OUTPUT_MISSING")
        output = read_json(output_path)
        Draft202012Validator(read_json(schema_path)).validate(output)
        return output

    @staticmethod
    def classify_failure(observable: str, *, session_id: str | None) -> FailureInfo:
        return classify_failure(observable, session_id=session_id)

    @staticmethod
    def summarize_events(raw_event_path: Path) -> dict[str, Any]:
        return summarize_events(raw_event_path)
