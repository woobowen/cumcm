"""Derive the 27 R2A authorization preconditions from frozen repository evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    read_json,
    read_yaml,
    sha256_json,
)
from cumcm_skill_lab.historical_compat import (
    competition_rc_successor,
    git_repository_file_hashes,
    historical_json_if_successor,
)
from cumcm_skill_lab.specification.implementation_embargo import verify_embargo
from cumcm_skill_lab.specification.vault_manifest import check_benchmark_vault

from .adversarial_closure import CLOSURE_PATH as R2A_CLOSURE_PATH
from .evidence_freeze import FORMAL_SKILL_ROOT, verify_input_freeze
from .models import FREEZE_PATH, RESULT_ROOT, repository_file_hashes, tree_hash
from .scope import ACCEPTED_SCOPE, SCOPE_PATH, validate_scope_value

PRECONDITIONS_PATH = RESULT_ROOT / "authorization_preconditions.json"
PRECONDITIONS_SCHEMA_PATH = Path("contracts/authorization_precondition.schema.json")
CREATED_AT = "2026-09-03T04:00:00+08:00"
R2_ROOT = Path("evals/results/phase-002d-r2")
DECISION_PATHS = {
    "R2A-PRE-01": R2_ROOT / "automated_decisions/component_specification_freeze.json",
    "R2A-PRE-02": R2_ROOT / "automated_decisions/interaction_contract.json",
    "R2A-PRE-03": R2_ROOT / "automated_decisions/architecture_candidate_set.json",
    "R2A-PRE-04": R2_ROOT / "automated_decisions/prospective_benchmark_freeze.json",
    "R2A-PRE-05": R2_ROOT / "automated_decisions/threshold_policy_freeze.json",
}
EXPECTED_DECISIONS = {
    "R2A-PRE-01": (
        "DECISION-COMPONENT-SPECIFICATION-FREEZE-002D-R2",
        "SPECIFICATION_FROZEN",
    ),
    "R2A-PRE-02": ("DECISION-INTERACTION-CONTRACT-002D-R2", "SPECIFICATION_FROZEN"),
    "R2A-PRE-03": (
        "DECISION-ARCHITECTURE-CANDIDATE-SET-002D-R2",
        "CANDIDATE_SET_FROZEN",
    ),
    "R2A-PRE-04": (
        "DECISION-PROSPECTIVE-BENCHMARK-FREEZE-002D-R2",
        "BENCHMARK_FROZEN",
    ),
    "R2A-PRE-05": ("DECISION-THRESHOLD-POLICY-FREEZE-002D-R2", "POLICY_FROZEN"),
}
UNKNOWN_FACTS = [
    "CLEAN_ROOM_LEGAL_COMPLIANCE_NOT_PROVEN",
    "HIDDEN_VAULT_OS_ISOLATION_NOT_VERIFIED",
    "PROTOTYPE_EFFECTIVENESS_UNMEASURED",
    "MONETARY_COST_UNKNOWN",
]


def _check(check_id: str, passed: bool, observed: str, *refs: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "PASS" if passed else "FAIL",
        "required": True,
        "observed": observed,
        "evidence_refs": list(dict.fromkeys(refs)),
    }


def _decision_check(root: Path, check_id: str) -> dict[str, Any]:
    path = DECISION_PATHS[check_id]
    value = read_json(root / path)
    core = value["automated_decision"]
    expected_id, expected_scope = EXPECTED_DECISIONS[check_id]
    passed = (
        core["decision_id"] == expected_id
        and core["decision"] == "AUTOMATED_ACCEPTED"
        and value["phase_scope"] == expected_scope
    )
    return _check(
        check_id,
        passed,
        f"{core['decision_id']}={core['decision']}/{value['phase_scope']}",
        path.as_posix(),
    )


def build_preconditions(root: Path) -> dict[str, Any]:
    freeze = read_json(root / FREEZE_PATH)
    state = historical_json_if_successor(root, "state/project_state.json")
    audit = read_json(root / R2_ROOT / "decision_audit/audit.json")
    replay = read_json(root / R2_ROOT / "replay/replay.json")
    r2_findings = read_json(root / R2_ROOT / "adversarial_findings/findings.json")["findings"]
    r2_evidence = read_json(root / R2_ROOT / "test_evidence/evidence.json")["test_evidence"]
    r2a_closure = read_json(root / R2A_CLOSURE_PATH)
    architecture = read_yaml(root / "specifications/architectures/architecture_candidate_set.yaml")
    protocol = read_yaml(
        root / "evals/prospective/phase-002d-r2/prospective_experiment_protocol.yaml"
    )
    scope = read_yaml(root / SCOPE_PATH)
    vault = check_benchmark_vault(root)
    r2_passed = {item["finding_id"] for item in r2_evidence if item["status"] == "PASSED"}
    r2_serious = {
        item["finding_id"] for item in r2_findings if item["severity"] in {"BLOCKER", "ERROR"}
    }
    current_skill_hash = tree_hash(
        git_repository_file_hashes(root, (FORMAL_SKILL_ROOT,))
        if competition_rc_successor(root)
        else repository_file_hashes(root, (FORMAL_SKILL_ROOT,))
    )
    skill_files = sorted((root / ".agents/skills").glob("*/SKILL.md"))
    candidate_ids = [item["architecture_id"] for item in architecture["candidates"]]
    stage_ids = {item["stage"] for item in protocol["stages"]}
    execution_zero = all(
        freeze[field] == 0 for field in ("prototype_executions", "third_party_executions")
    )
    checks = [_decision_check(root, check_id) for check_id in sorted(DECISION_PATHS)]
    checks.extend(
        [
            _check(
                "R2A-PRE-06",
                audit["result"] == "PASS",
                f"R2 Decision Auditor={audit['result']}",
                (R2_ROOT / "decision_audit/audit.json").as_posix(),
            ),
            _check(
                "R2A-PRE-07",
                replay["stable"] is True,
                f"R2 replay stable={replay['stable']}",
                (R2_ROOT / "replay/replay.json").as_posix(),
            ),
            _check(
                "R2A-PRE-08",
                r2_serious <= r2_passed
                and r2a_closure["all_serious_findings_closed_for_bounded_authorization"],
                (
                    f"R2 passed serious evidence={len(r2_serious & r2_passed)}/"
                    f"{len(r2_serious)}; R2A closed="
                    f"{r2a_closure['closed_serious_finding_count']}/"
                    f"{r2a_closure['serious_finding_count']}"
                ),
                (R2_ROOT / "test_evidence/evidence.json").as_posix(),
                R2A_CLOSURE_PATH.as_posix(),
            ),
            _check(
                "R2A-PRE-09",
                not any(item["unresolved"] for item in r2_findings)
                and not r2a_closure["unresolved_serious_findings"],
                "unresolved serious blockers=0",
                (R2_ROOT / "adversarial_findings/findings.json").as_posix(),
                R2A_CLOSURE_PATH.as_posix(),
            ),
            _check(
                "R2A-PRE-10",
                not verify_embargo(root),
                "implementation embargo=PASS",
                (R2_ROOT / "implementation_embargo.json").as_posix(),
            ),
            _check(
                "R2A-PRE-11",
                current_skill_hash == freeze["formal_skill_tree_hash"],
                f"formal Skill tree hash={current_skill_hash}",
                FREEZE_PATH.as_posix(),
                ".agents/skills/cumcm-modeling-evidence/SKILL.md",
            ),
            _check(
                "R2A-PRE-12",
                execution_zero and state["specification_protocol"]["prototype_executions"] == 0,
                "prototype executions=0",
                FREEZE_PATH.as_posix(),
                "state/project_state.json",
            ),
            _check(
                "R2A-PRE-13",
                execution_zero and state["specification_protocol"]["third_party_executions"] == 0,
                "third-party executions=0",
                FREEZE_PATH.as_posix(),
                "state/project_state.json",
            ),
            _check(
                "R2A-PRE-14",
                freeze["api_calls"] == 0,
                "API calls=0",
                FREEZE_PATH.as_posix(),
            ),
            _check(
                "R2A-PRE-15",
                freeze["real_batch_model_runs"] == 0,
                "real batch model runs=0",
                FREEZE_PATH.as_posix(),
            ),
            _check(
                "R2A-PRE-16",
                state["selected_architecture"] is None,
                "selected_architecture=null",
                "state/project_state.json",
            ),
            _check(
                "R2A-PRE-17",
                state["base_selected"] is False,
                "base_selected=false",
                "state/project_state.json",
            ),
            _check(
                "R2A-PRE-18",
                state["third_party_integrated"] is False,
                "third_party_integrated=false",
                "state/project_state.json",
            ),
            _check(
                "R2A-PRE-19",
                len(skill_files) == 1 and skill_files[0].parent.name == "cumcm-modeling-evidence",
                f"formal Skill count={len(skill_files)}",
                ".agents/skills/cumcm-modeling-evidence/SKILL.md",
            ),
            _check(
                "R2A-PRE-20",
                vault["status"] == "PASS"
                and vault["public_commitment_verified"] is True
                and vault["private_values_read"] is False,
                (
                    f"vault={vault['status']}; commitment="
                    f"{vault['public_commitment_verified']}; private_values_read="
                    f"{vault['private_values_read']}"
                ),
                "evals/prospective/phase-002d-r2/sealed_manifest.json",
                "evals/prospective/phase-002d-r2/manifests/oracle_commitments.json",
            ),
            _check(
                "R2A-PRE-21",
                vault["status"] == "PASS" and vault["private_values_read"] is False,
                "hidden seed actual values are untracked and unread",
                ".gitignore",
                "evals/prospective/phase-002d-r2/access_policy.yaml",
            ),
            _check(
                "R2A-PRE-22",
                2 <= len(candidate_ids) <= 3,
                f"candidate count={len(candidate_ids)}",
                "specifications/architectures/architecture_candidate_set.yaml",
            ),
            _check(
                "R2A-PRE-23",
                architecture["baseline_id"] == "ARCH-S0-RETAIN-SCAFFOLD-ONLY"
                and architecture["baseline_id"] in candidate_ids,
                f"baseline={architecture['baseline_id']}",
                "specifications/architectures/architecture_candidate_set.yaml",
            ),
            _check(
                "R2A-PRE-24",
                stage_ids == {1, 2, 3},
                f"prospective protocol stages={sorted(stage_ids)}",
                "evals/prospective/phase-002d-r2/prospective_experiment_protocol.yaml",
            ),
            _check(
                "R2A-PRE-25",
                protocol["absolute_start_cap"] <= 30
                and protocol["resource_caps"]["model_starts_including_retries"] <= 30,
                f"frozen model-run cap={protocol['absolute_start_cap']}",
                "evals/prospective/phase-002d-r2/prospective_experiment_protocol.yaml",
            ),
            _check(
                "R2A-PRE-26",
                scope["accepted_scope"] == ACCEPTED_SCOPE
                and validate_scope_value(root, scope) == [],
                f"accepted scope={scope['accepted_scope']}",
                SCOPE_PATH.as_posix(),
            ),
            _check(
                "R2A-PRE-27",
                scope["phase003_prohibited"] is True,
                "Phase 003 remains prohibited",
                SCOPE_PATH.as_posix(),
                "rules/phase002d_r2a_workflow_rules.yaml",
            ),
        ]
    )
    checks = sorted(checks, key=lambda item: item["check_id"])
    failed = [item["check_id"] for item in checks if item["status"] != "PASS"]
    freeze_errors = verify_input_freeze(root)
    eligibility = (
        "STALE"
        if freeze_errors
        else ("ELIGIBLE_FOR_BOUNDED_CANDIDATE" if not failed else "RETEST_REQUIRED")
    )
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_id": "PHASE-002D-R2A-AUTHORIZATION-PRECONDITIONS-001",
        "created_at": CREATED_AT,
        "input_freeze_id": freeze["freeze_id"],
        "input_freeze_hash": freeze["manifest_hash"],
        "checks": checks,
        "required_check_count": len(checks),
        "passed_check_count": sum(item["status"] == "PASS" for item in checks),
        "failed_check_ids": failed,
        "unknowns": UNKNOWN_FACTS,
        "all_required_pass": not failed and not freeze_errors,
        "eligibility": eligibility,
    }
    body["preconditions_hash"] = sha256_json(body)
    return body


def validate_preconditions_value(root: Path, value: dict[str, Any]) -> list[str]:
    errors = [
        f"R2A_PRECONDITION_SCHEMA:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(read_json(root / PRECONDITIONS_SCHEMA_PATH)).iter_errors(
            value
        )
    ]
    body = dict(value)
    recorded_hash = body.pop("preconditions_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("R2A_PRECONDITION_HASH_MISMATCH")
    ids = [item.get("check_id") for item in value.get("checks", [])]
    expected_ids = [f"R2A-PRE-{index:02d}" for index in range(1, 28)]
    if ids != expected_ids:
        errors.append("R2A_PRECONDITION_CHECK_SET_MISMATCH")
    passed = sum(item.get("status") == "PASS" for item in value.get("checks", []))
    failed = [
        item.get("check_id") for item in value.get("checks", []) if item.get("status") != "PASS"
    ]
    if value.get("required_check_count") != 27 or value.get("passed_check_count") != passed:
        errors.append("R2A_PRECONDITION_COUNT_MISMATCH")
    if value.get("failed_check_ids") != failed:
        errors.append("R2A_PRECONDITION_FAILURE_LIST_MISMATCH")
    if value.get("all_required_pass") != (passed == 27):
        errors.append("R2A_PRECONDITION_SUMMARY_MISMATCH")
    eligibility = value.get("eligibility")
    if eligibility == "ELIGIBLE_FOR_BOUNDED_CANDIDATE" and passed != 27:
        errors.append("R2A_PRECONDITION_ELIGIBILITY_MISMATCH")
    if eligibility == "RETEST_REQUIRED" and passed == 27:
        errors.append("R2A_PRECONDITION_ELIGIBILITY_MISMATCH")
    return sorted(set(errors))


def check_or_write_preconditions(root: Path, *, check: bool) -> dict[str, Any]:
    expected = build_preconditions(root)
    errors = validate_preconditions_value(root, expected)
    errors.extend(check_or_write(root / PRECONDITIONS_PATH, expected, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "record_id": expected["record_id"],
        "preconditions_hash": expected["preconditions_hash"],
        "required_check_count": expected["required_check_count"],
        "passed_check_count": expected["passed_check_count"],
        "failed_check_ids": expected["failed_check_ids"],
        "eligibility": expected["eligibility"],
    }


__all__ = [
    "PRECONDITIONS_PATH",
    "build_preconditions",
    "check_or_write_preconditions",
    "validate_preconditions_value",
]
