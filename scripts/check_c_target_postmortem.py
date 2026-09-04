#!/usr/bin/env python3
"""Validate the bounded C-batch reference review and cross-case RC4 admission decision."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REVIEWS_PATH = ROOT / "evals/results/phase-004c-c-batch/reference_reviews.json"
MATRIX_PATH = ROOT / "evals/results/phase-004c-c-batch/cross_case_failure_matrix.json"
UNLOCK_PATH = ROOT / "evals/results/phase-004c-c-batch/batch_reference_unlock.json"
CASES = {
    "CUMCM-2022-C-DEVELOPMENT-BATCH-001": "CUMCM-2022-C-BATCH-001",
    "CUMCM-2021-C-DEVELOPMENT-BATCH-002": "CUMCM-2021-C-BATCH-002",
    "CUMCM-2020-C-DEVELOPMENT-BATCH-003": "CUMCM-2020-C-BATCH-003",
}
REFERENCE_CLASSES = {
    "OFFICIAL_PROBLEM_PAGE",
    "OFFICIAL_COMMENTARY",
    "OFFICIAL_AWARD_DISPLAY",
    "PUBLISHED_FOLLOW_UP_ANALYSIS",
}
CLASSIFICATIONS = {
    "CROSS_CASE_REPEATED_FAILURE",
    "UNIVERSAL_HARD_FAILURE",
    "REQUIREMENT_DECOMPOSITION_FAILURE",
    "DATA_ENGINEERING_FAILURE",
    "SEARCH_FAILURE",
    "MODEL_PORTFOLIO_FAILURE",
    "MATHEMATICAL_MODELING_FAILURE",
    "STATISTICAL_VALIDITY_FAILURE",
    "OPTIMIZATION_FAILURE",
    "EXPERIMENT_DESIGN_FAILURE",
    "EXECUTION_EVIDENCE_FAILURE",
    "ROBUSTNESS_FAILURE",
    "CLAIM_EVIDENCE_FAILURE",
    "HANDOFF_FAILURE",
    "CONTEST_EFFICIENCY_FAILURE",
    "PROBLEM_SPECIFIC_INSIGHT",
    "REFERENCE_DISAGREEMENT",
    "MODEL_KNOWLEDGE_GAP",
}
FINDING_FIELDS = {
    "failure_id",
    "classification",
    "affected_cases",
    "first_run_evidence",
    "reference_evidence",
    "severity",
    "root_cause",
    "repeat_count",
    "universal_hard_failure",
    "generalizable",
    "proposed_skill_change",
    "risk_of_overfitting",
    "neutral_test",
    "expected_cross_case_benefit",
    "maintenance_cost",
    "decision",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_CHANGE_TERMS = (
    "2020",
    "2021",
    "2022",
    "玻璃",
    "供应商",
    "企业",
    "附件",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_reviews(
    reviews: dict[str, Any], unlock: dict[str, Any], *, root: Path | None = None
) -> list[str]:
    errors: list[str] = []
    policy = reviews.get("reference_policy", {})
    if (
        reviews.get("schema_version") != "1.0.0"
        or reviews.get("artifact_type") != "c_target_batch_reference_reviews"
        or reviews.get("batch_id") != "C-TARGET-BATCH-001"
        or policy.get("maximum_per_case") != 3
        or policy.get("actual_per_case") != 2
        or policy.get("reference_bodies_tracked") is not False
        or policy.get("reference_bodies_git_ignored") is not True
        or any(
            policy.get(field) is not False
            for field in (
                "mass_solution_collection",
                "code_copied",
                "parameters_copied",
                "formulas_copied",
                "passages_copied",
                "first_run_overwritten",
            )
        )
    ):
        errors.append("POSTMORTEM_REFERENCE_POLICY_INVALID")
    receipt = reviews.get("unlock_receipt", {})
    receipt_path = (ROOT if root is None else root) / UNLOCK_PATH.relative_to(ROOT)
    if receipt.get("sha256") != file_hash(receipt_path) or receipt.get("unlock_time") != unlock.get(
        "unlock_time"
    ):
        errors.append("POSTMORTEM_UNLOCK_BINDING_INVALID")
    try:
        unlock_time = datetime.fromisoformat(str(unlock.get("unlock_time")))
    except ValueError:
        unlock_time = datetime.max.astimezone()
        errors.append("POSTMORTEM_UNLOCK_TIME_INVALID")
    cases = reviews.get("cases")
    if not isinstance(cases, list) or {item.get("case_id") for item in cases} != set(CASES):
        errors.append("POSTMORTEM_CASE_SET_INVALID")
        cases = []
    for case in cases:
        case_id = case.get("case_id")
        references = case.get("references")
        if not isinstance(references, list) or not 1 <= len(references) <= 3:
            errors.append(f"POSTMORTEM_REFERENCE_COUNT_INVALID:{case_id}")
            continue
        if len(references) != policy.get("actual_per_case"):
            errors.append(f"POSTMORTEM_REFERENCE_COUNT_DRIFT:{case_id}")
        for reference in references:
            try:
                accessed = datetime.fromisoformat(str(reference.get("accessed_at")))
            except ValueError:
                accessed = datetime.min.astimezone()
            if (
                reference.get("class") not in REFERENCE_CLASSES
                or not str(reference.get("url", "")).startswith("https://")
                or not HEX64.fullmatch(str(reference.get("body_sha256", "")))
                or accessed <= unlock_time
                or not reference.get("evaluation_use")
            ):
                errors.append(f"POSTMORTEM_REFERENCE_RECORD_INVALID:{case_id}")
        freeze = case.get("first_run_freeze", {})
        freeze_path = ROOT / str(freeze.get("path", ""))
        if (
            not freeze_path.is_file()
            or file_hash(freeze_path) != freeze.get("sha256")
            or not case.get("gap_summary")
        ):
            errors.append(f"POSTMORTEM_CASE_BINDING_INVALID:{case_id}")
    return errors


def validate_matrix(matrix: dict[str, Any], reviews: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    findings = matrix.get("findings")
    decision = matrix.get("decision", {})
    if (
        matrix.get("schema_version") != "1.0.0"
        or matrix.get("artifact_type") != "c_target_cross_case_failure_matrix"
        or matrix.get("batch_id") != "C-TARGET-BATCH-001"
        or matrix.get("source_first_run_count") != 3
        or matrix.get("reference_policy_result") != "PASS_BOUNDED_TWO_PER_CASE_NO_COPY"
        or not isinstance(findings, list)
        or not findings
    ):
        errors.append("POSTMORTEM_MATRIX_HEADER_INVALID")
        findings = []
    ids: set[str] = set()
    authorized: list[str] = []
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != FINDING_FIELDS:
            errors.append("POSTMORTEM_FINDING_FIELDS_INVALID")
            continue
        finding_id = finding.get("failure_id")
        classes = finding.get("classification")
        affected = finding.get("affected_cases")
        if (
            not isinstance(finding_id, str)
            or finding_id in ids
            or not isinstance(classes, list)
            or not classes
            or not set(classes) <= CLASSIFICATIONS
            or not isinstance(affected, list)
            or not affected
            or not set(affected) <= set(CASES)
            or finding.get("repeat_count") != len(affected)
            or not finding.get("first_run_evidence")
            or not finding.get("reference_evidence")
        ):
            errors.append(f"POSTMORTEM_FINDING_IDENTITY_INVALID:{finding_id}")
            continue
        ids.add(finding_id)
        if finding.get("decision") == "AUTHORIZE_SINGLE_RC4_CHANGE_SET":
            authorized.append(finding_id)
            if (
                finding.get("generalizable") is not True
                or not (
                    finding.get("repeat_count", 0) >= 2 or finding.get("universal_hard_failure")
                )
                or str(finding.get("neutral_test", "")).startswith("NON_TESTABLE")
                or any(
                    term in str(finding.get(field, ""))
                    for field in ("proposed_skill_change", "neutral_test")
                    for term in FORBIDDEN_CHANGE_TERMS
                )
            ):
                errors.append(f"POSTMORTEM_RC4_ADMISSION_INVALID:{finding_id}")
    if (
        decision.get("status") != "RC4_CHANGE_AUTHORIZED"
        or decision.get("authorized_change_sets") != 1
        or decision.get("maximum_revision_cycles") != 2
        or decision.get("planned_revision_cycle") != 1
        or decision.get("authorized_failure_ids") != authorized
        or len(authorized) != 1
    ):
        errors.append("POSTMORTEM_RC4_DECISION_INVALID")
    if reviews.get("batch_id") != matrix.get("batch_id"):
        errors.append("POSTMORTEM_REFERENCE_MATRIX_BATCH_MISMATCH")
    return errors


def verify_reference_bodies(reviews: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    for case in reviews.get("cases", []):
        case_id = case.get("case_id")
        case_root = root / ".cache/official_inputs" / CASES.get(str(case_id), "") / "references"
        for index, reference in enumerate(case.get("references", [])):
            filename = "official_page.html" if index == 0 else "published_analysis.pdf"
            path = case_root / filename
            if not path.is_file() or file_hash(path) != reference.get("body_sha256"):
                errors.append(f"POSTMORTEM_REFERENCE_BODY_MISMATCH:{case_id}:{index}")
    tracked = subprocess.run(
        ["git", "ls-files", ".cache/official_inputs"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if tracked.returncode != 0 or tracked.stdout.strip():
        errors.append("POSTMORTEM_REFERENCE_BODY_TRACKING_INVALID")
    return errors


def evaluate(root: Path = ROOT, *, verify_bodies: bool = False) -> dict[str, Any]:
    reviews = load_json(root / REVIEWS_PATH.relative_to(ROOT))
    matrix = load_json(root / MATRIX_PATH.relative_to(ROOT))
    unlock = load_json(root / UNLOCK_PATH.relative_to(ROOT))
    errors = validate_reviews(reviews, unlock)
    errors.extend(validate_matrix(matrix, reviews))
    if verify_bodies:
        errors.extend(verify_reference_bodies(reviews, root))
    errors = sorted(set(errors))
    return {
        "batch_id": matrix.get("batch_id"),
        "case_count": len(reviews.get("cases", [])),
        "finding_count": len(matrix.get("findings", [])),
        "authorized_change_sets": matrix.get("decision", {}).get("authorized_change_sets"),
        "reference_bodies_verified": verify_bodies,
        "error_count": len(errors),
        "errors": errors,
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--verify-bodies", action="store_true")
    args = parser.parse_args()
    result = evaluate(verify_bodies=args.verify_bodies)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
