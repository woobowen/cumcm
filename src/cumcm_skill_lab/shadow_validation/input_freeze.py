"""Build and verify the immutable Phase 002D-R3 implementation input freeze."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .io import file_sha256, read_json, sha256_bytes, sha256_json, tree_hash, write_json_atomic

FREEZE_PATH = Path("evals/results/phase-002d-r3/input_freeze_manifest.json")
FREEZE_ID = "PHASE-002D-R3-INPUT-FREEZE-001"
CREATED_AT = "2026-09-03T21:20:00+08:00"
EXPECTED_BRANCH = "feat/phase002d-r3-shadow-validation"
AUTHORIZATION_PATH = Path(
    "evals/results/phase-002d-r2a-c1/authorization_decision/authorization-c2.json"
)
FROZEN_FILES = (
    AUTHORIZATION_PATH.as_posix(),
    "specifications/shadow_prototype_scope.yaml",
    "specifications/components/accepted-versus-done-workflow-state.yaml",
    "specifications/components/claim-evidence-support-gate.yaml",
    "specifications/components/hash-bound-reproducibility-manifest.yaml",
    "specifications/components/leakage-safe-model-comparison-gate.yaml",
    "specifications/interactions/component_interaction_contract.yaml",
    "specifications/architectures/architecture_candidate_set.yaml",
    "evals/prospective/phase-002d-r2/public_conformance/cases.json",
    "evals/prospective/phase-002d-r2/manifests/public_manifest.json",
    "evals/prospective/phase-002d-r2/sealed_manifest.json",
    "evals/prospective/phase-002d-r2/manifests/oracle_commitments.json",
    "evals/prospective/phase-002d-r2/metric_registry.yaml",
    "evals/prospective/phase-002d-r2/threshold_policy.yaml",
    "evals/prospective/phase-002d-r2/prospective_experiment_protocol.yaml",
    "evals/prospective/phase-002d-r2/ablation_policy.yaml",
    "evals/prospective/phase-002d-r2/access_policy.yaml",
)
ENGINE_FILES = (
    "src/cumcm_skill_lab/shadow_validation/runner.py",
    "src/cumcm_skill_lab/shadow_validation/scorer.py",
    "src/cumcm_skill_lab/shadow_validation/grader.py",
)
HISTORICAL_ROOTS = tuple(
    Path("evals/results") / name
    for name in (
        "phase-002",
        "phase-002a",
        "phase-002b",
        "phase-002c",
        "phase-002d",
        "phase-002d-r1",
        "phase-002d-r2",
        "phase-002d-r2a",
        "phase-002d-r2a-c1",
    )
)
FORMAL_SKILL_ROOT = Path(".agents/skills/cumcm-modeling-evidence")


def _git(root: Path, *arguments: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=not binary
    )
    return result.stdout if binary else result.stdout.strip()


def _file_hashes(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {path: file_sha256(root / path) for path in paths}


def build_input_freeze(root: Path, *, subject_commit: str | None = None) -> dict[str, Any]:
    commit = subject_commit or str(_git(root, "rev-parse", "HEAD"))
    branch = str(_git(root, "branch", "--show-current"))
    if branch != EXPECTED_BRANCH:
        raise ValueError(f"R3_BRANCH_MISMATCH:{branch}")
    authorization = read_json(root / AUTHORIZATION_PATH)
    if (
        authorization.get("authorization_id")
        != "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C2"
        or authorization.get("decision") != "AUTOMATED_ACCEPTED"
        or authorization.get("accepted_scope") != "EXPERIMENTAL_SHADOW_PROTOTYPE_ONLY"
    ):
        raise ValueError("R3_AUTHORIZATION_SCOPE_BLOCKED")
    state_bytes = _git(root, "show", f"{commit}:state/project_state.json", binary=True)
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "freeze_id": FREEZE_ID,
        "phase": "PHASE-EVIDENCE-EXPANSION-002D",
        "subphase": "PHASE-002D-R3-SHADOW-PROTOTYPE-VALIDATION",
        "created_at": CREATED_AT,
        "subject_commit": commit,
        "branch": EXPECTED_BRANCH,
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": authorization["authorization_hash"],
        "accepted_scope": authorization["accepted_scope"],
        "frozen_file_hashes": _file_hashes(root, FROZEN_FILES),
        "engine_file_hashes": _file_hashes(root, ENGINE_FILES),
        "historical_tree_hashes": {
            path.as_posix(): tree_hash(root, path) for path in HISTORICAL_ROOTS
        },
        "formal_skill_tree_hash": tree_hash(root, FORMAL_SKILL_ROOT),
        "state_snapshot": {
            "commit": commit,
            "sha256": sha256_bytes(
                state_bytes if isinstance(state_bytes, bytes) else state_bytes.encode()
            ),
        },
        "architecture_ids": [
            "ARCH-S0-RETAIN-SCAFFOLD-ONLY",
            "ARCH-W1-WORKFLOW-ONLY-GUARDS",
            "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL",
        ],
        "component_ids": [
            "accepted-versus-done-workflow-state",
            "claim-evidence-support-gate",
            "hash-bound-reproducibility-manifest",
            "leakage-safe-model-comparison-gate",
        ],
        "hidden_values_read": False,
        "third_party_code_executed": False,
    }
    body["manifest_hash"] = sha256_json(body)
    return body


def verify_input_freeze(root: Path) -> list[str]:
    path = root / FREEZE_PATH
    if not path.is_file():
        return ["R3_INPUT_FREEZE_MISSING"]
    manifest = read_json(path)
    errors: list[str] = []
    body = dict(manifest)
    recorded = body.pop("manifest_hash", None)
    if sha256_json(body) != recorded:
        errors.append("R3_INPUT_FREEZE_HASH_MISMATCH")
    if manifest.get("branch") != EXPECTED_BRANCH:
        errors.append("R3_INPUT_FREEZE_BRANCH_MISMATCH")
    for group in ("frozen_file_hashes", "engine_file_hashes"):
        for relative, expected in manifest.get(group, {}).items():
            path = root / relative
            if not path.is_file() or file_sha256(path) != expected:
                errors.append(f"R3_FROZEN_FILE_MUTATED:{relative}")
    for relative, expected in manifest.get("historical_tree_hashes", {}).items():
        if tree_hash(root, Path(relative)) != expected:
            errors.append(f"R3_HISTORICAL_TREE_MUTATED:{relative}")
    if tree_hash(root, FORMAL_SKILL_ROOT) != manifest.get("formal_skill_tree_hash"):
        errors.append("R3_FORMAL_SKILL_TREE_MUTATED")
    commit = manifest.get("state_snapshot", {}).get("commit")
    try:
        state_bytes = _git(root, "show", f"{commit}:state/project_state.json", binary=True)
    except subprocess.CalledProcessError:
        errors.append("R3_STATE_SNAPSHOT_COMMIT_MISSING")
    else:
        digest = sha256_bytes(
            state_bytes if isinstance(state_bytes, bytes) else state_bytes.encode()
        )
        if digest != manifest.get("state_snapshot", {}).get("sha256"):
            errors.append("R3_STATE_SNAPSHOT_HASH_MISMATCH")
    if manifest.get("hidden_values_read") is not False:
        errors.append("R3_HIDDEN_VALUE_DISCIPLINE_VIOLATION")
    return sorted(set(errors))


def write_input_freeze(root: Path, *, subject_commit: str | None = None) -> dict[str, Any]:
    artifact = build_input_freeze(root, subject_commit=subject_commit)
    write_json_atomic(root / FREEZE_PATH, artifact)
    return artifact


__all__ = [
    "EXPECTED_BRANCH",
    "FREEZE_ID",
    "FREEZE_PATH",
    "build_input_freeze",
    "verify_input_freeze",
    "write_input_freeze",
]
