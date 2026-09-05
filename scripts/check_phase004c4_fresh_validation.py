#!/usr/bin/env python3
"""Check the frozen Phase 004C4 fresh C Validation terminal outcome."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "CUMCM-2017-C-VALIDATION-003F"
CASE_RELATIVE = Path("evals/results/phase-004c4/fresh_validation") / CASE_ID
FREEZE_RELATIVE = CASE_RELATIVE / "terminal_freeze/terminal_validation_freeze.json"
DELIVERY_RELATIVE = CASE_RELATIVE / "terminal_freeze/terminal_validation_freeze_delivery.json"
DECISION_RELATIVE = CASE_RELATIVE / "validation/DECISION-C-TARGET-VALIDATION-004C4.json"
AUDIT_RELATIVE = CASE_RELATIVE / "validation/fresh_integrity_audit.json"
CHALLENGE_RELATIVE = (
    CASE_RELATIVE / "validation/challenges/HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION.json"
)
EXPECTED_VERDICT = "C_TARGET_VALIDATION_FAILED"
EXPECTED_REASONS = [
    "VALIDATION_FINALIZATION_INTERFACE_CONTRACT_FAILURE",
    "VALIDATION_FINAL_RUN_NOT_COMPLETED",
    "VALIDATION_HANDOFF_NOT_REACHED",
]
EXPECTED_HARD_FAILURES = ["HF14", "HF21", "HF23"]
EXPECTED_NEXT = "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5"
EXPECTED_AUDIT_FINDING = "HF22_SEMANTIC_SUPPORT_FALSE_DECLARATION"
EXPECTED_RUN_IDS = {
    f"RUN-{candidate}-{seed}"
    for candidate in ("BASELINE_MEDIAN", "KERNEL_RBF_RIDGE", "RIDGE_LINEAR")
    for seed in (17001, 17017, 17033)
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def skill_tree_hash() -> str:
    skill_root = ".agents/skills/cumcm-modeling-evidence"
    files = subprocess.check_output(
        ["git", "ls-files", skill_root], cwd=ROOT, text=True
    ).splitlines()
    mapping = {path: file_hash(ROOT / path) for path in files if (ROOT / path).is_file()}
    return canonical_hash(mapping)


def validate_freeze_document(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    payload = dict(freeze)
    declared_payload_hash = payload.pop("freeze_payload_sha256", None)
    if declared_payload_hash != canonical_hash(payload):
        errors.append("PHASE004C4_TERMINAL_FREEZE_PAYLOAD_HASH_INVALID")
    if (
        freeze.get("schema_version") != "phase-004c4-fresh-validation-terminal-freeze/v1"
        or freeze.get("freeze_id") != "CUMCM-2017-C-VALIDATION-003F-TERMINAL-FREEZE-001"
        or freeze.get("case_id") != CASE_ID
        or freeze.get("verdict") != EXPECTED_VERDICT
        or freeze.get("reason_codes") != EXPECTED_REASONS
        or freeze.get("hard_failure_ids") != EXPECTED_HARD_FAILURES
        or freeze.get("next_phase_allowed") != EXPECTED_NEXT
    ):
        errors.append("PHASE004C4_TERMINAL_FREEZE_IDENTITY_INVALID")
    if (
        freeze.get("answer_access_status") != "SEALED"
        or freeze.get("sealed_test_access_count") != 0
        or freeze.get("reference_unlock") != "LOCKED"
        or freeze.get("one_shot_respected") is not True
        or freeze.get("retry_count") != 0
        or freeze.get("post_result_tuning_count") != 0
        or freeze.get("run_count") != 9
        or freeze.get("same_case_rerun_allowed") is not False
        or freeze.get("new_runs_after_freeze_allowed") is not False
    ):
        errors.append("PHASE004C4_TERMINAL_BOUNDARY_INVALID")
    start = datetime.fromisoformat(str(freeze.get("episode_started_at")))
    frozen = datetime.fromisoformat(str(freeze.get("frozen_at")))
    if not 0 <= (frozen - start).total_seconds() <= freeze.get("maximum_wall_seconds", -1):
        errors.append("PHASE004C4_TERMINAL_TIMEBOX_INVALID")
    return errors


def validate_tracked_bindings(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for relative, expected in freeze.get("tracked_artifact_hashes", {}).items():
        path = ROOT / relative
        if not path.is_file() or file_hash(path) != expected:
            errors.append(f"PHASE004C4_TRACKED_ARTIFACT_DRIFT:{relative}")
    for relative, expected in freeze.get("case_code_hashes", {}).items():
        path = ROOT / relative
        if not path.is_file() or file_hash(path) != expected:
            errors.append(f"PHASE004C4_CASE_CODE_DRIFT:{relative}")
    release = load_json(ROOT / "evals/results/phase-004c4/rc7_release.json")
    identity = freeze.get("release_identity", {})
    runner = ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
    controller = ROOT / "scripts/finalize_fresh_c_validation.py"
    if (
        identity.get("skill_version") != "0.2.0-competition-rc7"
        or identity.get("release_commit") != "22abe92d2b5da2e3f1be3161e8376fb83b0cee0a"
        or identity.get("skill_tree_sha256") != release.get("skill_tree_hash")
        or identity.get("skill_tree_sha256") != skill_tree_hash()
        or identity.get("runner_sha256") != file_hash(runner)
        or identity.get("controller_sha256") != file_hash(controller)
        or identity.get("skill_unchanged") is not True
    ):
        errors.append("PHASE004C4_TERMINAL_SKILL_BINDING_INVALID")
    return errors


def validate_decision_and_summaries(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    decision = load_json(ROOT / DECISION_RELATIVE)
    if (
        decision.get("decision_id") != "DECISION-C-TARGET-VALIDATION-004C4"
        or decision.get("status") != EXPECTED_VERDICT
        or decision.get("reason_codes") != EXPECTED_REASONS
        or decision.get("hard_failure_ids") != EXPECTED_HARD_FAILURES
        or decision.get("next_phase_allowed") != EXPECTED_NEXT
        or decision.get("answer_access_status") != "SEALED"
        or decision.get("paper_dispatch_accepted") is not False
        or decision.get("same_case_rerun_allowed") is not False
    ):
        errors.append("PHASE004C4_TERMINAL_DECISION_INVALID")
    summary = load_json(ROOT / CASE_RELATIVE / "validation/selection_and_run_summary.json")
    if (
        summary.get("selection_batch", {}).get("actual_attempt_count") != 9
        or summary.get("selection_batch", {}).get("success_count") != 9
        or summary.get("selection_batch", {}).get("retry_count") != 0
        or summary.get("sealed_test_access_count") != 0
        or summary.get("run_manifest_validation") != "PASS_9_OF_9"
        or summary.get("independent_check_status") != "PASS_9_OF_9"
    ):
        errors.append("PHASE004C4_SELECTION_SUMMARY_INVALID")
    controller = load_json(ROOT / CASE_RELATIVE / "validation/controller_outcome.json")
    if (
        controller.get("invocation_count") != 1
        or controller.get("exit_code") != 1
        or controller.get("status") != "BLOCK_NATIVE_CONTRACTS"
        or controller.get("reason_codes") != ["RC_GATE_EXECUTION_FAILED"]
        or controller.get("missing_gate_ids") != ["GATE_HANDOFF"]
        or controller.get("sealed_test_access_count") != 0
        or controller.get("hard_failure_ids") != EXPECTED_HARD_FAILURES
    ):
        errors.append("PHASE004C4_CONTROLLER_OUTCOME_INVALID")
    episode = load_json(ROOT / CASE_RELATIVE / "validation/fourteen_stage_episode.json")
    stages = episode.get("stages", [])
    if (
        len(stages) != 14
        or [item.get("stage") for item in stages] != list(range(1, 15))
        or stages[11].get("status") != "BLOCK"
        or stages[13].get("status") != "NOT_REACHED_BLOCK"
        or episode.get("terminal_classification") != EXPECTED_VERDICT
    ):
        errors.append("PHASE004C4_FOURTEEN_STAGE_RECORD_INVALID")
    return errors


def validate_state_and_registry() -> list[str]:
    errors: list[str] = []
    audit_path = ROOT / AUDIT_RELATIVE
    challenge_path = ROOT / CHALLENGE_RELATIVE
    audit_sha256 = file_hash(audit_path) if audit_path.is_file() else None
    challenge_sha256 = file_hash(challenge_path) if challenge_path.is_file() else None
    state = load_json(ROOT / "state/project_state.json")
    if (
        state.get("phase") != "PHASE-SKILL-C-TARGET-RUNTIME-PIPELINE-CLOSURE-004C4"
        or state.get("subphase") != "C-TARGET-FRESH-VALIDATION-TERMINAL"
        or state.get("technical_adjudication_status") != EXPECTED_VERDICT
        or state.get("active_skill_version") != "0.2.0-competition-rc7"
        or state.get("current_validation_case") != CASE_ID
        or state.get("answer_access_status") != "SEALED_AT_TERMINAL_FREEZE"
        or state.get("next_phase_allowed") != EXPECTED_NEXT
        or EXPECTED_AUDIT_FINDING not in state.get("blockers", [])
        or state.get("third_party_integrated") is not False
    ):
        errors.append("PHASE004C4_TERMINAL_STATE_INVALID")
    registry = yaml.safe_load((ROOT / "benchmarks/case_registry.yaml").read_text())
    matches = [case for case in registry.get("cases", []) if case.get("case_id") == CASE_ID]
    record = matches[0] if len(matches) == 1 else {}
    if (
        len(matches) != 1
        or record.get("validation_decision") != EXPECTED_VERDICT
        or record.get("answer_access_status") != "SEALED"
        or record.get("reference_unlock") != "LOCKED"
        or record.get("paper_dispatch_accepted") is not False
        or record.get("same_case_future_role") != "DEVELOPMENT_ONLY"
        or record.get("terminal_freeze", {}).get("path") != str(FREEZE_RELATIVE)
        or record.get("integrity_audit", {}).get("status") != "CHALLENGE"
        or record.get("integrity_audit", {}).get("sha256") != audit_sha256
        or record.get("integrity_audit", {}).get("challenge_sha256") != challenge_sha256
    ):
        errors.append("PHASE004C4_TERMINAL_REGISTRY_INVALID")
    reservations = registry.get("held_out_reservations", [])
    heldout = next(
        (
            item
            for item in reservations
            if item.get("reservation_id") == "CUMCM-2025-C-HELDOUT-RESERVED"
        ),
        {},
    )
    flags = (
        "archive_accessed",
        "title_accessed",
        "problem_accessed",
        "attachments_accessed",
        "references_accessed",
        "answer_accessed",
    )
    if heldout.get("status") != "SEALED_NOT_ACCESSED" or any(heldout.get(key) for key in flags):
        errors.append("PHASE004C4_HELDOUT_2025_ACCESSED")
    return errors


def validate_integrity_audit(freeze: dict[str, Any]) -> list[str]:
    if not (ROOT / AUDIT_RELATIVE).is_file() or not (ROOT / CHALLENGE_RELATIVE).is_file():
        return ["PHASE004C4_FRESH_INTEGRITY_AUDIT_MISSING"]
    audit = load_json(ROOT / AUDIT_RELATIVE)
    challenge = load_json(ROOT / CHALLENGE_RELATIVE)
    finding = audit.get("additional_deterministic_blocker", {})
    if (
        audit.get("audit_status") != "CHALLENGE"
        or audit.get("terminal_verdict") != EXPECTED_VERDICT
        or audit.get("terminal_verdict_preserved") is not True
        or audit.get("next_phase_preserved") != EXPECTED_NEXT
        or audit.get("subject_terminal_freeze_sha256") != file_hash(ROOT / FREEZE_RELATIVE)
        or finding.get("finding_id") != EXPECTED_AUDIT_FINDING
        or finding.get("verdict_effect") != "ADDITIONAL_BLOCKER_NO_TERMINAL_VERDICT_CHANGE"
        or finding.get("selected_output_sha256")
        != "78408903d0dc49c801c12c6fb76c8c0c81af86f7e587be5089aa76c800acb57e"
        or finding.get("claim_support_sha256")
        != "afa6ffbc6b5928a410cb2190bbc1c8d3416e3c4067e441e7aafde885387b0157"
        or challenge.get("finding_id") != EXPECTED_AUDIT_FINDING
        or challenge.get("status") != "ACCEPTED_AS_POST_FREEZE_CHALLENGE"
        or challenge.get("next_phase") != EXPECTED_NEXT
        or challenge.get("subject_terminal_freeze_sha256") != file_hash(ROOT / FREEZE_RELATIVE)
    ):
        return ["PHASE004C4_FRESH_INTEGRITY_AUDIT_INVALID"]
    builder = ROOT / str(finding.get("builder_path", ""))
    if not builder.is_file() or file_hash(builder) != finding.get("builder_sha256"):
        return ["PHASE004C4_FRESH_INTEGRITY_AUDIT_BUILDER_DRIFT"]
    return []


def validate_workspace(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    workspace = ROOT / str(freeze.get("workspace_relative", ""))
    if not workspace.is_dir():
        return ["PHASE004C4_TERMINAL_WORKSPACE_MISSING"]
    for relative, expected in freeze.get("workspace_hashes", {}).items():
        path = workspace / relative
        if not path.is_file() or file_hash(path) != expected:
            errors.append(f"PHASE004C4_WORKSPACE_DRIFT:{relative}")
    actual_runs = {path.name for path in (workspace / "runs").iterdir() if path.is_dir()}
    if actual_runs != EXPECTED_RUN_IDS:
        errors.append("PHASE004C4_TERMINAL_RUN_SET_DRIFT")
    records = freeze.get("run_records", [])
    if {record.get("run_id") for record in records} != EXPECTED_RUN_IDS:
        errors.append("PHASE004C4_TERMINAL_RUN_RECORD_SET_INVALID")
    for record in records:
        run_id = str(record.get("run_id", ""))
        run_root = workspace / "runs" / run_id
        checks = {
            "capture_sha256": run_root / "execution_capture.json",
            "output_sha256": run_root / "output.json",
            "manifest_sha256": run_root / "manifest.json",
            "independent_check_sha256": workspace
            / "evidence/independent_checks"
            / f"{run_id}.json",
        }
        for field, path in checks.items():
            if not path.is_file() or file_hash(path) != record.get(field):
                errors.append(f"PHASE004C4_RUN_ARTIFACT_DRIFT:{run_id}:{field}")
    native = load_json(workspace / "evidence/native_completion.json")
    state = load_json(workspace / "case_state.json")
    if native.get("test_access_count") != 0 or state.get("state") != "RUNNING":
        errors.append("PHASE004C4_WORKSPACE_TERMINAL_BOUNDARY_INVALID")
    semantic = load_json(workspace / "evidence/semantic_claim_support.json")
    selected = load_json(workspace / "runs/RUN-KERNEL_RBF_RIDGE-17001/output.json")
    req2_claims = [
        item
        for item in semantic.get("content", {}).get("claims", [])
        if item.get("requirement_id") == "REQ-2-DATA2-CONCENTRATION-MODEL"
    ]
    selected_req2 = selected.get("requirements", {}).get("REQ-2-DATA2-CONCENTRATION-MODEL", {})
    if (
        len(req2_claims) != 1
        or req2_claims[0].get("support_predicates", {}).get("held_out_test_valid") is not True
        or selected.get("evaluation_boundary") != "DEVELOPMENT_GROUPED_OOS"
        or selected.get("test_access", {}).get("status") != "NOT_AUTHORIZED"
        or selected.get("test_access", {}).get("access_count") != 0
        or selected_req2.get("support_predicates", {}).get("held_out_test_valid") is not False
    ):
        errors.append("PHASE004C4_HF22_EVIDENCE_RELATION_DRIFT")
    return errors


def validate_delivery(freeze: dict[str, Any]) -> list[str]:
    if not (ROOT / DELIVERY_RELATIVE).is_file():
        return ["PHASE004C4_TERMINAL_DELIVERY_MISSING"]
    delivery = load_json(ROOT / DELIVERY_RELATIVE)
    errors: list[str] = []
    if (
        delivery.get("status") != "REMOTE_DELIVERED"
        or delivery.get("freeze_id") != freeze.get("freeze_id")
        or delivery.get("freeze_sha256") != file_hash(ROOT / FREEZE_RELATIVE)
        or delivery.get("freeze_payload_sha256") != freeze.get("freeze_payload_sha256")
        or delivery.get("decision_sha256") != file_hash(ROOT / DECISION_RELATIVE)
        or delivery.get("freeze_commit") != delivery.get("remote_sha")
    ):
        errors.append("PHASE004C4_TERMINAL_DELIVERY_INVALID")
    try:
        frozen = subprocess.check_output(
            ["git", "show", f"{delivery.get('freeze_commit')}:{FREEZE_RELATIVE}"], cwd=ROOT
        )
        if hashlib.sha256(frozen).hexdigest() != file_hash(ROOT / FREEZE_RELATIVE):
            errors.append("PHASE004C4_TERMINAL_COMMIT_BINDING_INVALID")
    except subprocess.CalledProcessError:
        errors.append("PHASE004C4_TERMINAL_COMMIT_BINDING_INVALID")
    return errors


def evaluate(*, verify_workspace: bool, require_delivery: bool) -> dict[str, Any]:
    if not (ROOT / FREEZE_RELATIVE).is_file():
        return {
            "case_id": CASE_ID,
            "status": "BLOCK",
            "error_count": 1,
            "errors": ["PHASE004C4_TERMINAL_FREEZE_MISSING"],
        }
    freeze = load_json(ROOT / FREEZE_RELATIVE)
    errors = validate_freeze_document(freeze)
    errors.extend(validate_tracked_bindings(freeze))
    errors.extend(validate_decision_and_summaries(freeze))
    errors.extend(validate_state_and_registry())
    errors.extend(validate_integrity_audit(freeze))
    if verify_workspace:
        errors.extend(validate_workspace(freeze))
    if require_delivery:
        errors.extend(validate_delivery(freeze))
    errors = sorted(set(errors))
    return {
        "case_id": CASE_ID,
        "verdict": freeze.get("verdict"),
        "status": "BLOCK" if errors else "PASS",
        "error_count": len(errors),
        "errors": errors,
        "workspace_verified": verify_workspace,
        "delivery_verified": require_delivery,
        "answer_access_status": freeze.get("answer_access_status"),
        "run_count": freeze.get("run_count"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--verify-workspace", action="store_true")
    parser.add_argument("--require-delivery", action="store_true")
    args = parser.parse_args()
    result = evaluate(
        verify_workspace=args.verify_workspace, require_delivery=args.require_delivery
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
