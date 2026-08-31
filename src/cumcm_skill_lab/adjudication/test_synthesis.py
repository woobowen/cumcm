"""Translate serious findings into deterministic test requests and evidence."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime


def synthesize_test(finding: dict) -> dict:
    testable = finding.get("testability") == "TESTABLE"
    return {
        "test_id": f"TEST-{finding['finding_id']}",
        "finding_id": finding["finding_id"],
        "target": finding["target"],
        "inputs": list(finding.get("evidence_refs", [])),
        "oracle": f"Deterministically falsify or confirm: {finding['statement']}",
        "command_or_procedure": f"registered:{finding['target']}",
        "expected_result": "Oracle returns true for compliant implementation.",
        "pass_condition": "Registered oracle returns true and evidence is hashed.",
        "fail_condition": "Registered oracle returns false, errors, or times out.",
        "artifacts": [],
        "required_evidence": ["oracle_result", "artifact_hashes"],
        "timeout": 60,
        "reproducibility": "DETERMINISTIC",
        "status": "PENDING" if testable else "NON_TESTABLE_CLAIM",
    }


def synthesize_all(findings: list[dict]) -> list[dict]:
    return [
        synthesize_test(item) for item in findings if item.get("severity") in {"BLOCKER", "ERROR"}
    ]


def execute_registered(
    request: dict, registry: dict[str, Callable[[dict], bool]], inputs: dict | None = None
) -> dict:
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    target = request["target"]
    if request["status"] == "NON_TESTABLE_CLAIM" or target not in registry:
        status, result, observed = "ERROR", False, "No registered deterministic oracle."
    else:
        try:
            result = bool(registry[target](inputs or {}))
            status = "PASSED" if result else "FAILED"
            observed = f"Registered oracle returned {result}."
        except Exception as exc:  # boundary intentionally records executor failures
            status, result, observed = "ERROR", False, f"{type(exc).__name__}:{exc}"
    return {
        "test_id": request["test_id"],
        "finding_id": request["finding_id"],
        "status": status,
        "observed_result": observed,
        "oracle_result": result,
        "command_or_procedure": request["command_or_procedure"],
        "artifact_hashes": {},
        "started_at": now,
        "completed_at": now,
    }
