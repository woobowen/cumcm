"""Strict fresh-session primary eligibility without correctness selection bias."""

from __future__ import annotations

from typing import Any

from .models import hashed_body


def evaluate_primary_eligibility(
    *,
    attempt: dict[str, Any],
    oracle: dict[str, Any],
    process: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    checks = {
        "fresh_session": attempt["fresh_session"] is True,
        "not_resumed": attempt["resume_used"] is False,
        "not_parser_recovered": attempt["parser_recovery_used"] is False,
        "schema_valid": attempt["schema_valid"] is True,
        "legal_exit": attempt["exit_code"] == 0,
        "completion_complete": attempt["completion_status"] == "COMPLETED",
        "task_input_hash_match": attempt["task_input_hash"] == expected["task_input_hash"],
        "fixture_hash_match": attempt["fixture_hash"] == expected["fixture_hash"],
        "package_hash_match": attempt["package_hash"] == expected["package_hash"],
        "prompt_hash_match": attempt["prompt_hash"] == expected["prompt_hash"],
        "cohort_match": attempt["cohort_hash"] == expected["cohort_hash"],
        "model_match": attempt["model"] == expected["model"],
        "reasoning_match": attempt["reasoning_setting"] == expected["reasoning_setting"],
        "sandbox_match": attempt["sandbox"] == expected["sandbox"],
        "transport_profile_match": attempt["transport_profile"] == expected["transport_profile"],
        "policy_hash_match": attempt["policy_hash"] == expected["policy_hash"],
        "schema_hash_match": attempt["schema_hash"] == expected["schema_hash"],
        "oracle_hash_match": attempt["oracle_hash"] == expected["oracle_hash"],
        "scorer_hash_match": attempt["scorer_hash"] == expected["scorer_hash"],
        "runner_hash_match": attempt["runner_hash"] == expected["runner_hash"],
        "no_hard_failure": not attempt["hard_failures"],
        "network_clear": "NETWORK_POLICY_VIOLATION" not in attempt["hard_failures"],
        "mcp_clear": "MCP_POLICY_VIOLATION" not in attempt["hard_failures"],
        "identity_clear": "IDENTITY_LEAK" not in attempt["hard_failures"],
        "answer_contamination_clear": "ANSWER_CONTAMINATION" not in attempt["hard_failures"],
        "input_unchanged": attempt["input_mutated"] is False,
        "result_present": bool(attempt["result_hashes"].get("observation")),
        "oracle_executed": oracle["executed"] is True,
        "process_verified": process["passed"] is True,
    }
    exclusions = sorted(key.upper() for key, passed in checks.items() if not passed)
    eligible = not exclusions
    body = {
        "schema_version": "1.0.0",
        "attempt_id": attempt["attempt_id"],
        "cohort_id": attempt["cohort_id"],
        "case_id": attempt["case_id"],
        "anonymous_arm_id": attempt["anonymous_arm_id"],
        "repeat_id": attempt["repeat_id"],
        "classification": "PRIMARY_ELIGIBLE" if eligible else "EXCLUDED",
        "primary_eligible": eligible,
        "checks": checks,
        "exclusion_reasons": exclusions,
        "oracle_outcome_used_for_selection": False,
        "oracle_status": oracle["status"],
        "recovery_evidence": False,
    }
    return hashed_body(body, "eligibility_hash")
