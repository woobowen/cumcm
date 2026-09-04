"""Versioned untrusted-input transport for the Competition RC1 candidate revisions."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .interface import deep_freeze


def _boundary_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _boundary_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_boundary_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_boundary_value(item) for item in value), key=repr)
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            marker = "NaN"
        elif value > 0:
            marker = "+Infinity"
        else:
            marker = "-Infinity"
        return {"__invalid_nonfinite_number__": marker}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return {"__invalid_type__": type(value).__name__}


def boundary_json(value: Any) -> bytes:
    """Snapshot malformed input deterministically without legitimizing its values."""
    return json.dumps(
        _boundary_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_boundary_json(value: Any) -> str:
    return hashlib.sha256(boundary_json(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class R1CaseInput:
    """Immutable RC1 input that can carry invalid JSON numbers to a fail-closed gate."""

    case_id: str
    component_id: str
    payload: Mapping[str, Any]
    input_hash: str
    case_class: str = "unspecified"
    source_commitment_hash: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.payload, Mapping):
            raise ValueError("R1_CASE_PAYLOAD_NOT_MAPPING")
        object.__setattr__(self, "payload", deep_freeze(dict(self.payload)))
        if self.input_hash != sha256_boundary_json(self.payload):
            raise ValueError("R1_CASE_INPUT_HASH_MISMATCH")


__all__ = ["R1CaseInput", "boundary_json", "sha256_boundary_json"]
