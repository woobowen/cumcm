"""Frozen metric projection over terminal, hash-bound shadow observations."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from .io import sha256_json


def score_observations(
    architecture_id: str,
    observations: Iterable[Mapping[str, Any]],
    *,
    static_counts: Mapping[str, int | float] | None = None,
) -> dict[str, Any]:
    rows = list(observations)
    failures = Counter(str(row.get("sanitized_failure_class", "TERMINAL_FAILURE")) for row in rows)
    complete = sum(bool(row.get("terminal", True)) for row in rows)
    passed = sum(bool(row.get("passed")) for row in rows)
    valid_rows = [row for row in rows if row.get("oracle_class") == "VALID_CONTROL"]
    targeted_rows = [row for row in rows if row.get("oracle_class") == "TARGET_VIOLATION"]
    values: dict[str, int | float | None] = {
        "critical_violation_count": failures["FALSE_ACCEPT"] + failures["INPUT_MUTATION"],
        "raw_input_mutation_count": failures["INPUT_MUTATION"],
        "targeted_detection_recall": (
            sum(bool(row.get("passed")) for row in targeted_rows) / len(targeted_rows)
            if targeted_rows
            else None
        ),
        "valid_control_false_block_rate": (
            sum(not bool(row.get("passed")) for row in valid_rows) / len(valid_rows)
            if valid_rows
            else None
        ),
        "completion_rate": complete / len(rows) if rows else None,
        "terminal_failure_rate": failures["TERMINAL_FAILURE"] / len(rows) if rows else None,
        "reproduction_success_rate": passed / len(rows) if rows else None,
    }
    values.update(static_counts or {})
    body = {
        "schema_version": "1.0.0",
        "architecture_id": architecture_id,
        "observation_count": len(rows),
        "metrics": values,
        "failure_counts": dict(sorted(failures.items())),
    }
    return {**body, "score_hash": sha256_json(body)}


__all__ = ["score_observations"]
