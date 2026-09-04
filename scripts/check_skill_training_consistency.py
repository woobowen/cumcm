#!/usr/bin/env python3
"""Check active Skill state and Development/Validation case isolation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "benchmarks/case_registry.yaml"
SKILL = REPO_ROOT / ".agents/skills/cumcm-modeling-evidence/SKILL.md"
STATE = REPO_ROOT / "state/project_state.json"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
CASE_EVIDENCE_ROOT = REPO_ROOT / "evals/results/phase-004a/CUMCM-2023-C-DEVELOPMENT-001"
DEVELOPMENT_EVIDENCE = CASE_EVIDENCE_ROOT / "rc2/development_regression_evidence.json"
STRESS_EVIDENCE = {
    "A": CASE_EVIDENCE_ROOT / "stress/stress_a_evidence.json",
    "B": CASE_EVIDENCE_ROOT / "stress/stress_b_evidence.json",
    "C": CASE_EVIDENCE_ROOT / "stress/stress_c_evidence.json",
}
REFERENCE_REVIEW = CASE_EVIDENCE_ROOT / "postmortem/reference_review.json"
GAP_ANALYSIS = CASE_EVIDENCE_ROOT / "postmortem/gap_analysis.json"
REQUIRED_REPORTS = tuple(
    REPO_ROOT / f"reports/phase004a_{name}.md"
    for name in (
        "first_run",
        "first_run_freeze",
        "postmortem",
        "generalizable_failures",
        "skill_changes",
        "rc2_regression",
        "stress_results",
        "timing_and_cost",
        "acceptance",
    )
)
EXPECTED_VERSION = "0.2.0-competition-rc3"
PHASE004A_VERSION = "0.2.0-competition-rc2"
ALLOWED_CASE_VERSIONS = {"0.2.0-competition-rc1", PHASE004A_VERSION}
REQUIRED_FIELDS = {
    "case_id",
    "set_type",
    "problem_source",
    "problem_hash",
    "data_hashes",
    "answer_access_status",
    "first_run_status",
    "skill_version",
    "skill_commit",
    "model",
    "reasoning",
    "start_time",
    "freeze_time",
    "unlock_time",
    "generalizable_failures",
    "problem_specific_findings",
}
SET_TYPES = {"DEVELOPMENT", "VALIDATION", "HELD_OUT", "STRESS"}
ANSWER_STATES = {"SEALED", "UNLOCKED_AFTER_FIRST_RUN", "PERMANENTLY_DEVELOPMENT"}
RUN_STATES = {"NOT_STARTED", "IN_PROGRESS", "FROZEN"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def run_scores(value: dict[str, Any]) -> dict[str, float]:
    runs = value.get("runs")
    if not isinstance(runs, list):
        return {}
    return {
        str(run.get("candidate_id")): float(run.get("validation_score"))
        for run in runs
        if isinstance(run, dict)
        and isinstance(run.get("candidate_id"), str)
        and isinstance(run.get("validation_score"), (int, float))
    }


def check() -> dict[str, Any]:
    errors: list[str] = []
    state = json.loads(STATE.read_text(encoding="utf-8"))
    skill_text = SKILL.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")
    registry = load_yaml(REGISTRY)
    if state.get("active_skill_version") != EXPECTED_VERSION:
        errors.append("PROJECT_STATE_SKILL_VERSION_MISMATCH")
    if state.get("skill_capability_status") != "COMPETITION_RC":
        errors.append("PROJECT_STATE_CAPABILITY_MISMATCH")
    if EXPECTED_VERSION not in skill_text:
        errors.append("FORMAL_SKILL_VERSION_MISMATCH")
    if EXPECTED_VERSION not in changelog:
        errors.append("CHANGELOG_VERSION_MISSING")
    skills = list((REPO_ROOT / ".agents/skills").glob("*/SKILL.md"))
    if len(skills) != 1 or skills[0].parent.name != "cumcm-modeling-evidence":
        errors.append("FORMAL_SKILL_COUNT_INVALID")
    declared_fields = registry.get("required_case_fields")
    if not isinstance(declared_fields, list) or set(declared_fields) != REQUIRED_FIELDS:
        errors.append("REGISTRY_FIELD_CONTRACT_INVALID")
    cases = registry.get("cases")
    if not isinstance(cases, list):
        errors.append("REGISTRY_CASES_INVALID")
        cases = []
    ids: list[str] = []
    for case in cases:
        if not isinstance(case, dict) or not set(case) >= REQUIRED_FIELDS:
            errors.append("CASE_REQUIRED_FIELDS_MISSING")
            continue
        case_id = case.get("case_id")
        ids.append(str(case_id))
        if case.get("set_type") not in SET_TYPES:
            errors.append(f"CASE_SET_TYPE_INVALID:{case_id}")
        if case.get("answer_access_status") not in ANSWER_STATES:
            errors.append(f"CASE_ANSWER_STATUS_INVALID:{case_id}")
        if case.get("first_run_status") not in RUN_STATES:
            errors.append(f"CASE_FIRST_RUN_STATUS_INVALID:{case_id}")
        if case.get("skill_version") not in ALLOWED_CASE_VERSIONS:
            errors.append(f"CASE_SKILL_VERSION_MISMATCH:{case_id}")
        if not GIT_SHA.fullmatch(str(case.get("skill_commit", ""))):
            errors.append(f"CASE_SKILL_COMMIT_INVALID:{case_id}")
        if not HEX64.fullmatch(str(case.get("problem_hash", ""))):
            errors.append(f"CASE_PROBLEM_HASH_INVALID:{case_id}")
        data_hashes = case.get("data_hashes")
        if not isinstance(data_hashes, dict) or any(
            not HEX64.fullmatch(str(value)) for value in data_hashes.values()
        ):
            errors.append(f"CASE_DATA_HASH_INVALID:{case_id}")
        if case.get("set_type") in {"VALIDATION", "HELD_OUT"} and (
            case.get("answer_access_status") != "SEALED" or case.get("unlock_time") is not None
        ):
            errors.append(f"VALIDATION_OR_HELD_OUT_POLLUTED:{case_id}")
        if case.get("answer_access_status") != "SEALED" and case.get("set_type") != "DEVELOPMENT":
            errors.append(f"UNSEALED_CASE_NOT_DEVELOPMENT:{case_id}")
        if case.get("first_run_status") == "FROZEN":
            evidence = case.get("first_run_evidence")
            if not isinstance(evidence, dict):
                errors.append(f"FIRST_RUN_EVIDENCE_MISSING:{case_id}")
            elif evidence.get("skill_commit") != case.get("skill_commit"):
                errors.append(f"FIRST_RUN_SKILL_COMMIT_MISMATCH:{case_id}")
            if not case.get("freeze_time"):
                errors.append(f"FIRST_RUN_FREEZE_TIME_MISSING:{case_id}")
        if not isinstance(case.get("generalizable_failures"), list) or not isinstance(
            case.get("problem_specific_findings"), list
        ):
            errors.append(f"CASE_FINDINGS_INVALID:{case_id}")
    if len(ids) != len(set(ids)):
        errors.append("CASE_ID_DUPLICATE")
    first_run_case = next(
        (
            case
            for case in cases
            if isinstance(case, dict) and case.get("case_id") == "CUMCM-2023-C-DEVELOPMENT-001"
        ),
        {},
    )
    freeze = first_run_case.get("first_run_freeze")
    if not isinstance(freeze, dict):
        errors.append("FIRST_RUN_FREEZE_RECORD_MISSING")
    else:
        freeze_path = freeze.get("path")
        path = REPO_ROOT / str(freeze_path)
        if (
            not isinstance(freeze_path, str)
            or not path.is_file()
            or not HEX64.fullmatch(str(freeze.get("sha256", "")))
            or sha256_file(path) != freeze.get("sha256")
        ):
            errors.append("FIRST_RUN_FREEZE_HASH_MISMATCH")

    evidence_paths = [
        DEVELOPMENT_EVIDENCE,
        *STRESS_EVIDENCE.values(),
        REFERENCE_REVIEW,
        GAP_ANALYSIS,
    ]
    if any(not path.is_file() for path in evidence_paths):
        errors.append("PHASE004A_EVIDENCE_MISSING")
    else:
        development = load_json(DEVELOPMENT_EVIDENCE)
        stress = {key: load_json(path) for key, path in STRESS_EVIDENCE.items()}
        if (
            development.get("final_state") != "READY_FOR_PAPER_HANDOFF"
            or development.get("skill_version") != PHASE004A_VERSION
            or development.get("answer_access_status") != "UNLOCKED_AFTER_FIRST_RUN"
            or len(development.get("runs", [])) != 3
            or any(run.get("exit_code") != 0 for run in development.get("runs", []))
        ):
            errors.append("DEVELOPMENT_REGRESSION_EVIDENCE_INVALID")
        development_scores = run_scores(development)
        for key, expected_variant in {
            "A": "STRESS_A_SCHEMA_ORDERING",
            "B": "STRESS_B_UNITS_TIME",
            "C": "STRESS_C_DEGRADED_INPUT",
        }.items():
            value = stress[key]
            metadata = value.get("variant_metadata")
            if (
                value.get("final_state") != "READY_FOR_PAPER_HANDOFF"
                or value.get("skill_version") != PHASE004A_VERSION
                or not isinstance(metadata, dict)
                or metadata.get("variant_id") != expected_variant
                or len(value.get("runs", [])) != 3
                or any(run.get("exit_code") != 0 for run in value.get("runs", []))
            ):
                errors.append(f"STRESS_{key}_EVIDENCE_INVALID")
        if (
            run_scores(stress["A"]) != development_scores
            or stress["A"].get("decision_hash") != development.get("decision_hash")
            or stress["A"].get("final_metrics") != development.get("final_metrics")
            or stress["A"].get("input_hashes") == development.get("input_hashes")
        ):
            errors.append("STRESS_A_ORDER_INVARIANCE_FAILED")
        stress_b_metadata = stress["B"].get("variant_metadata", {})
        if (
            run_scores(stress["B"]) != development_scores
            or stress["B"].get("final_metrics") != development.get("final_metrics")
            or stress_b_metadata.get("quantity_scale_to_kg") != 0.001
            or stress_b_metadata.get("date_shift_days") != 365
            or stress["B"].get("stale_probe", {}).get("status") != "STALE"
        ):
            errors.append("STRESS_B_UNIT_TIME_OR_STALE_FAILED")
        stress_c_quality = stress["C"].get("data_quality", {})
        if (
            stress_c_quality.get("loss_source_available") is not False
            or not isinstance(stress_c_quality.get("missing_loss_rows"), int)
            or stress_c_quality.get("missing_loss_rows", 0) <= 0
            or stress["C"].get("decision_hash") == development.get("decision_hash")
            or stress["C"].get("final_metrics") == development.get("final_metrics")
            or stress["C"].get("stale_probe", {}).get("status") != "STALE"
        ):
            errors.append("STRESS_C_DEGRADED_UNCERTAINTY_OR_STALE_FAILED")
        reference_review = load_json(REFERENCE_REVIEW)
        references = reference_review.get("references")
        if (
            reference_review.get("answer_access_status") != "UNLOCKED_AFTER_FIRST_RUN"
            or not isinstance(references, list)
            or not (1 <= len(references) <= 3)
            or any(item.get("source_domain") != "mcm.edu.cn" for item in references)
            or not str(reference_review.get("copy_policy_result", "")).startswith("PASS")
        ):
            errors.append("POST_UNLOCK_REFERENCE_BOUNDARY_INVALID")
        gap_analysis = load_json(GAP_ANALYSIS)
        gaps = gap_analysis.get("gaps")
        if (
            not isinstance(gaps, list)
            or not gaps
            or not any(
                gap.get("classification") == "GENERALIZABLE_SKILL_FAILURE"
                and str(gap.get("accepted_or_rejected", "")).startswith("ACCEPTED")
                for gap in gaps
                if isinstance(gap, dict)
            )
        ):
            errors.append("GENERALIZABLE_FAILURE_EVIDENCE_MISSING")
        registered_regression = first_run_case.get("rc2_development_regression", {})
        if (
            registered_regression.get("evidence_path")
            != str(DEVELOPMENT_EVIDENCE.relative_to(REPO_ROOT))
            or registered_regression.get("evidence_sha256") != sha256_file(DEVELOPMENT_EVIDENCE)
            or registered_regression.get("final_state") != "READY_FOR_PAPER_HANDOFF"
        ):
            errors.append("DEVELOPMENT_REGRESSION_REGISTRY_MISMATCH")
        registered_stress = first_run_case.get("stress_evidence")
        if not isinstance(registered_stress, dict):
            errors.append("STRESS_REGISTRY_MISSING")
        else:
            for key, path in STRESS_EVIDENCE.items():
                record = registered_stress.get(key, {})
                if (
                    record.get("path") != str(path.relative_to(REPO_ROOT))
                    or record.get("sha256") != sha256_file(path)
                    or record.get("status") != "PASS"
                ):
                    errors.append(f"STRESS_{key}_REGISTRY_MISMATCH")
    if any(
        not path.is_file() or not path.read_text(encoding="utf-8").strip()
        for path in REQUIRED_REPORTS
    ):
        errors.append("PHASE004A_REPORT_SET_INCOMPLETE")
    else:
        acceptance = (REPO_ROOT / "reports/phase004a_acceptance.md").read_text(encoding="utf-8")
        if (
            "DEVELOPMENT_EVAL_RC2_READY" not in acceptance
            or "PHASE-SKILL-DEVELOPMENT-EVAL-004-B" not in acceptance
            or "1808 passed, 1 skipped" not in acceptance
        ):
            errors.append("PHASE004A_ACCEPTANCE_REPORT_INCONSISTENT")

    problem_specific_tokens = (
        "2023 C",
        "蔬菜类商品",
        "附件1.xlsx",
        "附件2.xlsx",
        "附件3.xlsx",
        "附件4.xlsx",
        "销量(千克)",
        "销售日期",
        "2020 A",
        "炉温曲线",
        "2020A-炉温曲线.docx",
    )
    formal_skill_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPO_ROOT / ".agents/skills/cumcm-modeling-evidence").rglob("*")
        if path.is_file() and path.suffix in {".md", ".py", ".json"}
    )
    if any(token in formal_skill_text for token in problem_specific_tokens):
        errors.append("FORMAL_SKILL_PROBLEM_SPECIFIC_CONTENT")
    if state.get("technical_adjudication_status") == "DEVELOPMENT_EVAL_RC2_READY" and (
        state.get("next_phase_allowed") != "PHASE-SKILL-DEVELOPMENT-EVAL-004-B"
        or state.get("development_eval", {}).get("stress_statuses")
        != {"A": "PASS", "B": "PASS", "C": "PASS"}
    ):
        errors.append("RC2_READY_STATE_EVIDENCE_MISMATCH")
    if state.get("technical_adjudication_status") == "DEVELOPMENT_FIRST_RUN_IN_PROGRESS":
        active_case = next(
            (
                case
                for case in cases
                if isinstance(case, dict)
                and case.get("case_id") == state.get("development_eval", {}).get("case_id")
            ),
            {},
        )
        if (
            active_case.get("case_id") != "CUMCM-2020-A-DEVELOPMENT-002"
            or active_case.get("answer_access_status") != "SEALED"
            or active_case.get("first_run_status") != "IN_PROGRESS"
            or active_case.get("skill_version") != EXPECTED_VERSION
            or state.get("next_phase_allowed") is not None
        ):
            errors.append("PHASE004B_SEALED_START_STATE_MISMATCH")
    return {
        "ok": not errors,
        "error_count": len(errors),
        "errors": sorted(errors),
        "case_count": len(cases),
        "formal_skill_count": len(skills),
        "skill_version": EXPECTED_VERSION,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    result = check()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
