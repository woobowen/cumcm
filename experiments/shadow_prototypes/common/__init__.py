"""Shared immutable interface and public-only fixtures for all shadow arms."""

from .interface import (
    ShadowAction,
    ShadowCaseInput,
    ShadowContext,
    ShadowDecision,
    ShadowEvidence,
    ShadowMetricResult,
    ShadowRunResult,
    canonical_json,
    deep_freeze,
    sha256_json,
)

__all__ = [
    "ShadowAction",
    "ShadowCaseInput",
    "ShadowContext",
    "ShadowDecision",
    "ShadowEvidence",
    "ShadowMetricResult",
    "ShadowRunResult",
    "canonical_json",
    "deep_freeze",
    "sha256_json",
]
