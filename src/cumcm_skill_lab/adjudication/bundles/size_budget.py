"""Fail-closed byte and estimated-token limits for role bundles."""

from __future__ import annotations

from math import ceil
from typing import Any

from ..models import canonical_json

MAX_NORMALIZED_BYTES = 128 * 1024
MAX_ESTIMATED_TOKENS = 30_000


def measure_bundle(files: dict[str, Any]) -> dict[str, int]:
    normalized_bytes = sum(len(canonical_json(value).encode()) for value in files.values())
    return {
        "normalized_bytes": normalized_bytes,
        "estimated_tokens": ceil(normalized_bytes / 4),
        "maximum_normalized_bytes": MAX_NORMALIZED_BYTES,
        "maximum_estimated_tokens": MAX_ESTIMATED_TOKENS,
    }


def enforce_size_budget(files: dict[str, Any]) -> dict[str, int]:
    measurement = measure_bundle(files)
    if measurement["normalized_bytes"] > MAX_NORMALIZED_BYTES:
        raise ValueError("BUNDLE_BYTE_BUDGET_EXCEEDED")
    if measurement["estimated_tokens"] > MAX_ESTIMATED_TOKENS:
        raise ValueError("BUNDLE_TOKEN_BUDGET_EXCEEDED")
    return measurement
