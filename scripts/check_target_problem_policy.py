#!/usr/bin/env python3
"""Check the bounded C-target policy, allocation, batch, reservation, and live state."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "rules/target_problem_policy.yaml"
REGISTRY_PATH = ROOT / "benchmarks/case_registry.yaml"
STATE_PATH = ROOT / "state/project_state.json"
WORKFLOW_RULES_PATH = ROOT / "rules/workflow_rules.yaml"
FORMAL_SKILLS = ROOT / ".agents/skills"

BATCH_ID = "C-TARGET-BATCH-001"
PHASE = "PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C"
PLAN = "plans/active/PLAN-0004C-C-target-batch-generalization.md"
BRANCH = "feat/phase004c-c-target-batch-generalization"
RC3 = "0.2.0-competition-rc3"
RC4 = "0.2.0-competition-rc4"
RC3_COMMIT = "8a2a813ff34d8c2701c64ff9d959848e7b88c27c"
RC3_TREE = "a4551c8aa0b6b119823f6ce9df3f0f948339bb33"
ARCHITECTURE = "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
RESERVATION_ID = "CUMCM-2025-C-HELDOUT-RESERVED"
RESERVATION_PAGE_HASH = "83e2b2a88e81213252c4aa8212558a738a95f44d2d03de80e849b154d31a468f"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TARGET_CASE_FIELDS = {
    "target_problem_type",
    "evidence_role",
    "independent_problem",
    "batch_id",
    "batch_position",
    "answer_access_status",
    "first_run_freeze",
    "reference_unlock",
    "formal_skill_version",
    "formal_skill_commit",
    "contamination_status",
    "generalization_axis",
}
BATCH_CASE_IDS = {
    "CUMCM-2022-C-DEVELOPMENT-BATCH-001",
    "CUMCM-2021-C-DEVELOPMENT-BATCH-002",
    "CUMCM-2020-C-DEVELOPMENT-BATCH-003",
}
RESERVATION_FORBIDDEN_FIELDS = {
    "official_title",
    "title",
    "archive_url",
    "archive_hash",
    "official_archive_filename",
    "problem_source",
    "problem_hash",
    "data_hashes",
    "skill_version",
    "skill_commit",
    "start_time",
    "freeze_time",
    "unlock_time",
}


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _development_allocation(cases: list[dict[str, Any]]) -> tuple[int, int, float]:
    independent = [
        item
        for item in cases
        if item.get("set_type") == "DEVELOPMENT" and item.get("independent_problem") is True
    ]
    c_count = sum(item.get("target_problem_type") == "C" for item in independent)
    share = c_count / len(independent) if independent else 0.0
    return c_count, len(independent), share


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    policy = _yaml(root / POLICY_PATH.relative_to(ROOT))
    registry = _yaml(root / REGISTRY_PATH.relative_to(ROOT))
    state = _json(root / STATE_PATH.relative_to(ROOT))
    workflow_rules = _yaml(root / WORKFLOW_RULES_PATH.relative_to(ROOT))
    cases = [item for item in registry.get("cases", []) if isinstance(item, dict)]
    planned = [item for item in registry.get("planned_cases", []) if isinstance(item, dict)]

    expected_policy = {
        "primary_target": "C",
        "minimum_independent_c_share": 0.80,
        "validation_target": "C",
        "held_out_target": "C",
        "final_simulation_target": "C",
        "a_problem_role": "AUXILIARY_TRANSFER_ONLY",
        "b_problem_role": "EXCLUDED_BY_DEFAULT",
        "stress_counts_as_independent": False,
        "same_case_regression_counts_as_independent": False,
        "answer_sealing_required": True,
        "batch_skill_freeze_required": True,
        "post_result_same_case_validation_rerun": "PROHIBITED",
    }
    for field, expected in expected_policy.items():
        if policy.get(field) != expected:
            errors.append(f"TARGET_POLICY_FIELD_MISMATCH:{field}")
    if policy.get("decision_id") != "DECISION-C-TARGET-TRAINING-POLICY-004C":
        errors.append("TARGET_POLICY_DECISION_ID_MISMATCH")

    batch_policy = policy.get("batch", {})
    if not isinstance(batch_policy, dict) or (
        batch_policy.get("batch_id") != BATCH_ID
        or batch_policy.get("formal_skill_version") != RC3
        or batch_policy.get("formal_skill_commit") != RC3_COMMIT
        or batch_policy.get("formal_skill_tree") != RC3_TREE
        or batch_policy.get("batch_skill_frozen") is not True
        or batch_policy.get("batch_reference_unlocked") is not False
        or batch_policy.get("case_count") != 3
        or batch_policy.get("problem_type") != "C"
        or batch_policy.get("all_cases_before_unlock") is not True
    ):
        errors.append("TARGET_POLICY_BATCH_CONTRACT_INVALID")

    declared = registry.get("target_case_fields")
    if not isinstance(declared, list) or set(declared) != TARGET_CASE_FIELDS:
        errors.append("TARGET_REGISTRY_FIELD_CONTRACT_INVALID")
    for case in cases:
        if not TARGET_CASE_FIELDS.issubset(case):
            errors.append(f"TARGET_CASE_FIELDS_MISSING:{case.get('case_id')}")
        if case.get("formal_skill_version") != case.get("skill_version"):
            errors.append(f"TARGET_CASE_SKILL_VERSION_ALIAS_DRIFT:{case.get('case_id')}")
        if case.get("formal_skill_commit") != case.get("skill_commit"):
            errors.append(f"TARGET_CASE_SKILL_COMMIT_ALIAS_DRIFT:{case.get('case_id')}")
        if not isinstance(case.get("generalization_axis"), list) or not case.get(
            "generalization_axis"
        ):
            errors.append(f"TARGET_CASE_AXIS_INVALID:{case.get('case_id')}")

    batch_records_by_id: dict[str, dict[str, Any]] = {}
    for item in [*planned, *cases]:
        if item.get("batch_id") == BATCH_ID:
            batch_records_by_id[str(item.get("case_id"))] = item
    batch_records = list(batch_records_by_id.values())
    if set(batch_records_by_id) != BATCH_CASE_IDS:
        errors.append("TARGET_BATCH_CASE_SET_INVALID")
    if {item.get("batch_position") for item in batch_records} != {1, 2, 3}:
        errors.append("TARGET_BATCH_POSITION_SET_INVALID")
    for item in batch_records:
        case_id = item.get("case_id")
        unlocked = state.get("batch_reference_unlocked") is True
        expected_answer = "UNLOCKED_AFTER_FIRST_RUN" if unlocked else "SEALED"
        expected_reference = "UNLOCKED_AFTER_ALL_FIRST_RUN_FREEZES" if unlocked else "LOCKED"
        if (
            item.get("set_type") != "DEVELOPMENT"
            or item.get("target_problem_type") != "C"
            or item.get("evidence_role") != "DEVELOPMENT_BATCH"
            or item.get("independent_problem") is not True
            or item.get("answer_access_status") != expected_answer
            or item.get("reference_unlock") != expected_reference
            or item.get("formal_skill_version") != RC3
            or item.get("formal_skill_commit") != RC3_COMMIT
            or item.get("model_prior_status") != "MODEL_PRIOR_EXPOSURE_UNVERIFIABLE"
            or not isinstance(item.get("generalization_axis"), list)
            or not item.get("generalization_axis")
        ):
            errors.append(f"TARGET_BATCH_CASE_CONTRACT_INVALID:{case_id}")
        if item in planned and item.get("first_run_freeze") is not None:
            errors.append(f"TARGET_PLANNED_CASE_FREEZE_NOT_NULL:{case_id}")
        for hash_field in ("official_page_url_sha256", "official_archive_url_sha256"):
            if not HEX64.fullmatch(str(item.get(hash_field, ""))):
                errors.append(f"TARGET_BATCH_SOURCE_HASH_INVALID:{case_id}:{hash_field}")
        if item in cases:
            extracted = item.get("extracted_c_files")
            input_registration = item.get("input_registration")
            if (
                item.get("registration_status") != "INPUT_REGISTERED"
                or item.get("first_run_status") not in {"IN_PROGRESS", "FROZEN"}
                or item.get("strict_first_run_eligibility") != "ELIGIBLE_MODEL_PRIOR_UNVERIFIABLE"
                or item.get("no_solution_exposure_result")
                != "PASS_NO_SOLUTION_OR_REFERENCE_ACCESSED"
                or not HEX64.fullmatch(str(item.get("official_package_sha256", "")))
                or not HEX64.fullmatch(str(item.get("problem_hash", "")))
                or not isinstance(item.get("data_hashes"), dict)
                or not item.get("data_hashes")
                or not isinstance(extracted, list)
                or not extracted
                or not isinstance(input_registration, dict)
                or input_registration.get("path")
                != "evals/results/phase-004c-c-batch/input_registration.json"
                or not HEX64.fullmatch(str(input_registration.get("sha256", "")))
            ):
                errors.append(f"TARGET_BATCH_REGISTERED_INPUT_INVALID:{case_id}")

    allocation_by_id = {
        str(item.get("case_id")): item
        for item in [*cases, *planned]
        if item.get("set_type") == "DEVELOPMENT"
    }
    c_allocated, allocated, planned_share = _development_allocation(list(allocation_by_id.values()))
    minimum = policy.get("minimum_independent_c_share")
    if not isinstance(minimum, (int, float)) or planned_share + 1e-12 < float(minimum):
        errors.append("TARGET_INDEPENDENT_C_ALLOCATION_SHARE_TOO_LOW")

    realized = [
        item
        for item in cases
        if item.get("first_run_status") == "FROZEN"
        and item.get("independent_problem") is True
        and item.get("set_type") == "DEVELOPMENT"
    ]
    c_realized, realized_count, realized_share = _development_allocation(realized)

    if any(
        item.get("target_problem_type") == "A"
        and item.get("evidence_role") != "AUXILIARY_TRANSFER_ONLY"
        for item in [*cases, *planned]
    ):
        errors.append("TARGET_A_PROBLEM_ROLE_INVALID")
    if any(item.get("target_problem_type") == "B" for item in [*cases, *planned]):
        errors.append("TARGET_B_PROBLEM_NOT_EXCLUDED")

    reservations = [
        item for item in registry.get("held_out_reservations", []) if isinstance(item, dict)
    ]
    reservation = next(
        (item for item in reservations if item.get("reservation_id") == RESERVATION_ID), {}
    )
    if (
        len(reservations) != 1
        or reservation.get("set_type") != "HELD_OUT"
        or reservation.get("target_problem_type") != "C"
        or reservation.get("status") != "SEALED_NOT_ACCESSED"
        or reservation.get("official_annual_page_url_sha256") != RESERVATION_PAGE_HASH
        or any(
            reservation.get(field) is not False
            for field in (
                "archive_accessed",
                "title_accessed",
                "problem_accessed",
                "attachments_accessed",
                "references_accessed",
                "answer_accessed",
            )
        )
    ):
        errors.append("TARGET_HELD_OUT_RESERVATION_INVALID")
    forbidden_present = sorted(RESERVATION_FORBIDDEN_FIELDS.intersection(reservation))
    if forbidden_present:
        errors.append(f"TARGET_HELD_OUT_FORBIDDEN_FIELD:{forbidden_present[0]}")

    postmortem = state.get("technical_adjudication_status") == (
        "C_TARGET_BATCH_POSTMORTEM_IN_PROGRESS"
    )
    expected_state = {
        "phase": PHASE,
        "subphase": (
            "C-TARGET-UNIFIED-REFERENCE-REVIEW-AND-POSTMORTEM"
            if postmortem
            else "C-TARGET-STRATEGY-MIGRATION-AND-BATCH-FIRST-RUNS"
        ),
        "technical_adjudication_status": (
            "C_TARGET_BATCH_POSTMORTEM_IN_PROGRESS" if postmortem else "C_TARGET_BATCH_IN_PROGRESS"
        ),
        "current_plan": PLAN,
        "current_branch": BRANCH,
        "active_skill_version": RC3,
        "primary_target_problem_type": "C",
        "current_batch_id": BATCH_ID,
        "batch_skill_frozen": True,
        "batch_reference_unlocked": postmortem,
        "next_phase_allowed": None,
        "third_party_integrated": False,
        "skill_capability_status": "COMPETITION_RC",
        "selected_architecture": ARCHITECTURE,
    }
    for field, expected in expected_state.items():
        if state.get(field) != expected:
            errors.append(f"TARGET_STATE_FIELD_MISMATCH:{field}")

    plan_path = root / PLAN
    plan_text = plan_path.read_text(encoding="utf-8") if plan_path.is_file() else ""
    for token in (PHASE, BATCH_ID, RC3, "DECISION-C-TARGET-TRAINING-POLICY-004C"):
        if token not in plan_text:
            errors.append(f"TARGET_ACTIVE_PLAN_TOKEN_MISSING:{token}")
    if workflow_rules.get("git_delivery", {}).get("preferred_task_branch") != BRANCH:
        errors.append("TARGET_WORKFLOW_BRANCH_MISMATCH")

    skills = list((root / FORMAL_SKILLS.relative_to(ROOT)).glob("*/SKILL.md"))
    if len(skills) != 1 or skills[0].parent.name != "cumcm-modeling-evidence":
        errors.append("TARGET_FORMAL_SKILL_COUNT_INVALID")
    else:
        skill_text = skills[0].read_text(encoding="utf-8")
        candidate_path = root / "evals/results/phase-004c-c-batch/rc4/candidate_freeze.json"
        unified_path = (
            root / "evals/results/phase-004c-c-batch/rc4/unified_regression_evidence.json"
        )
        candidate = _json(candidate_path) if candidate_path.is_file() else {}
        unified = _json(unified_path) if unified_path.is_file() else {}
        staged_rc4 = (
            RC4 in skill_text
            and candidate.get("formal_release") is False
            and candidate.get("status")
            == "CANDIDATE_IMPLEMENTED_FOCUSED_TESTS_PASS_RELEASE_PENDING_UNIFIED_REGRESSION"
            and unified.get("release_gate") == "PASS_READY_TO_FREEZE_RC4"
        )
        if ARCHITECTURE not in skill_text or (RC3 not in skill_text and not staged_rc4):
            errors.append("TARGET_FORMAL_SKILL_IDENTITY_INVALID")

    return {
        "ok": not errors,
        "error_count": len(errors),
        "errors": sorted(set(errors)),
        "primary_target": policy.get("primary_target"),
        "planned_independent_c_count": c_allocated,
        "planned_independent_problem_count": allocated,
        "planned_independent_c_share": planned_share,
        "realized_independent_c_count": c_realized,
        "realized_independent_problem_count": realized_count,
        "realized_independent_c_share": realized_share,
        "realized_share_status": "REPORTED_NOT_USED_AS_PLANNED_ALLOCATION_GATE",
        "batch_case_count": len(batch_records),
        "formal_skill_count": len(skills),
        "held_out_reservation_count": len(reservations),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    result = evaluate()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
