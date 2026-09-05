#!/usr/bin/env python3
"""Offline chronology, immutable evidence and terminal routing checks for one fresh episode."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "CUMCM-2019-C-VALIDATION-002"
RESULTS = Path("evals/results/phase-004c2")
CASE = RESULTS / CASE_ID
SKILL = ".agents/skills/cumcm-modeling-evidence"
PIPELINE_REQUIREMENTS = {
    "all_primary_outputs_valid",
    "baseline_and_primary_executed",
    "independent_control_executed",
    "final_run_current_sealed_validated",
    "robustness_complete",
    "requirement_claims_valid",
    "aggregate_coverage_exact",
    "claim_lineage_exact",
    "handoff_valid",
    "ready_for_paper_handoff",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def payload_hash(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def terminal_outcome(facts):
    """Hard failures and primary empirical coverage cannot be offset by simulation scores."""
    if facts.get("skill_unchanged") is not True:
        return "VALIDATION_CANDIDATE_DRIFT", ["VALIDATION_SKILL_DRIFT"]
    if facts.get("answer_sealed") is not True:
        return "FIRST_RUN_CONTAMINATION_SUSPECTED", ["VALIDATION_ANSWER_EXPOSED"]
    if facts.get("one_shot_and_timebox_respected") is not True:
        return "C_TARGET_VALIDATION_FAILED", ["VALIDATION_EPISODE_BOUNDARY_VIOLATED"]
    if facts["uncompensable_model_failures"]:
        return "C_TARGET_VALIDATION_FAILED", sorted(facts["uncompensable_model_failures"])
    if facts.get("empirical_primary_requirement_satisfied") is not True:
        return "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT", [
            "VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING"
        ]
    pipeline = facts.get("pipeline_pass_requirements", {})
    if set(pipeline) != PIPELINE_REQUIREMENTS or not all(
        value is True for value in pipeline.values()
    ):
        return "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT", [
            "VALIDATION_PIPELINE_EVIDENCE_INCOMPLETE"
        ]
    return "C_TARGET_VALIDATION_PASSED", []


def evaluate(root=ROOT, *, verify_workspace=False, require_delivery=False):
    errors = []
    state = read(root / "state/project_state.json")
    successor = state.get("phase") == "PHASE-SKILL-C-TARGET-EVIDENCE-REPAIR-004C3"
    release = read(root / RESULTS / "rc5_release.json")
    receipt = read(root / RESULTS / "rc5_release_delivery.json")
    if (
        receipt["release_commit"] != receipt["remote_sha"]
        or receipt["status"] != "REMOTE_DELIVERED"
    ):
        errors.append("RC5_RELEASE_DELIVERY_INVALID")
    frozen_release = subprocess.check_output(
        ["git", "show", f"{receipt['release_commit']}:{RESULTS}/rc5_release.json"], cwd=root
    )
    if hashlib.sha256(frozen_release).hexdigest() != digest(root / RESULTS / "rc5_release.json"):
        errors.append("RC5_RELEASE_COMMIT_BINDING_INVALID")
    for source in read(root / CASE / "registration/official_retrieval.json")["sources"]:
        if datetime.fromisoformat(source["retrieved_at"]) <= datetime.fromisoformat(
            receipt["verified_at"]
        ):
            errors.append("VALIDATION_INPUT_BEFORE_REMOTE_RELEASE")
    inputs = read(root / CASE / "registration/input_registration.json")
    if inputs["answer_access_status"] != "SEALED":
        errors.append("VALIDATION_INPUT_ANSWER_NOT_SEALED")
    pre_path = root / CASE / "pre_run/pre_run_validation_freeze.json"
    terminal_path = root / CASE / "terminal_freeze/terminal_validation_freeze.json"
    historical_commit = (
        read(terminal_path.with_name(terminal_path.stem + "_delivery.json"))["commit"]
        if successor
        else None
    )
    for path in (pre_path, terminal_path):
        if not path.is_file():
            continue
        freeze = read(path)
        payload = dict(freeze)
        expected = payload.pop("freeze_payload_sha256")
        if payload_hash(payload) != expected:
            errors.append("VALIDATION_FREEZE_PAYLOAD_DRIFT:" + path.name)
        if (
            freeze["case_id"] != CASE_ID
            or freeze["set_type"] != "VALIDATION"
            or freeze["answer_access_status"] != "SEALED"
            or freeze["skill_release_commit"] != receipt["release_commit"]
            or freeze["skill_tree"] != release["skill_tree"]
            or freeze["maximum_wall_seconds"] != 14400
        ):
            errors.append("VALIDATION_FREEZE_IDENTITY_INVALID:" + path.name)
        for relative, expected_hash in freeze["artifact_hashes"].items():
            actual_hash = (
                hashlib.sha256(
                    subprocess.check_output(
                        ["git", "show", f"{historical_commit}:{relative}"], cwd=root
                    )
                ).hexdigest()
                if historical_commit is not None
                else digest(root / relative)
            )
            if actual_hash != expected_hash:
                errors.append("VALIDATION_ARTIFACT_DRIFT:" + relative)
        for relative, expected_hash in freeze["case_code_hashes"].items():
            blob = subprocess.check_output(
                ["git", "show", f"{freeze['case_code_commit']}:{relative}"], cwd=root
            )
            if hashlib.sha256(blob).hexdigest() != expected_hash:
                errors.append("VALIDATION_CODE_COMMIT_BINDING_INVALID:" + relative)
        delivery_path = path.with_name(path.stem + "_delivery.json")
        if delivery_path.is_file():
            delivery = read(delivery_path)
            blob = subprocess.check_output(
                ["git", "show", f"{delivery['commit']}:{path.relative_to(root)}"], cwd=root
            )
            if (
                delivery["commit"] != delivery["remote_sha"]
                or delivery["status"] != "REMOTE_DELIVERED"
                or hashlib.sha256(blob).hexdigest() != digest(path)
            ):
                errors.append("VALIDATION_FREEZE_DELIVERY_INVALID:" + path.name)
        elif require_delivery:
            errors.append("VALIDATION_FREEZE_DELIVERY_MISSING:" + path.name)
    if terminal_path.is_file():
        freeze = read(terminal_path)
        decision = read(root / CASE / "validation/DECISION-C-TARGET-VALIDATION-004C2.json")
        expected_status, reasons = terminal_outcome(decision["facts"])
        if decision["status"] != expected_status or decision["reason_codes"] != reasons:
            errors.append("VALIDATION_DECISION_REPLAY_MISMATCH")
        expected_next = (
            "PHASE-SKILL-C-TARGET-HELDOUT-004D"
            if expected_status == "C_TARGET_VALIDATION_PASSED"
            else None
        )
        if decision["next_phase_allowed"] != expected_next:
            errors.append("VALIDATION_NEXT_PHASE_INVALID")
        elapsed = (
            datetime.fromisoformat(freeze["frozen_at"])
            - datetime.fromisoformat(freeze["episode_started_at"])
        ).total_seconds()
        if not 0 <= elapsed <= freeze["maximum_wall_seconds"]:
            errors.append("VALIDATION_TIMEBOX_EXCEEDED")
        registered_empirical = any(item.get("role") == "DATA" for item in inputs["files"])
        if (
            decision["facts"]["empirical_primary_requirement_satisfied"]
            and not registered_empirical
        ):
            errors.append("VALIDATION_EMPIRICAL_REQUIREMENT_UNSUPPORTED_BY_REGISTERED_INPUTS")
        pre_delivery = read(pre_path.with_name(pre_path.stem + "_delivery.json"))
        for record in freeze["run_records"]:
            if not (
                datetime.fromisoformat(pre_delivery["verified_at"])
                <= datetime.fromisoformat(record["started_at"])
                <= datetime.fromisoformat(record["ended_at"])
                <= datetime.fromisoformat(freeze["frozen_at"])
            ):
                errors.append("VALIDATION_RUN_CHRONOLOGY_INVALID:" + record["run_id"])
        if verify_workspace:
            workspace = root / freeze["workspace_relative"]
            if sorted(p.name for p in (workspace / "runs").iterdir()) != sorted(
                item["run_id"] for item in freeze["run_records"]
            ):
                errors.append("VALIDATION_POST_FREEZE_RUN_OR_REMOVED_RUN")
            for relative, expected_hash in freeze["workspace_hashes"].items():
                if (
                    not (workspace / relative).is_file()
                    or digest(workspace / relative) != expected_hash
                ):
                    errors.append("VALIDATION_WORKSPACE_DRIFT:" + relative)
    return {
        "ok": not errors,
        "errors": errors,
        "error_count": len(errors),
        "case_id": CASE_ID,
        "pre_run_frozen": pre_path.is_file(),
        "terminal_frozen": terminal_path.is_file(),
        "workspace_verified": verify_workspace,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", required=True, action="store_true")
    parser.add_argument("--verify-workspace", action="store_true")
    parser.add_argument("--require-delivery", action="store_true")
    args = parser.parse_args()
    result = evaluate(
        verify_workspace=args.verify_workspace, require_delivery=args.require_delivery
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
