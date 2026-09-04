#!/usr/bin/env python3
"""Validate the answer-sealed 2024 C one-shot pre-run freeze."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "evals/results/phase-004c-c-validation/pre_run_validation_freeze.json"
RECEIPT_PATH = (
    ROOT / "evals/results/phase-004c-c-validation/pre_run_validation_freeze_delivery.json"
)
REGISTRY_PATH = ROOT / "benchmarks/case_registry.yaml"
CASE_ID = "CUMCM-2024-C-VALIDATION-001"
SKILL_ROOT = ".agents/skills/cumcm-modeling-evidence"
EXPECTED_STAGES = [
    "PROBLEM_INTAKE",
    "REQUIREMENT_DECOMPOSITION",
    "RESEARCH_AND_SOURCE_PLANNING",
    "ASSUMPTION_AND_SYMBOL_DEFINITION",
    "DATA_AUDIT",
    "MODEL_PORTFOLIO_GENERATION",
    "BASELINE_DEFINITION",
    "EXPERIMENT_DESIGN",
    "IMPLEMENTATION_AND_EXECUTION",
    "MODEL_COMPARISON",
    "ROBUSTNESS_AND_SENSITIVITY",
    "FINAL_RUN",
    "CLAIM_EVIDENCE_VALIDATION",
    "MODELING_TO_PAPER_HANDOFF",
]
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


def dependency_snapshot() -> tuple[int, str]:
    packages = sorted(
        (distribution.metadata["Name"].lower().replace("_", "-"), distribution.version)
        for distribution in importlib.metadata.distributions()
        if distribution.metadata.get("Name")
    )
    value = {
        "implementation": platform.python_implementation(),
        "packages": packages,
        "python": platform.python_version(),
    }
    return len(packages), canonical_hash(value)


def validate_document(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    payload = dict(freeze)
    payload_hash = payload.pop("freeze_payload_sha256", None)
    if not HEX64.fullmatch(str(payload_hash or "")) or canonical_hash(payload) != payload_hash:
        errors.append("VALIDATION_FREEZE_PAYLOAD_HASH_MISMATCH")
    if (
        freeze.get("schema_version") != "1.0.0"
        or freeze.get("artifact_type") != "c_target_validation_pre_run_freeze"
        or freeze.get("freeze_id") != "CUMCM-2024-C-VALIDATION-001-PRE-RUN-FREEZE-001"
        or freeze.get("case_id") != CASE_ID
        or freeze.get("set_type") != "VALIDATION"
        or freeze.get("target_problem_type") != "C"
        or freeze.get("answer_state") != "SEALED"
        or freeze.get("reference_access") != "LOCKED"
        or freeze.get("contamination_status") != "NO_KNOWN_SOLUTION_OR_REFERENCE_EXPOSURE"
    ):
        errors.append("VALIDATION_FREEZE_HEADER_INVALID")
    skill = freeze.get("formal_skill", {})
    if (
        not isinstance(skill, dict)
        or skill.get("name") != "cumcm-modeling-evidence"
        or skill.get("version") != "0.2.0-competition-rc4"
        or skill.get("capability") != "COMPETITION_RC"
        or skill.get("architecture") != "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
        or skill.get("implementation_commit") != "297cad0a29c659b18484d4f3b67d69a942ad415c"
        or skill.get("release_commit") != "46e13d31a3d22fe12a2cffe65a52558da3ecfa82"
        or skill.get("release_delivery_commit") != "df5f6cf925ba3a8556f154446ae2778349f99dac"
        or skill.get("git_tree_sha1") != "d041ca38de030ae04813ef02dbe12f7f2b7a1c22"
    ):
        errors.append("VALIDATION_FREEZE_SKILL_INVALID")
    execution = freeze.get("execution_policy", {})
    if (
        not isinstance(execution, dict)
        or execution.get("one_shot") is not True
        or execution.get("maximum_wall_seconds") != 14400
        or execution.get("all_runs_must_be_actual") is not True
        or execution.get("baseline_required") is not True
        or execution.get("primary_candidate_required") is not True
        or execution.get("infeasible_final") != "PROHIBITED"
        or execution.get("nonconverged_final") != "PROHIBITED"
        or execution.get("formal_skill_mutation") != "PROHIBITED"
        or execution.get("result_driven_manual_repair") != "PROHIBITED"
        or execution.get("terminal_freeze_forbids_new_validation_runs") is not True
    ):
        errors.append("VALIDATION_FREEZE_EXECUTION_POLICY_INVALID")
    workspace = freeze.get("case_workspace", {})
    if (
        not isinstance(workspace, dict)
        or workspace.get("path") != ".cache/official_inputs/CUMCM-2024-C/validation_001"
        or workspace.get("case_state") != "CREATED"
        or workspace.get("initial_run_count") != 0
        or workspace.get("raw_inputs_git_ignored") is not True
        or not HEX64.fullmatch(str(workspace.get("case_state_sha256", "")))
    ):
        errors.append("VALIDATION_FREEZE_WORKSPACE_INVALID")
    worker = freeze.get("worker_context", {})
    if (
        not isinstance(worker, dict)
        or worker.get("freshness") != "FRESH_NATIVE_SUBAGENT_SESSION"
        or worker.get("write_scope") != "OWN_IGNORED_CASE_DIRECTORY_ONLY"
        or worker.get("formal_state_write") != "PROHIBITED"
        or worker.get("git_write") != "PROHIBITED"
        or worker.get("skill_write") != "PROHIBITED"
        or worker.get("peer_output_access") != "PROHIBITED"
        or "2024_C_SOLUTIONS" not in worker.get("forbidden_inputs", [])
        or "FROZEN_FORMAL_SKILL" not in worker.get("allowed_inputs", [])
    ):
        errors.append("VALIDATION_FREEZE_WORKER_CONTEXT_INVALID")
    protocol = freeze.get("worker_protocol", {})
    if (
        not isinstance(protocol, dict)
        or protocol.get("checkpoint") != "PRE_EXECUTION_CODE_GIT_BINDING"
        or protocol.get("checkpoint_maximum_count") != 1
        or protocol.get("checkpoint_prohibits_model_execution") is not True
        or protocol.get("checkpoint_allows_result_access") is not False
        or protocol.get("same_worker_must_resume") is not True
        or protocol.get("checkpoint_phase_a_stages") != EXPECTED_STAGES[:8]
    ):
        errors.append("VALIDATION_FREEZE_WORKER_PROTOCOL_INVALID")
    if freeze.get("required_stages") != EXPECTED_STAGES:
        errors.append("VALIDATION_FREEZE_STAGE_SET_INVALID")
    if len(freeze.get("hard_failures", [])) != 12:
        errors.append("VALIDATION_FREEZE_HARD_FAILURE_SET_INVALID")
    if len(freeze.get("pass_requirements", [])) != 12:
        errors.append("VALIDATION_FREEZE_PASS_REQUIREMENT_SET_INVALID")
    if len(freeze.get("inputs", [])) != 6:
        errors.append("VALIDATION_FREEZE_INPUT_SET_INVALID")
    return errors


def validate_bound_file(
    errors: list[str], freeze: dict[str, Any], key: str, expected_path: str
) -> None:
    record = freeze.get(key, {})
    if (
        not isinstance(record, dict)
        or record.get("path") != expected_path
        or not (ROOT / expected_path).is_file()
        or file_hash(ROOT / expected_path) != record.get("sha256")
    ):
        errors.append(f"VALIDATION_FREEZE_{key.upper()}_DRIFT")


def validate_workspace(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    workspace_record = freeze.get("case_workspace", {})
    workspace = ROOT / str(workspace_record.get("path", ""))
    state_path = workspace / "case_state.json"
    if not workspace.is_dir() or not state_path.is_file():
        return ["VALIDATION_FREEZE_WORKSPACE_MISSING"]
    state = load_json(state_path)
    if (
        state.get("case_id") != CASE_ID
        or state.get("state") != "CREATED"
        or state.get("skill_version") != "0.2.0-competition-rc4"
        or file_hash(state_path) != workspace_record.get("case_state_sha256")
    ):
        errors.append("VALIDATION_FREEZE_CASE_STATE_DRIFT")
    run_files = list((workspace / "runs").glob("**/*")) if (workspace / "runs").exists() else []
    if any(path.is_file() for path in run_files):
        errors.append("VALIDATION_FREEZE_INITIAL_RUNS_NOT_EMPTY")
    expected = {
        item.get("path"): item.get("sha256")
        for item in freeze.get("inputs", [])
        if isinstance(item, dict)
    }
    for relative, expected_hash in expected.items():
        input_path = workspace / str(relative)
        if not input_path.is_file() or file_hash(input_path) != expected_hash:
            errors.append(f"VALIDATION_FREEZE_INPUT_DRIFT:{relative}")
    return errors


def evaluate(*, verify_workspace: bool, require_delivery: bool) -> dict[str, Any]:
    if not FREEZE_PATH.is_file():
        return {"error_count": 1, "errors": ["VALIDATION_FREEZE_MISSING"], "ok": False}
    freeze = load_json(FREEZE_PATH)
    errors = validate_document(freeze)
    validate_bound_file(
        errors,
        freeze,
        "input_registration",
        "evals/results/phase-004c-c-validation/input_registration.json",
    )
    validate_bound_file(
        errors, freeze, "validation_protocol", "rules/c_target_validation_protocol.yaml"
    )
    rubric = freeze.get("rubric", {})
    rubric_path = "evals/rubrics/phase-004c/CUMCM-2024-C-VALIDATION-001.yaml"
    if (
        not isinstance(rubric, dict)
        or rubric.get("path") != rubric_path
        or file_hash(ROOT / rubric_path) != rubric.get("sha256")
        or rubric.get("metric_count") != 25
        or rubric.get("result_independent") is not True
    ):
        errors.append("VALIDATION_FREEZE_RUBRIC_DRIFT")
    release = freeze.get("skill_release", {})
    for field, expected_path in (
        ("manifest", "evals/results/phase-004c-c-batch/rc4/skill_release.json"),
        ("delivery", "evals/results/phase-004c-c-batch/rc4/release_delivery.json"),
    ):
        if (
            not isinstance(release, dict)
            or release.get(f"{field}_path") != expected_path
            or file_hash(ROOT / expected_path) != release.get(f"{field}_sha256")
        ):
            errors.append(f"VALIDATION_FREEZE_SKILL_RELEASE_{field.upper()}_DRIFT")
    skill = freeze.get("formal_skill", {})
    runner = freeze.get("runner", {})
    release_commit = str(skill.get("release_commit", ""))
    runner_content = git_bytes("show", f"{release_commit}:{runner.get('path')}")
    tree_content = git_bytes("rev-parse", f"{release_commit}:{SKILL_ROOT}")
    if (
        runner_content is None
        or hashlib.sha256(runner_content).hexdigest() != runner.get("sha256")
        or tree_content is None
        or tree_content.decode().strip() != skill.get("git_tree_sha1")
    ):
        errors.append("VALIDATION_FREEZE_RELEASE_COMMIT_DRIFT")
    subject = str(freeze.get("subject_commit", ""))
    if not HEX40.fullmatch(subject) or git_bytes("cat-file", "-e", f"{subject}^{{commit}}") is None:
        errors.append("VALIDATION_FREEZE_SUBJECT_COMMIT_INVALID")
    registry_content = git_bytes("show", f"{subject}:benchmarks/case_registry.yaml")
    registry = (
        yaml.safe_load(registry_content.decode("utf-8")) if registry_content is not None else {}
    )
    matches = [
        item
        for item in registry.get("cases", [])
        if isinstance(item, dict) and item.get("case_id") == CASE_ID
    ]
    record = matches[0] if len(matches) == 1 else {}
    if (
        len(matches) != 1
        or record.get("set_type") != "VALIDATION"
        or record.get("evidence_role") != "STRICT_ONE_SHOT_VALIDATION"
        or record.get("answer_access_status") != "SEALED"
        or record.get("reference_unlock") != "LOCKED"
        or record.get("first_run_status") != "NOT_STARTED"
        or record.get("formal_skill_version") != "0.2.0-competition-rc4"
        or record.get("formal_skill_commit") != skill.get("release_commit")
        or record.get("input_registration", {}).get("sha256")
        != freeze.get("input_registration", {}).get("sha256")
    ):
        errors.append("VALIDATION_FREEZE_REGISTRY_DRIFT")
    tracked_cache = git_bytes("ls-files", ".cache")
    if tracked_cache is None or tracked_cache.strip():
        errors.append("VALIDATION_FREEZE_RAW_INPUT_TRACKING_INVALID")
    if verify_workspace:
        distribution_count, environment_hash = dependency_snapshot()
        environment = freeze.get("environment", {})
        dependency = (
            environment.get("dependency_snapshot", {}) if isinstance(environment, dict) else {}
        )
        if (
            platform.python_version() != environment.get("python")
            or platform.python_implementation() != environment.get("interpreter")
            or distribution_count != dependency.get("distribution_count")
            or environment_hash != dependency.get("canonical_sha256")
            or file_hash(ROOT / "pyproject.toml") != environment.get("pyproject_sha256")
        ):
            errors.append("VALIDATION_FREEZE_ENVIRONMENT_DRIFT")
        errors.extend(validate_workspace(freeze))
    if require_delivery:
        if not RECEIPT_PATH.is_file():
            errors.append("VALIDATION_FREEZE_DELIVERY_MISSING")
        else:
            receipt = load_json(RECEIPT_PATH)
            if (
                receipt.get("status") != "REMOTE_DELIVERED"
                or receipt.get("freeze_id") != freeze.get("freeze_id")
                or receipt.get("freeze_file_sha256") != file_hash(FREEZE_PATH)
                or receipt.get("freeze_payload_sha256") != freeze.get("freeze_payload_sha256")
                or receipt.get("subject_commit") != subject
                or receipt.get("freeze_commit") != receipt.get("remote_sha")
            ):
                errors.append("VALIDATION_FREEZE_DELIVERY_INVALID")
        current_registry = load_yaml(REGISTRY_PATH)
        current_matches = [
            item
            for item in current_registry.get("cases", [])
            if isinstance(item, dict) and item.get("case_id") == CASE_ID
        ]
        current_record = current_matches[0] if len(current_matches) == 1 else {}
        current_pre_run_freeze = current_record.get("pre_run_freeze", {})
        current_first_run_status = current_record.get("first_run_status")
        current_first_run_freeze = current_record.get("first_run_freeze")
        if (
            len(current_matches) != 1
            or current_record.get("answer_access_status") != "SEALED"
            or current_record.get("reference_unlock") != "LOCKED"
            or current_first_run_status not in {"IN_PROGRESS", "FROZEN"}
            or (current_first_run_status == "IN_PROGRESS" and current_first_run_freeze is not None)
            or (
                current_first_run_status == "FROZEN"
                and not isinstance(current_first_run_freeze, dict)
            )
            or not current_record.get("start_time")
            or not isinstance(current_pre_run_freeze, dict)
            or current_pre_run_freeze.get("freeze_id") != freeze.get("freeze_id")
            or current_pre_run_freeze.get("path") != str(FREEZE_PATH.relative_to(ROOT))
            or current_pre_run_freeze.get("sha256") != file_hash(FREEZE_PATH)
            or current_pre_run_freeze.get("payload_sha256") != freeze.get("freeze_payload_sha256")
            or current_pre_run_freeze.get("freeze_commit")
            != "e45d0679d1f129496fedcd8eaf8b0823e4543ce1"
            or current_pre_run_freeze.get("remote_sha")
            != "e45d0679d1f129496fedcd8eaf8b0823e4543ce1"
            or current_pre_run_freeze.get("status") != "REMOTE_DELIVERED"
        ):
            errors.append("VALIDATION_FREEZE_CURRENT_REGISTRY_INVALID")
    errors = sorted(set(errors))
    return {
        "case_id": freeze.get("case_id"),
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
