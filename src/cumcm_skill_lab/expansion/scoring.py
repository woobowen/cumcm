"""Coverage-only score adapter kept separate from correctness evidence."""

from __future__ import annotations

from typing import Any

from cumcm_skill_lab.eval.scoring import score_observation

from .models import hashed_body


def score_coverage(
    *, observation: dict[str, Any], rubric: dict[str, Any], run_binding: dict[str, Any]
) -> dict[str, Any]:
    historical = score_observation(observation, rubric, run_binding, recovered=False)
    body = {
        "schema_version": "1.0.0",
        "case_id": observation["case_id"],
        "anonymous_arm_id": observation["anonymous_arm_id"],
        "repeat_id": observation["run_index"],
        "status": historical["status"],
        "structured_coverage_score": historical["deterministic_score"],
        "dimensions": historical["dimensions"],
        "evidence": historical["evidence"],
        "missing": historical["missing"],
        "hard_failures": historical["hard_failures"],
        "proves_correctness": False,
        "semantic_review_used": False,
    }
    return hashed_body(body, "coverage_hash")
