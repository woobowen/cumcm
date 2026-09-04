"""Candidate-neutral grader boundary; never returns oracle bodies or hidden seeds."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from experiments.shadow_prototypes.common.interface import ShadowRunResult, sha256_json

SANITIZED_FAILURES = frozenset(
    {
        "NONE",
        "FALSE_ACCEPT",
        "FALSE_BLOCK",
        "ABSTENTION",
        "TERMINAL_FAILURE",
        "RESULT_HASH_MISMATCH",
        "INPUT_MUTATION",
    }
)


def grade_result(
    result: ShadowRunResult,
    oracle: Mapping[str, Any],
    *,
    input_unchanged: bool,
) -> dict[str, Any]:
    """Grade a terminal result and emit only aggregate-safe classification fields."""
    expected = str(oracle["expected_outcome"])
    if not input_unchanged:
        failure = "INPUT_MUTATION"
    elif result.result_hash != sha256_json(result.hash_body()):
        failure = "RESULT_HASH_MISMATCH"
    elif result.terminal_status != "COMPLETED":
        failure = "TERMINAL_FAILURE"
    elif result.decision.outcome == "ABSTAIN":
        failure = "ABSTENTION"
    elif expected == "BLOCK" and result.decision.outcome != "BLOCK":
        failure = "FALSE_ACCEPT"
    elif expected == "PASS" and result.decision.outcome != "PASS":
        failure = "FALSE_BLOCK"
    else:
        failure = "NONE"
    if failure not in SANITIZED_FAILURES:
        raise AssertionError("UNSANITIZED_FAILURE_CLASS")
    body = {
        "schema_version": "1.0.0",
        "run_id": result.run_id,
        "architecture_id": result.architecture_id,
        "case_id": result.case_id,
        "result_hash": result.result_hash,
        "passed": failure == "NONE",
        "sanitized_failure_class": failure,
    }
    return {**body, "grade_hash": sha256_json(body)}


__all__ = ["SANITIZED_FAILURES", "grade_result"]
