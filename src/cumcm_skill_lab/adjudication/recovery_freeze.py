"""Freeze Phase 002B adjudication inputs at the recovery subject commit."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .models import check_or_write, file_sha256, read_json, read_yaml, sha256_bytes, sha256_json

SUBJECT_COMMIT = "e7438da1d48a6c76c5859e3b8c232e344f35f364"
MANIFEST_PATH = Path("evals/results/phase-002b/input_freeze_manifest.json")
POLICY_PATH = "adjudication/policies/phase-002a.yaml"
CONFIG_PATH = "adjudication/configs/phase-002a.yaml"

IMMUTABLE_PREFIXES = (
    "evals/results/phase-002/",
    "evals/results/phase-002a/evidence_freeze_manifest.json",
    "evals/results/phase-002a/eligibility/",
    "evals/results/phase-002a/structured_coverage/",
    "evals/results/phase-002a/oracle_correctness/",
    "evals/results/phase-002a/process_evidence/",
    "evals/results/phase-002a/recovery_gap_evidence/",
    "evals/results/phase-002a/adversarial/",
    "evals/results/phase-002a/runtime/",
    "evals/results/phase-002a/dissent/dissent-real-001.json",
    "evals/results/phase-002a/anonymous_evidence_bundle.json",
)

ROLE_SCHEMAS = (
    "contracts/judge_decision.schema.json",
    "contracts/dissent_record.schema.json",
    "contracts/meta_adjudication.schema.json",
    "contracts/decision_audit.schema.json",
    "contracts/automated_decision.schema.json",
)

POLICY_INPUTS = (
    CONFIG_PATH,
    POLICY_PATH,
    "rules/evidence_hierarchy.yaml",
    "rules/automated_adjudication_rules.yaml",
    "rules/team_compliance_rules.yaml",
)

LEGACY_RUNNERS = (
    "src/cumcm_skill_lab/adjudication/judge_runner.py",
    "scripts/run_blind_adjudication.py",
    "scripts/run_meta_adjudication.py",
    "scripts/audit_automated_decision.py",
    "scripts/replay_automated_decision.py",
)

PREVIOUS_FAILURES = tuple(
    f"evals/results/phase-002a/runtime/blind_failure_{index:03d}.json" for index in range(1, 4)
)


def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=text)
    return result.stdout


def _subject_paths(root: Path) -> list[str]:
    output = _git(root, "ls-tree", "-r", "--name-only", SUBJECT_COMMIT)
    assert isinstance(output, str)
    return sorted(
        path
        for path in output.splitlines()
        if any(path == prefix or path.startswith(prefix) for prefix in IMMUTABLE_PREFIXES)
    )


def _subject_bytes(root: Path, relative: str) -> bytes:
    output = _git(root, "show", f"{SUBJECT_COMMIT}:{relative}", text=False)
    assert isinstance(output, bytes)
    return output


def _subject_hashes(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {relative: sha256_bytes(_subject_bytes(root, relative)) for relative in paths}


def build_manifest(root: Path) -> dict:
    immutable_files = {
        relative: {
            "sha256": sha256_bytes(_subject_bytes(root, relative)),
            "immutable": True,
        }
        for relative in _subject_paths(root)
    }
    config = read_yaml(root / CONFIG_PATH)
    policy = read_yaml(root / POLICY_PATH)
    role_schema_hashes = _subject_hashes(root, ROLE_SCHEMAS)
    policy_input_hashes = _subject_hashes(root, POLICY_INPUTS)
    previous_failure_hashes = _subject_hashes(root, PREVIOUS_FAILURES)
    legacy_runner_hashes = _subject_hashes(root, LEGACY_RUNNERS)
    evidence_hash = sha256_json(
        {
            relative: record["sha256"]
            for relative, record in immutable_files.items()
            if relative.startswith(("evals/results/phase-002/", "evals/results/phase-002a/"))
        }
    )
    body = {
        "schema_version": "1.0.0",
        "freeze_id": "PHASE-002B-ADJUDICATION-INPUT-FREEZE",
        "subject_commit": SUBJECT_COMMIT,
        "immutable_files": immutable_files,
        "immutable_file_count": len(immutable_files),
        "policy_hash": policy["policy_hash"],
        "policy_input_hashes": policy_input_hashes,
        "evidence_hash": evidence_hash,
        "role_schema_hashes": role_schema_hashes,
        "model_config": {
            "model": config["model"],
            "reasoning_setting": config["reasoning_setting"],
            "sandbox": config["sandbox"],
            "network_isolation_level": config["network_isolation_level"],
        },
        "legacy_runner_hashes_at_subject": legacy_runner_hashes,
        "previous_failed_attempt_hashes": previous_failure_hashes,
        "excluded_unblinded_dissent": {
            "path": "evals/results/phase-002a/dissent/dissent-real-001.json",
            "ranking_eligible": False,
            "formal_role_eligible": False,
        },
    }
    body["freeze_hash"] = sha256_json(body)
    return body


def verify_manifest(root: Path, manifest: dict | None = None) -> list[str]:
    manifest = manifest or read_json(root / MANIFEST_PATH)
    errors: list[str] = []
    if manifest.get("subject_commit") != SUBJECT_COMMIT:
        errors.append("SUBJECT_COMMIT_MISMATCH")
    expected_paths = _subject_paths(root)
    if sorted(manifest.get("immutable_files", {})) != expected_paths:
        errors.append("INPUT_SET_MISMATCH")
    for relative, record in manifest.get("immutable_files", {}).items():
        path = root / relative
        if not path.is_file():
            errors.append(f"INPUT_MISSING:{relative}")
        elif file_sha256(path) != record.get("sha256"):
            errors.append(f"INPUT_FREEZE_BROKEN:{relative}")
    body = dict(manifest)
    recorded_hash = body.pop("freeze_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("FREEZE_HASH_MISMATCH")
    if manifest.get("policy_hash") != read_yaml(root / POLICY_PATH).get("policy_hash"):
        errors.append("POLICY_HASH_MISMATCH")
    if manifest.get("role_schema_hashes") != _subject_hashes(root, ROLE_SCHEMAS):
        errors.append("ROLE_SCHEMA_HASH_MISMATCH")
    if manifest.get("previous_failed_attempt_hashes") != _subject_hashes(root, PREVIOUS_FAILURES):
        errors.append("PREVIOUS_FAILURE_HASH_MISMATCH")
    return errors


def freeze(root: Path, *, check: bool) -> dict:
    manifest = build_manifest(root)
    errors = verify_manifest(root, manifest)
    if not errors:
        errors.extend(check_or_write(root / MANIFEST_PATH, manifest, check=check))
    return {
        "status": "PASS" if not errors else "INPUT_FREEZE_BROKEN",
        "freeze_hash": manifest["freeze_hash"],
        "evidence_hash": manifest["evidence_hash"],
        "immutable_file_count": manifest["immutable_file_count"],
        "errors": errors,
    }
