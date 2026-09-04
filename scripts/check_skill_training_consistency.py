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
PHASE004B_ROOT = REPO_ROOT / "evals/results/phase-004b/CUMCM-2020-A-DEVELOPMENT-002"
PHASE004B_FREEZE = PHASE004B_ROOT / "first_run/first_run_freeze.json"
PHASE004B_REGRESSION = PHASE004B_ROOT / "rc3/development_regression_evidence.json"
PHASE004B_RELEASE = PHASE004B_ROOT / "rc3/skill_release.json"
PHASE004B_CROSS_CASE = PHASE004B_ROOT / "cross_case_regression/cumcm_2023c_rc3.json"
PHASE004B_STRESS = {
    "A": PHASE004B_ROOT / "stress/stress_a_evidence.json",
    "B": PHASE004B_ROOT / "stress/stress_b_evidence.json",
    "C": PHASE004B_ROOT / "stress/stress_c_evidence.json",
}
PHASE004C_HANDOFF = REPO_ROOT / "evals/results/phase-004b/phase004c_validation_handoff.json"
PHASE004B_REPORTS = tuple(
    REPO_ROOT / f"reports/{name}.md"
    for name in (
        "phase004b_first_run",
        "phase004b_first_run_freeze",
        "phase004b_scientific_validity",
        "phase004b_postmortem",
        "phase004b_generalizable_failures",
        "phase004b_skill_changes",
        "phase004b_development_regression",
        "phase004b_cross_case_regression",
        "phase004b_stress_results",
        "phase004b_timing_and_cost",
        "phase004b_cross_case_generalization",
        "phase004c_validation_handoff",
        "phase004b_acceptance",
    )
)
EXPECTED_VERSION = "0.2.0-competition-rc3"
PHASE004A_VERSION = "0.2.0-competition-rc2"
ALLOWED_CASE_VERSIONS = {"0.2.0-competition-rc1", PHASE004A_VERSION, EXPECTED_VERSION}
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

    phase004b_case = next(
        (
            case
            for case in cases
            if isinstance(case, dict) and case.get("case_id") == "CUMCM-2020-A-DEVELOPMENT-002"
        ),
        {},
    )
    phase004b_paths = [
        PHASE004B_FREEZE,
        PHASE004B_REGRESSION,
        PHASE004B_RELEASE,
        PHASE004B_CROSS_CASE,
        *PHASE004B_STRESS.values(),
        PHASE004C_HANDOFF,
    ]
    if any(not path.is_file() for path in phase004b_paths):
        errors.append("PHASE004B_EVIDENCE_MISSING")
    else:
        freeze_004b = load_json(PHASE004B_FREEZE)
        regression_004b = load_json(PHASE004B_REGRESSION)
        release_004b = load_json(PHASE004B_RELEASE)
        cross_case_004b = load_json(PHASE004B_CROSS_CASE)
        stress_004b = {key: load_json(path) for key, path in PHASE004B_STRESS.items()}
        handoff_004c = load_json(PHASE004C_HANDOFF)
        freeze_record = phase004b_case.get("first_run_freeze", {})
        if (
            freeze_004b.get("answer_access_status") != "SEALED"
            or freeze_004b.get("first_run_status") != "FROZEN"
            or freeze_004b.get("blocked_reason_code") != "RC_RUN_SUCCESS_SET_INSUFFICIENT"
            or freeze_record.get("path") != str(PHASE004B_FREEZE.relative_to(REPO_ROOT))
            or freeze_record.get("sha256") != sha256_file(PHASE004B_FREEZE)
        ):
            errors.append("PHASE004B_FIRST_RUN_FREEZE_INVALID")
        release_skill = release_004b.get("formal_skill", {})
        if (
            release_004b.get("release_status") != "FROZEN_FOR_PHASE004C_VALIDATION"
            or release_skill.get("version") != EXPECTED_VERSION
            or not GIT_SHA.fullmatch(str(release_skill.get("commit", "")))
            or not GIT_SHA.fullmatch(str(release_skill.get("git_tree", "")))
            or release_004b.get("evidence_basis", {}).get("accepted_failure_id") != "GAP-004B-001"
        ):
            errors.append("PHASE004B_RC3_RELEASE_INVALID")
        if (
            regression_004b.get("evidence_class")
            != "DEVELOPMENT_REGRESSION_NOT_BLIND_NOT_VALIDATION"
            or regression_004b.get("final_state") != "READY_FOR_PAPER_HANDOFF"
            or regression_004b.get("skill", {}).get("version") != EXPECTED_VERSION
            or regression_004b.get("selected_model") != "PRIMARY_ASYMMETRIC_FIRST_ORDER"
            or len(regression_004b.get("runs", [])) != 6
            or any(run.get("exit_code") != 0 for run in regression_004b.get("runs", []))
            or regression_004b.get("handoff", {}).get("status") != "PASS"
        ):
            errors.append("PHASE004B_DEVELOPMENT_REGRESSION_INVALID")
        expected_stress_variants = {
            "A": "STRESS_A_UNITS_TIME",
            "B": "STRESS_B_EQUIVALENT_SEGMENTS",
            "C": "STRESS_C_DEGRADED_OBSERVATIONS",
        }
        for key, expected_variant in expected_stress_variants.items():
            value = stress_004b[key]
            if (
                value.get("variant_id") != expected_variant
                or value.get("result") != "PASS"
                or value.get("final_state") != "READY_FOR_PAPER_HANDOFF"
                or value.get("skill_version") != EXPECTED_VERSION
                or len(value.get("runs", [])) != 2
                or any(run.get("exit_code") != 0 for run in value.get("runs", []))
                or value.get("stale_probe", {}).get("status") != "STALE"
            ):
                errors.append(f"PHASE004B_STRESS_{key}_INVALID")
        if (
            stress_004b["A"].get("conversion_metadata", {}).get("time_to_seconds") != 60.0
            or stress_004b["A"].get("reference_comparison", {}).get("tolerance_pass") is not True
            or stress_004b["B"].get("process_representation", {}).get("coordinate_sort_required")
            is not True
            or stress_004b["B"].get("reference_comparison", {}).get("tolerance_pass") is not True
            or stress_004b["C"].get("uncertainty", {}).get("reported_parameter_significant_digits")
            != 4
            or stress_004b["C"].get("final_metrics", {}).get("validation_rmse_c")
            == regression_004b.get("final_metrics", {}).get("validation_rmse_c")
        ):
            errors.append("PHASE004B_STRESS_SEMANTICS_INVALID")
        if (
            cross_case_004b.get("result") != "PASS"
            or cross_case_004b.get("skill_version") != EXPECTED_VERSION
            or cross_case_004b.get("final_state") != "READY_FOR_PAPER_HANDOFF"
            or len(cross_case_004b.get("runs", [])) != 3
            or not all(
                cross_case_004b.get("executor_checks", {}).get(name) == "PASS"
                for name in (
                    "case_local_execute",
                    "capture_immutable",
                    "custom_code_manifest_binding",
                    "development_unlock_boundary",
                    "seal_run",
                )
            )
            or not all(cross_case_004b.get("comparison_to_rc2", {}).values())
            or cross_case_004b.get("stale_probe", {}).get("status") != "STALE"
            or cross_case_004b.get("handoff", {}).get("status") != "PASS"
        ):
            errors.append("PHASE004B_CROSS_CASE_REGRESSION_INVALID")
        registered_regression = phase004b_case.get("rc3_development_regression", {})
        if (
            registered_regression.get("evidence_path")
            != str(PHASE004B_REGRESSION.relative_to(REPO_ROOT))
            or registered_regression.get("evidence_sha256") != sha256_file(PHASE004B_REGRESSION)
            or phase004b_case.get("cross_case_regression_status") != "PASS"
        ):
            errors.append("PHASE004B_REGISTRY_EVIDENCE_MISMATCH")
        registered_stress = phase004b_case.get("stress_evidence", {})
        for key, path in PHASE004B_STRESS.items():
            record = registered_stress.get(key, {})
            if (
                record.get("path") != str(path.relative_to(REPO_ROOT))
                or record.get("sha256") != sha256_file(path)
                or record.get("status") != "PASS"
            ):
                errors.append(f"PHASE004B_STRESS_{key}_REGISTRY_MISMATCH")
        frozen_skill = handoff_004c.get("frozen_skill", {})
        if (
            handoff_004c.get("status") != "READY_FOR_VALIDATION_INTAKE_NOT_STARTED"
            or handoff_004c.get("validation_started") is not False
            or handoff_004c.get("answer_access_policy") != "SEALED_UNTIL_VALIDATION_RESULT_FREEZE"
            or handoff_004c.get("next_phase") != "PHASE-SKILL-VALIDATION-EVAL-004-C"
            or frozen_skill
            != release_skill
            | {
                "architecture": "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL",
                "capability": "COMPETITION_RC",
            }
            or len(handoff_004c.get("development_cases", [])) != 2
        ):
            errors.append("PHASE004C_VALIDATION_HANDOFF_INVALID")
    if any(
        not path.is_file() or not path.read_text(encoding="utf-8").strip()
        for path in PHASE004B_REPORTS
    ):
        errors.append("PHASE004B_REPORT_SET_INCOMPLETE")
    else:
        acceptance_004b = (REPO_ROOT / "reports/phase004b_acceptance.md").read_text(
            encoding="utf-8"
        )
        if (
            "DEVELOPMENT_EVAL_RC3_READY" not in acceptance_004b
            or "PHASE-SKILL-VALIDATION-EVAL-004-C" not in acceptance_004b
            or "1816 passed, 1 skipped" not in acceptance_004b
            or "FINAL_VERIFICATION_PENDING" in acceptance_004b
        ):
            errors.append("PHASE004B_ACCEPTANCE_REPORT_INCONSISTENT")

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
    if state.get("technical_adjudication_status") == "DEVELOPMENT_EVAL_RC3_READY" and (
        state.get("subphase") != "CUMCM-2020-A-DEVELOPMENT-RC3"
        or state.get("active_skill_version") != EXPECTED_VERSION
        or state.get("next_phase_allowed") != "PHASE-SKILL-VALIDATION-EVAL-004-C"
        or state.get("development_eval", {}).get("case_id") != "CUMCM-2020-A-DEVELOPMENT-002"
        or state.get("development_eval", {}).get("answer_access_status")
        != "UNLOCKED_AFTER_FIRST_RUN"
        or state.get("development_eval", {}).get("stress_statuses")
        != {"A": "PASS", "B": "PASS", "C": "PASS"}
        or state.get("third_party_integrated") is not False
    ):
        errors.append("PHASE004B_RC3_READY_STATE_EVIDENCE_MISMATCH")
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
