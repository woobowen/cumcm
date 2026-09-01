"""Case-specific deterministic oracle adapter for Phase 002D."""

from __future__ import annotations

from typing import Any

from cumcm_skill_lab.adjudication.oracle_scoring import oracle_correctness

from .models import hashed_body


def evaluate_oracle(
    *, case_id: str, observation: dict[str, Any], run_binding: dict[str, Any]
) -> dict[str, Any]:
    result = oracle_correctness(case_id, observation, run_binding)
    body = {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "anonymous_arm_id": run_binding["anonymous_arm_id"],
        "repeat_id": run_binding["run_index"],
        "role": result["role"],
        "checks": result["checks"],
        "status": "PASS" if result["passed"] else "FAIL",
        "executed": True,
        "is_coverage": False,
    }
    return hashed_body(body, "oracle_result_hash")
