"""Minimal immutable contract shared by the three frozen shadow architectures."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol

ALLOWED_OUTCOMES = frozenset({"PASS", "BLOCK", "ABSTAIN", "ERROR"})
PROHIBITED_FORMAL_OUTCOMES = frozenset({"FINAL", "FORMALLY_INTEGRATED"})


def deep_freeze(value: Any) -> Any:
    """Return an immutable, recursively detached representation of JSON-like input."""
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): deep_freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(deep_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(deep_freeze(item) for item in value)
    return value


def thaw(value: Any) -> Any:
    """Convert an immutable interface value to canonical JSON-compatible data."""
    if isinstance(value, Mapping):
        return {str(key): thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [thaw(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((thaw(item) for item in value), key=repr)
    if isinstance(value, Path):
        return value.as_posix()
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        thaw(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class ShadowCaseInput:
    case_id: str
    component_id: str
    payload: Mapping[str, Any]
    input_hash: str
    case_class: str = "unspecified"
    source_commitment_hash: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", deep_freeze(dict(self.payload)))
        if self.input_hash != sha256_json(self.payload):
            raise ValueError("SHADOW_CASE_INPUT_HASH_MISMATCH")


@dataclass(frozen=True, slots=True)
class ShadowContext:
    run_id: str
    architecture_id: str
    stage: str
    output_dir: Path
    timeout_seconds: int
    operation_budget: int
    enabled_components: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ShadowAction:
    action_id: str
    action_type: str
    actor: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", deep_freeze(dict(self.payload)))


@dataclass(frozen=True, slots=True)
class ShadowEvidence:
    evidence_id: str
    evidence_type: str
    run_id: str
    current: bool
    supports: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", deep_freeze(dict(self.payload)))


@dataclass(frozen=True, slots=True)
class ShadowDecision:
    outcome: str
    reason_codes: tuple[str, ...]
    component_results: Mapping[str, str] = field(default_factory=dict)
    proposed_actions: tuple[ShadowAction, ...] = ()

    def __post_init__(self) -> None:
        if self.outcome not in ALLOWED_OUTCOMES:
            raise ValueError(f"SHADOW_OUTCOME_NOT_ALLOWED:{self.outcome}")
        if self.outcome in PROHIBITED_FORMAL_OUTCOMES:
            raise ValueError(f"FORMAL_OUTCOME_PROHIBITED:{self.outcome}")
        object.__setattr__(self, "component_results", deep_freeze(dict(self.component_results)))


@dataclass(frozen=True, slots=True)
class ShadowRunResult:
    schema_version: str
    run_id: str
    architecture_id: str
    case_id: str
    input_hash: str
    decision: ShadowDecision
    evidence: tuple[ShadowEvidence, ...]
    artifact_hashes: Mapping[str, str]
    diagnostics: Mapping[str, Any]
    terminal_status: str
    result_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_hashes", deep_freeze(dict(self.artifact_hashes)))
        object.__setattr__(self, "diagnostics", deep_freeze(dict(self.diagnostics)))

    def hash_body(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "architecture_id": self.architecture_id,
            "case_id": self.case_id,
            "input_hash": self.input_hash,
            "decision": {
                "outcome": self.decision.outcome,
                "reason_codes": list(self.decision.reason_codes),
                "component_results": thaw(self.decision.component_results),
                "proposed_actions": [
                    {
                        "action_id": action.action_id,
                        "action_type": action.action_type,
                        "actor": action.actor,
                        "payload": thaw(action.payload),
                    }
                    for action in self.decision.proposed_actions
                ],
            },
            "evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "evidence_type": item.evidence_type,
                    "run_id": item.run_id,
                    "current": item.current,
                    "supports": list(item.supports),
                    "contradicts": list(item.contradicts),
                    "payload": thaw(item.payload),
                }
                for item in self.evidence
            ],
            "artifact_hashes": thaw(self.artifact_hashes),
            "diagnostics": thaw(self.diagnostics),
            "terminal_status": self.terminal_status,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.hash_body(), "result_hash": self.result_hash}


@dataclass(frozen=True, slots=True)
class ShadowMetricResult:
    metric_id: str
    architecture_id: str
    value: int | float | None
    denominator: int | None
    status: str
    evidence_hashes: tuple[str, ...]
    reason_codes: tuple[str, ...] = ()


class ShadowArchitecture(Protocol):
    architecture_id: str

    def evaluate_case(
        self,
        case_input: ShadowCaseInput,
        isolated_state: Mapping[str, Any],
        run_context: ShadowContext,
    ) -> ShadowRunResult: ...


def build_result(
    *,
    context: ShadowContext,
    case_input: ShadowCaseInput,
    decision: ShadowDecision,
    evidence: tuple[ShadowEvidence, ...] = (),
    artifact_hashes: Mapping[str, str] | None = None,
    diagnostics: Mapping[str, Any] | None = None,
    terminal_status: str = "COMPLETED",
) -> ShadowRunResult:
    provisional = ShadowRunResult(
        schema_version="1.0.0",
        run_id=context.run_id,
        architecture_id=context.architecture_id,
        case_id=case_input.case_id,
        input_hash=case_input.input_hash,
        decision=decision,
        evidence=evidence,
        artifact_hashes=artifact_hashes or {},
        diagnostics=diagnostics or {},
        terminal_status=terminal_status,
        result_hash="",
    )
    return ShadowRunResult(
        **{**provisional.hash_body(), "decision": decision, "evidence": evidence},
        result_hash=sha256_json(provisional.hash_body()),
    )


def verify_result_hash(result: ShadowRunResult) -> bool:
    return result.result_hash == sha256_json(result.hash_body())


__all__ = [
    "ShadowAction",
    "ShadowArchitecture",
    "ShadowCaseInput",
    "ShadowContext",
    "ShadowDecision",
    "ShadowEvidence",
    "ShadowMetricResult",
    "ShadowRunResult",
    "build_result",
    "canonical_json",
    "deep_freeze",
    "sha256_json",
    "thaw",
    "verify_result_hash",
]
