"""Completeness and anonymity checks for normalized role bundles."""

from __future__ import annotations

from typing import Any

from ..judge_runner import IDENTITY_MARKERS

REQUIRED_FILES = {
    "bundle_index.json",
    "policy_summary.json",
    "eligible_evidence.json",
    "excluded_evidence.json",
    "hard_gates.json",
    "findings.json",
    "test_evidence.json",
    "evidence_catalog.json",
    "role_task.json",
    "output_schema.json",
}


def completeness_errors(files: dict[str, Any], all_blocker_ids: set[str]) -> list[str]:
    errors: list[str] = []
    missing_files = sorted(REQUIRED_FILES - files.keys())
    errors.extend(f"BUNDLE_FILE_MISSING:{name}" for name in missing_files)
    selected = {
        item["finding_id"]
        for item in files.get("findings.json", {}).get("findings", [])
        if item.get("severity") == "BLOCKER"
    }
    for finding_id in sorted(all_blocker_ids - selected):
        errors.append(f"BLOCKER_MISSING:{finding_id}")
    excluded = files.get("excluded_evidence.json", {})
    if excluded.get("recovery_policy") != "GAP_EVIDENCE_ONLY":
        errors.append("RECOVERY_POLICY_MISSING")
    recovery = excluded.get("recovery_records", [])
    if len(recovery) != 5 or any(item.get("ranking_eligible") is not False for item in recovery):
        errors.append("RECOVERY_EXCLUSION_MISSING")
    hard_gates = files.get("hard_gates.json", {}).get("hard_gates", [])
    if len(hard_gates) != 6:
        errors.append("HARD_GATES_INCOMPLETE")
    text = str(files).lower()
    for marker in IDENTITY_MARKERS:
        if marker.lower() in text:
            errors.append(f"IDENTITY_LEAK:{marker}")
    if "benchmark-vault" in text or "historical answer" in text:
        errors.append("ANSWER_REFERENCE_FORBIDDEN")
    return errors
