#!/usr/bin/env python3
"""Check the immutable C-target batch pre-run freeze without reading ignored inputs."""

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
FREEZE_PATH = ROOT / "evals/results/phase-004c-c-batch/batch_pre_run_freeze.json"
REGISTRY_PATH = ROOT / "benchmarks/case_registry.yaml"
STATE_PATH = ROOT / "state/project_state.json"
RECEIPT_PATH = ROOT / "evals/results/phase-004c-c-batch/batch_freeze_delivery_receipt.json"
EXPECTED_CASES = [
    "CUMCM-2022-C-DEVELOPMENT-BATCH-001",
    "CUMCM-2021-C-DEVELOPMENT-BATCH-002",
    "CUMCM-2020-C-DEVELOPMENT-BATCH-003",
]
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def git_bytes(root: Path, *arguments: str) -> bytes | None:
    completed = subprocess.run(["git", *arguments], cwd=root, check=False, capture_output=True)
    return completed.stdout if completed.returncode == 0 else None


def validate_document(freeze: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    payload = dict(freeze)
    payload_hash = payload.pop("freeze_payload_sha256", None)
    if not HEX64.fullmatch(str(payload_hash or "")) or canonical_hash(payload) != payload_hash:
        errors.append("BATCH_FREEZE_PAYLOAD_HASH_MISMATCH")
    if (
        freeze.get("schema_version") != "1.0.0"
        or freeze.get("artifact_type") != "c_target_batch_pre_run_freeze"
        or freeze.get("freeze_id") != "C-TARGET-BATCH-001-PRE-RUN-FREEZE-001"
        or freeze.get("batch_id") != "C-TARGET-BATCH-001"
        or freeze.get("batch_skill_frozen") is not True
        or freeze.get("batch_reference_unlocked") is not False
        or freeze.get("answer_states") != ["SEALED", "SEALED", "SEALED"]
        or freeze.get("case_order") != EXPECTED_CASES
        or freeze.get("raw_inputs_git_ignored") is not True
    ):
        errors.append("BATCH_FREEZE_HEADER_INVALID")
    skill = freeze.get("formal_skill", {})
    if (
        not isinstance(skill, dict)
        or skill.get("name") != "cumcm-modeling-evidence"
        or skill.get("version") != "0.2.0-competition-rc3"
        or skill.get("capability") != "COMPETITION_RC"
        or skill.get("architecture") != "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
        or skill.get("commit") != "8a2a813ff34d8c2701c64ff9d959848e7b88c27c"
        or skill.get("git_tree_sha1") != "a4551c8aa0b6b119823f6ce9df3f0f948339bb33"
        or not HEX64.fullmatch(str(skill.get("deterministic_listing_sha256", "")))
    ):
        errors.append("BATCH_FREEZE_SKILL_INVALID")
    cases = freeze.get("cases")
    if not isinstance(cases, list) or len(cases) != 3:
        errors.append("BATCH_FREEZE_CASE_SET_INVALID")
        cases = []
    for position, case_id in enumerate(EXPECTED_CASES, 1):
        matches = [
            item for item in cases if isinstance(item, dict) and item.get("case_id") == case_id
        ]
        if len(matches) != 1:
            errors.append(f"BATCH_FREEZE_CASE_MISSING:{case_id}")
            continue
        item = matches[0]
        if (
            item.get("batch_position") != position
            or item.get("set_type") != "DEVELOPMENT"
            or item.get("answer_state") != "SEALED"
            or item.get("reference_unlock") != "LOCKED"
            or item.get("first_run_status") != "IN_PROGRESS"
            or item.get("case_state") != "CREATED"
            or item.get("timebox_seconds") != 10800
            or item.get("model_prior_status") != "MODEL_PRIOR_EXPOSURE_UNVERIFIABLE"
            or item.get("strict_first_run_eligibility") != "ELIGIBLE_MODEL_PRIOR_UNVERIFIABLE"
            or not HEX64.fullmatch(str(item.get("official_archive_sha256", "")))
            or not HEX64.fullmatch(str(item.get("problem_hash", "")))
            or not HEX64.fullmatch(str(item.get("case_state_sha256", "")))
            or not HEX64.fullmatch(str(item.get("search_log_sha256", "")))
            or not isinstance(item.get("data_hashes"), dict)
            or not item.get("data_hashes")
        ):
            errors.append(f"BATCH_FREEZE_CASE_INVALID:{case_id}")
    parallelism = freeze.get("parallelism", {})
    if (
        not isinstance(parallelism, dict)
        or parallelism.get("maximum_concurrent_case_workers") != 2
        or parallelism.get("worker_write_scope") != "OWN_CASE_DIRECTORY_ONLY"
        or parallelism.get("peer_output_access") != "PROHIBITED"
        or parallelism.get("worktree_use") != "PROHIBITED"
        or parallelism.get("shared_state_writers") != ["modeling_orchestrator"]
    ):
        errors.append("BATCH_FREEZE_PARALLELISM_INVALID")
    if len(freeze.get("scoring_rubric", [])) != 25:
        errors.append("BATCH_FREEZE_RUBRIC_INVALID")
    if len(freeze.get("hard_failures", [])) != 11:
        errors.append("BATCH_FREEZE_HARD_FAILURE_SET_INVALID")
    if freeze.get("agent_roles") != [
        "modeling_orchestrator",
        "problem_and_model_analyst",
        "data_and_experiment_engineer",
        "adversarial_evidence_auditor",
    ]:
        errors.append("BATCH_FREEZE_ROLE_SET_INVALID")
    fallback = freeze.get("fallback_rule", {})
    if (
        not isinstance(fallback, dict)
        or fallback.get("case_id") != "CUMCM-2019-C-DEVELOPMENT-BATCH-003F"
        or fallback.get("decision") != "NOT_ACTIVATED"
    ):
        errors.append("BATCH_FREEZE_FALLBACK_DECISION_INVALID")
    return sorted(set(errors))


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    freeze_path = root / FREEZE_PATH.relative_to(ROOT)
    if not freeze_path.is_file():
        return {"error_count": 1, "errors": ["BATCH_FREEZE_MISSING"], "ok": False}
    freeze = load_json(freeze_path)
    errors.extend(validate_document(freeze))
    registry = load_yaml(root / REGISTRY_PATH.relative_to(ROOT))
    registered = {
        item.get("case_id"): item
        for item in registry.get("cases", [])
        if isinstance(item, dict) and item.get("case_id") in EXPECTED_CASES
    }
    for frozen in freeze.get("cases", []):
        if not isinstance(frozen, dict):
            continue
        case_id = frozen.get("case_id")
        record = registered.get(case_id, {})
        for registry_field, freeze_field in (
            ("problem_hash", "problem_hash"),
            ("data_hashes", "data_hashes"),
            ("official_package_sha256", "official_archive_sha256"),
            ("generalization_axis", "generalization_axis"),
            ("formal_skill_version", None),
            ("formal_skill_commit", None),
        ):
            expected = (
                "0.2.0-competition-rc3"
                if registry_field == "formal_skill_version"
                else "8a2a813ff34d8c2701c64ff9d959848e7b88c27c"
                if registry_field == "formal_skill_commit"
                else frozen.get(freeze_field)
            )
            if record.get(registry_field) != expected:
                errors.append(f"BATCH_FREEZE_REGISTRY_DRIFT:{case_id}:{registry_field}")
    subject = str(freeze.get("subject_commit", ""))
    if (
        not HEX40.fullmatch(subject)
        or git_bytes(root, "cat-file", "-e", f"{subject}^{{commit}}") is None
    ):
        errors.append("BATCH_FREEZE_SUBJECT_COMMIT_INVALID")
    input_registration = freeze.get("input_registration", {})
    input_registration_path = str(input_registration.get("path", ""))
    input_registration_content = git_bytes(root, "show", f"{subject}:{input_registration_path}")
    if (
        not isinstance(input_registration, dict)
        or input_registration_path != "evals/results/phase-004c-c-batch/input_registration.json"
        or input_registration_content is None
        or hashlib.sha256(input_registration_content).hexdigest()
        != input_registration.get("sha256")
    ):
        errors.append("BATCH_FREEZE_INPUT_REGISTRATION_DRIFT")
    for section, expected_path in (
        ("target_policy", "rules/target_problem_policy.yaml"),
        ("search_policy", "docs/SEARCH_POLICY.md"),
    ):
        record = freeze.get(section, {})
        content = git_bytes(root, "show", f"{subject}:{expected_path}")
        if (
            not isinstance(record, dict)
            or record.get("path") != expected_path
            or content is None
            or hashlib.sha256(content).hexdigest() != record.get("sha256")
        ):
            errors.append(f"BATCH_FREEZE_{section.upper()}_DRIFT")
    runner = freeze.get("runner", {})
    skill = freeze.get("formal_skill", {})
    if isinstance(runner, dict) and isinstance(skill, dict):
        content = git_bytes(root, "show", f"{skill.get('commit')}:{runner.get('path')}")
        if content is None or hashlib.sha256(content).hexdigest() != runner.get("sha256"):
            errors.append("BATCH_FREEZE_RUNNER_COMMIT_DRIFT")
        tree = git_bytes(
            root, "rev-parse", f"{skill.get('commit')}:{'.agents/skills/cumcm-modeling-evidence'}"
        )
        if tree is None or tree.decode().strip() != skill.get("git_tree_sha1"):
            errors.append("BATCH_FREEZE_SKILL_TREE_COMMIT_DRIFT")
    state = load_json(root / STATE_PATH.relative_to(ROOT))
    state_freeze = state.get("batch_pre_run_freeze", {})
    receipt = load_json(root / RECEIPT_PATH.relative_to(ROOT))
    if (
        state.get("phase")
        not in {
            "PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C",
            "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C2",
            "PHASE-SKILL-C-TARGET-EVIDENCE-REPAIR-004C3",
        }
        or state.get("current_batch_id") != "C-TARGET-BATCH-001"
        or not isinstance(state_freeze, dict)
        or state_freeze.get("freeze_id") != freeze.get("freeze_id")
        or state_freeze.get("file_sha256") != file_hash(freeze_path)
        or state_freeze.get("payload_sha256") != freeze.get("freeze_payload_sha256")
        or state_freeze.get("status") != "REMOTE_DELIVERED"
        or state_freeze.get("freeze_commit") != state_freeze.get("remote_sha")
    ):
        errors.append("BATCH_FREEZE_PROJECT_STATE_DRIFT")
    if (
        receipt.get("status") != "REMOTE_DELIVERED"
        or receipt.get("freeze_id") != freeze.get("freeze_id")
        or receipt.get("freeze_file_sha256") != file_hash(freeze_path)
        or receipt.get("freeze_payload_sha256") != freeze.get("freeze_payload_sha256")
        or receipt.get("freeze_commit") != state_freeze.get("freeze_commit")
        or receipt.get("remote_sha") != state_freeze.get("remote_sha")
        or receipt.get("subject_commit") != freeze.get("subject_commit")
    ):
        errors.append("BATCH_FREEZE_DELIVERY_RECEIPT_INVALID")
    return {
        "batch_id": freeze.get("batch_id"),
        "case_count": len(freeze.get("cases", [])),
        "error_count": len(set(errors)),
        "errors": sorted(set(errors)),
        "freeze_payload_sha256": freeze.get("freeze_payload_sha256"),
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    result = evaluate()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
