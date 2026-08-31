"""Fail-closed selection between exact exec resume and App Server fallback."""

from __future__ import annotations

from dataclasses import dataclass

from .base import TransportStatus


@dataclass(frozen=True)
class AdapterAction:
    adapter: str
    action: str


def select_initial() -> AdapterAction:
    return AdapterAction("EXEC_RESUMABLE", "START")


def select_recovery(
    *,
    status: TransportStatus,
    exact_session_available: bool,
    attempts_used: int,
) -> AdapterAction:
    if attempts_used >= 2:
        return AdapterAction("NONE", "EXHAUSTED")
    if status == TransportStatus.TRANSPORT_FAILED_RESUMABLE and exact_session_available:
        return AdapterAction("EXEC_RESUMABLE", "RESUME")
    if status == TransportStatus.TRANSPORT_FAILED_NONRESUMABLE or not exact_session_available:
        return AdapterAction("APP_SERVER_RESUMABLE", "START")
    return AdapterAction("NONE", "STOP")
