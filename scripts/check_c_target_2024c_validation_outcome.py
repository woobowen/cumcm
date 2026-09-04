#!/usr/bin/env python3
"""Validate the terminal, answer-sealed 2024 C one-shot outcome."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "evals/results/phase-004c-c-validation"
FREEZE_PATH = RESULT_ROOT / "terminal_validation_freeze.json"
DECISION_PATH = RESULT_ROOT / "DECISION-C-TARGET-VALIDATION-004C.json"
RECEIPT_PATH = RESULT_ROOT / "terminal_validation_freeze_delivery.json"
REGISTRY_PATH = ROOT / "benchmarks/case_registry.yaml"
CASE_ID = "CUMCM-2024-C-VALIDATION-001"
EXPECTED_DECISION = "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT"
EXPECTED_NEXT_PHASE = "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2"
EXPECTED_GATE_REASON = "RC_CLAIM_PRIMARY_REQUIREMENT_BINDING_INVALID"
EXPECTED_RUN_IDS = {
    "RUN-BASELINE_RULE_ROTATION-104729",
    "RUN-BASELINE_RULE_ROTATION-130363",
    "RUN-PRIMARY_RISK_GREEDY-104729",
    "RUN-PRIMARY_RISK_GREEDY-130363",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def git_bytes(*arguments: str) -> bytes | None:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    return completed.stdout if completed.returncode == 0 else None


def validate_document(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    payload = dict(freeze)
    payload_hash = payload.pop("freeze_payload_sha256", None)
    if not HEX64.fullmatch(str(payload_hash or "")) or canonical_hash(payload) != payload_hash:
        errors.append("VALIDATION_TERMINAL_PAYLOAD_HASH_MISMATCH")
    decision = freeze.get("decision", {})
    workspace = freeze.get("case_workspace", {})
    skill = freeze.get("formal_skill", {})
    if (
        freeze.get("schema_version") != "1.0.0"
        or freeze.get("artifact_type") != "c_target_validation_terminal_freeze"
        or freeze.get("freeze_id") != "CUMCM-2024-C-VALIDATION-001-TERMINAL-FREEZE-001"
        or freeze.get("case_id") != CASE_ID
        or freeze.get("target_problem_type") != "C"
        or freeze.get("answer_state") != "SEALED"
        or freeze.get("contamination_status") != "NO_KNOWN_SOLUTION_OR_REFERENCE_EXPOSURE"
    ):
        errors.append("VALIDATION_TERMINAL_HEADER_INVALID")
    if (
        not isinstance(decision, dict)
        or decision.get("decision_id") != "DECISION-C-TARGET-VALIDATION-004C"
        or decision.get("status") != EXPECTED_DECISION
        or decision.get("next_phase_allowed") != EXPECTED_NEXT_PHASE
    ):
        errors.append("VALIDATION_TERMINAL_DECISION_INVALID")
    if (
        not isinstance(workspace, dict)
        or workspace.get("case_state") != "REJECTED"
        or workspace.get("run_count") != 4
        or set(workspace.get("run_ids", [])) != EXPECTED_RUN_IDS
        or not HEX64.fullmatch(str(workspace.get("case_state_sha256", "")))
    ):
        errors.append("VALIDATION_TERMINAL_WORKSPACE_RECORD_INVALID")
    if (
        not isinstance(skill, dict)
        or skill.get("version") != "0.2.0-competition-rc4"
        or skill.get("release_commit") != "46e13d31a3d22fe12a2cffe65a52558da3ecfa82"
        or skill.get("git_tree_sha1_before_validation")
        != "d041ca38de030ae04813ef02dbe12f7f2b7a1c22"
        or skill.get("git_tree_sha1_after_validation")
        != skill.get("git_tree_sha1_before_validation")
        or skill.get("mutation_result") != "UNCHANGED"
    ):
        errors.append("VALIDATION_TERMINAL_SKILL_RECORD_INVALID")
    failure = freeze.get("failure", {})
    if (
        not isinstance(failure, dict)
        or failure.get("formal_gate") != "GATE_CLAIM_EVIDENCE"
        or failure.get("formal_reason_codes") != [EXPECTED_GATE_REASON]
        or failure.get("mutually_exclusive_equalities") is not True
        or failure.get("passing_claim_artifact_exists") is not False
        or failure.get("handoff_status") != "NOT_REACHED_BECAUSE_CLAIM_GATE_BLOCKED"
    ):
        errors.append("VALIDATION_TERMINAL_FAILURE_RECORD_INVALID")
    requirements = freeze.get("pass_requirement_results", {})
    if (
        not isinstance(requirements, dict)
        or len(requirements) != 12
        or requirements.get("CLAIM_EVIDENCE_COMPLETE") != "FAIL_FROZEN_GATE_CONTRADICTION"
        or requirements.get("HANDOFF_COMPLETE") != "FAIL_NOT_REACHED"
        or requirements.get("ALL_MAIN_PROBLEMS_HAVE_VALID_OUTPUTS") != "PASS_6_OF_6"
        or requirements.get("FORMAL_SKILL_UNCHANGED") != "PASS"
    ):
        errors.append("VALIDATION_TERMINAL_PASS_REQUIREMENTS_INVALID")
    hard_failures = freeze.get("hard_failure_audit", {})
    if (
        not isinstance(hard_failures, dict)
        or hard_failures.get("observed_count") != 0
        or hard_failures.get("observed") != []
        or len(hard_failures.get("not_observed", [])) != 12
    ):
        errors.append("VALIDATION_TERMINAL_HARD_FAILURE_AUDIT_INVALID")
    runs = freeze.get("run_records", [])
    if (
        not isinstance(runs, list)
        or len(runs) != 4
        or {item.get("run_id") for item in runs if isinstance(item, dict)} != EXPECTED_RUN_IDS
        or any(
            not isinstance(item, dict)
            or item.get("outcome") != "SUCCESS"
            or item.get("retry_count") != 0
            for item in runs
        )
    ):
        errors.append("VALIDATION_TERMINAL_RUN_RECORDS_INVALID")
    terminal = freeze.get("terminal_invariants", {})
    if (
        not isinstance(terminal, dict)
        or terminal.get("new_run_after_terminal_freeze") is not False
        or terminal.get("formal_skill_mutated") is not False
        or terminal.get("answer_remains_sealed") is not True
        or terminal.get("accepted_handoff_created") is not False
        or terminal.get("same_case_future_role") != "DEVELOPMENT_ONLY"
    ):
        errors.append("VALIDATION_TERMINAL_INVARIANTS_INVALID")
    timing = freeze.get("timing", {})
    if (
        not isinstance(timing, dict)
        or timing.get("maximum_wall_seconds") != 14400
        or timing.get("time_bound_respected") is not True
        or not isinstance(timing.get("elapsed_to_terminal_freeze_seconds"), int)
        or timing.get("elapsed_to_terminal_freeze_seconds", 14401) > 14400
    ):
        errors.append("VALIDATION_TERMINAL_TIMING_INVALID")
    return errors


def validate_tracked_bindings(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    subject = str(freeze.get("subject_commit", ""))
    code = freeze.get("model_code", {})
    skill = freeze.get("formal_skill", {})
    if not HEX40.fullmatch(subject) or git_bytes("cat-file", "-e", f"{subject}^{{commit}}") is None:
        errors.append("VALIDATION_TERMINAL_SUBJECT_COMMIT_INVALID")
        return errors
    code_bytes = git_bytes("show", f"{subject}:{code.get('path')}")
    code_tree = git_bytes("rev-parse", f"{subject}:evals/validation_code/phase-004c/{CASE_ID}")
    skill_tree = git_bytes("rev-parse", f"{subject}:.agents/skills/cumcm-modeling-evidence")
    runner_bytes = git_bytes(
        "show",
        f"{skill.get('release_commit')}:.agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
    )
    if (
        code_bytes is None
        or file_digest(code_bytes) != code.get("sha256")
        or code_tree is None
        or code_tree.decode().strip() != code.get("tree_sha1")
    ):
        errors.append("VALIDATION_TERMINAL_CODE_BINDING_INVALID")
    if (
        skill_tree is None
        or skill_tree.decode().strip() != skill.get("git_tree_sha1_after_validation")
        or runner_bytes is None
        or file_digest(runner_bytes) != skill.get("runner_sha256")
    ):
        errors.append("VALIDATION_TERMINAL_SKILL_BINDING_INVALID")
    return errors


def file_digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_decision(freeze: dict[str, Any]) -> list[str]:
    if not DECISION_PATH.is_file():
        return ["VALIDATION_TERMINAL_DECISION_MISSING"]
    decision = load_json(DECISION_PATH)
    terminal = decision.get("terminal_freeze", {})
    basis = decision.get("decision_basis", {})
    errors: list[str] = []
    if (
        decision.get("schema_version") != "1.0.0"
        or decision.get("decision_id") != "DECISION-C-TARGET-VALIDATION-004C"
        or decision.get("case_id") != CASE_ID
        or decision.get("status") != EXPECTED_DECISION
        or decision.get("next_phase_allowed") != EXPECTED_NEXT_PHASE
        or decision.get("answer_state") != "SEALED"
        or decision.get("same_case_future_role") != "DEVELOPMENT_ONLY"
    ):
        errors.append("VALIDATION_TERMINAL_DECISION_DOCUMENT_INVALID")
    if (
        not isinstance(terminal, dict)
        or terminal.get("sha256") != file_hash(FREEZE_PATH)
        or terminal.get("payload_sha256") != freeze.get("freeze_payload_sha256")
    ):
        errors.append("VALIDATION_TERMINAL_DECISION_FREEZE_BINDING_INVALID")
    if (
        not isinstance(basis, dict)
        or basis.get("claim_evidence_complete") is not False
        or basis.get("handoff_complete") is not False
        or basis.get("claim_gate_reason_codes") != [EXPECTED_GATE_REASON]
        or basis.get("hard_failure_count") != 0
        or basis.get("run_success_count") != 4
        or basis.get("run_total") != 4
    ):
        errors.append("VALIDATION_TERMINAL_DECISION_BASIS_INVALID")
    return errors


def validate_workspace(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    workspace_record = freeze.get("case_workspace", {})
    workspace = ROOT / str(workspace_record.get("path", ""))
    if not workspace.is_dir():
        return ["VALIDATION_TERMINAL_WORKSPACE_MISSING"]
    state_path = workspace / "case_state.json"
    state = load_json(state_path) if state_path.is_file() else {}
    run_ids = (
        {item.name for item in (workspace / "runs").iterdir() if item.is_dir()}
        if (workspace / "runs").is_dir()
        else set()
    )
    if (
        state.get("case_id") != CASE_ID
        or state.get("state") != "REJECTED"
        or file_hash(state_path) != workspace_record.get("case_state_sha256")
    ):
        errors.append("VALIDATION_TERMINAL_CASE_STATE_DRIFT")
    if run_ids != EXPECTED_RUN_IDS:
        errors.append("VALIDATION_TERMINAL_RUN_SET_DRIFT")
    for relative, expected in freeze.get("input_hashes", {}).items():
        path = workspace / relative
        if not path.is_file() or file_hash(path) != expected:
            errors.append(f"VALIDATION_TERMINAL_INPUT_DRIFT:{relative}")
    for relative, expected in freeze.get("supporting_artifact_hashes", {}).items():
        path = workspace / relative
        if not path.is_file() or file_hash(path) != expected:
            errors.append(f"VALIDATION_TERMINAL_ARTIFACT_DRIFT:{relative}")
    for record in freeze.get("run_records", []):
        if not isinstance(record, dict):
            continue
        root = workspace / "runs" / str(record.get("run_id", ""))
        for field, filename in (
            ("capture_sha256", "execution_capture.json"),
            ("manifest_sha256", "manifest.json"),
            ("output_sha256", "output.json"),
            ("result1_1_sha256", "result1_1.xlsx"),
            ("result1_2_sha256", "result1_2.xlsx"),
            ("result2_sha256", "result2.xlsx"),
        ):
            path = root / filename
            if not path.is_file() or file_hash(path) != record.get(field):
                errors.append(
                    f"VALIDATION_TERMINAL_RUN_ARTIFACT_DRIFT:{record.get('run_id')}:{filename}"
                )
    command = [
        str(ROOT / ".venv/bin/python"),
        str(ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"),
        "claim-check",
        "--case-root",
        str(workspace),
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = {}
    if (
        completed.returncode != 3
        or result.get("status") != "BLOCK"
        or result.get("reason_codes") != [EXPECTED_GATE_REASON]
    ):
        errors.append("VALIDATION_TERMINAL_CLAIM_GATE_NOT_REPLAYED")
    return errors


def validate_delivery(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not RECEIPT_PATH.is_file():
        return ["VALIDATION_TERMINAL_DELIVERY_MISSING"]
    receipt = load_json(RECEIPT_PATH)
    if (
        receipt.get("status") != "REMOTE_DELIVERED"
        or receipt.get("freeze_id") != freeze.get("freeze_id")
        or receipt.get("freeze_file_sha256") != file_hash(FREEZE_PATH)
        or receipt.get("freeze_payload_sha256") != freeze.get("freeze_payload_sha256")
        or receipt.get("decision_sha256") != file_hash(DECISION_PATH)
        or receipt.get("freeze_commit") != receipt.get("remote_sha")
    ):
        errors.append("VALIDATION_TERMINAL_DELIVERY_INVALID")
    registry = load_yaml(REGISTRY_PATH)
    matches = [
        item
        for item in registry.get("cases", [])
        if isinstance(item, dict) and item.get("case_id") == CASE_ID
    ]
    record = matches[0] if len(matches) == 1 else {}
    registered_freeze = record.get("first_run_freeze", {})
    if (
        len(matches) != 1
        or record.get("answer_access_status") != "SEALED"
        or record.get("reference_unlock") != "LOCKED"
        or record.get("first_run_status") != "FROZEN_EVIDENCE_INSUFFICIENT"
        or record.get("validation_decision") != EXPECTED_DECISION
        or record.get("same_case_future_role") != "DEVELOPMENT_ONLY"
        or not isinstance(registered_freeze, dict)
        or registered_freeze.get("path") != str(FREEZE_PATH.relative_to(ROOT))
        or registered_freeze.get("sha256") != file_hash(FREEZE_PATH)
        or registered_freeze.get("payload_sha256") != freeze.get("freeze_payload_sha256")
        or registered_freeze.get("freeze_commit") != receipt.get("freeze_commit")
        or registered_freeze.get("remote_sha") != receipt.get("remote_sha")
    ):
        errors.append("VALIDATION_TERMINAL_REGISTRY_INVALID")
    return errors


def evaluate(*, verify_workspace: bool, require_delivery: bool) -> dict[str, Any]:
    if not FREEZE_PATH.is_file():
        return {"error_count": 1, "errors": ["VALIDATION_TERMINAL_FREEZE_MISSING"], "ok": False}
    freeze = load_json(FREEZE_PATH)
    errors = validate_document(freeze)
    errors.extend(validate_tracked_bindings(freeze))
    errors.extend(validate_decision(freeze))
    if verify_workspace:
        errors.extend(validate_workspace(freeze))
    if require_delivery:
        errors.extend(validate_delivery(freeze))
    errors = sorted(set(errors))
    return {
        "case_id": freeze.get("case_id"),
        "decision": freeze.get("decision", {}).get("status"),
        "error_count": len(errors),
        "errors": errors,
        "freeze_payload_sha256": freeze.get("freeze_payload_sha256"),
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--verify-workspace", action="store_true")
    parser.add_argument("--require-delivery", action="store_true")
    args = parser.parse_args()
    result = evaluate(
        verify_workspace=args.verify_workspace,
        require_delivery=args.require_delivery,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
