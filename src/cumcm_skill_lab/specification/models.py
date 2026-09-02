"""Shared deterministic helpers and the Phase 002D-R2 historical input freeze."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    file_sha256,
    read_json,
    sha256_bytes,
    sha256_json,
)

RESULT_ROOT = Path("evals/results/phase-002d-r2")
FREEZE_PATH = RESULT_ROOT / "input_freeze_manifest.json"
FREEZE_ID = "PHASE-002D-R2-INPUT-FREEZE-001"
SUBJECT_COMMIT = "10073a2fe5b1512a16ab9a9c7907fb2b7f5ff765"
CREATED_AT = "2026-09-02T13:02:23+08:00"
HISTORICAL_ROOTS = tuple(
    Path(f"evals/results/{name}")
    for name in (
        "phase-002",
        "phase-002a",
        "phase-002b",
        "phase-002c",
        "phase-002d",
        "phase-002d-r1",
    )
)
COMPONENT_IDS = (
    "accepted-versus-done-workflow-state",
    "claim-evidence-support-gate",
    "hash-bound-reproducibility-manifest",
    "leakage-safe-model-comparison-gate",
)
FROZEN_CONTRACT_INPUTS = (
    "contracts/automated_decision.schema.json",
    "contracts/decision_audit.schema.json",
    "contracts/failure_aware_decision.schema.json",
    "contracts/project_state.schema.json",
    "contracts/test_evidence.schema.json",
    "contracts/test_request.schema.json",
)
FROZEN_RULE_INPUTS = (
    "rules/automated_adjudication_rules.yaml",
    "rules/evidence_hierarchy.yaml",
    "rules/evidence_rules.yaml",
    "rules/native_subagent_audit_rules.yaml",
    "rules/phase002d_r1_workflow_rules.yaml",
    "rules/phase002d_r2_workflow_rules.yaml",
)


def file_hashes(
    root: Path, relative: Path, *, excluded_prefixes: tuple[str, ...] = ()
) -> dict[str, str]:
    """Return stable repository-relative SHA-256 hashes for a tree."""
    values: dict[str, str] = {}
    for path in sorted((root / relative).rglob("*")):
        if not path.is_file() or path.name.endswith((".pyc", ".pyo")):
            continue
        key = path.relative_to(root).as_posix()
        if any(key.startswith(prefix) for prefix in excluded_prefixes):
            continue
        values[key] = file_sha256(path)
    return values


def tree_hash(values: dict[str, str]) -> str:
    return sha256_json(values)


def _git_file_sha256(root: Path, commit: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return sha256_bytes(result.stdout)


def _codex_version(root: Path) -> str:
    result = subprocess.run(
        ["codex", "--version"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _selected_hashes(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    return {path: file_sha256(root / path) for path in paths}


def build_input_freeze(root: Path) -> dict[str, Any]:
    r1_root = root / "evals/results/phase-002d-r1"
    r1_freeze = read_json(r1_root / "input_freeze_manifest.json")
    state = read_json(root / "state/project_state.json")
    direct_rejection = read_json(
        root / "evals/results/phase-002c/automated_decisions/direct_upstream_adoption.json"
    )
    architecture = read_json(r1_root / "automated_decisions/architecture.json")
    decision_paths = tuple(
        path.relative_to(root).as_posix()
        for path in sorted((r1_root / "automated_decisions").glob("*.json"))
    )
    component_card_paths = tuple(
        path.relative_to(root).as_posix()
        for path in sorted((root / "research/upstream_candidates/component_cards").glob("*.yaml"))
    )
    historical_hashes = {
        path.as_posix(): tree_hash(file_hashes(root, path)) for path in HISTORICAL_ROOTS
    }
    source_hashes = file_hashes(root, Path("src/cumcm_skill_lab/failure_aware"))
    formal_skill_hashes = file_hashes(root, Path(".agents/skills/cumcm-modeling-evidence"))
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "freeze_id": FREEZE_ID,
        "phase": "PHASE-EVIDENCE-EXPANSION-002D",
        "subphase": "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL",
        "created_at": CREATED_AT,
        "subject_commit": SUBJECT_COMMIT,
        "current_git_commit_at_freeze": SUBJECT_COMMIT,
        "current_state_subject_commit": SUBJECT_COMMIT,
        "current_state_subject_sha256": _git_file_sha256(
            root, SUBJECT_COMMIT, "state/project_state.json"
        ),
        "project_version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "codex_version": _codex_version(root),
        "phase002d_r1_freeze_id": r1_freeze["freeze_id"],
        "phase002d_r1_freeze_hash": r1_freeze["manifest_hash"],
        "phase002d_r1_automated_decision_hashes": _selected_hashes(root, decision_paths),
        "phase002d_r1_decision_audit_hash": file_sha256(r1_root / "decision_audit/audit.json"),
        "phase002d_r1_replay_hash": file_sha256(r1_root / "replay/replay.json"),
        "accepted_component_specification_ids": list(COMPONENT_IDS),
        "direct_upstream_rejection_ids": sorted(direct_rejection["rejected_scope"]),
        "architecture_insufficiency_decision": {
            "decision_id": architecture["automated_decision"]["decision_id"],
            "decision": architecture["automated_decision"]["decision"],
            "accepted_scope": architecture["accepted_scope"],
            "file_hash": file_sha256(r1_root / "automated_decisions/architecture.json"),
        },
        "historical_component_card_hashes": _selected_hashes(root, component_card_paths),
        "historical_tree_hashes": historical_hashes,
        "formal_skill_tree_hash": tree_hash(formal_skill_hashes),
        "formal_skill_file_hashes": formal_skill_hashes,
        "source_input_hashes": source_hashes,
        "source_input_tree_hash": tree_hash(source_hashes),
        "contract_input_hashes": _selected_hashes(root, FROZEN_CONTRACT_INPUTS),
        "rule_input_hashes": _selected_hashes(root, FROZEN_RULE_INPUTS),
        "subagent_policy_hash": file_sha256(root / "rules/phase002d_r2_workflow_rules.yaml"),
        "selected_architecture": None,
        "base_selected": False,
        "third_party_integrated": False,
        "skill_capability_status": "SCAFFOLD_ONLY",
        "historical_inputs_immutable": True,
    }
    if tuple(state["accepted_component_specifications"]) != COMPONENT_IDS:
        raise ValueError("R2_ACCEPTED_COMPONENT_SET_MISMATCH")
    body["manifest_hash"] = sha256_json(body)
    return body


def verify_input_freeze(root: Path, manifest: dict[str, Any] | None = None) -> list[str]:
    if manifest is None:
        if not (root / FREEZE_PATH).is_file():
            return ["PHASE002D_R2_INPUT_FREEZE_MISSING"]
        manifest = read_json(root / FREEZE_PATH)
    errors: list[str] = []
    body = dict(manifest)
    recorded_hash = body.pop("manifest_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("PHASE002D_R2_MANIFEST_HASH_MISMATCH")
    if manifest.get("subject_commit") != SUBJECT_COMMIT:
        errors.append("PHASE002D_R2_SUBJECT_COMMIT_MISMATCH")
    if manifest.get("project_version") != (root / "VERSION").read_text(encoding="utf-8").strip():
        errors.append("PHASE002D_R2_PROJECT_VERSION_MISMATCH")
    for relative, expected in manifest.get("formal_skill_file_hashes", {}).items():
        path = root / relative
        if not path.is_file() or file_sha256(path) != expected:
            errors.append(f"FORMAL_SKILL_INPUT_MUTATED:{relative}")
    for group in (
        "phase002d_r1_automated_decision_hashes",
        "historical_component_card_hashes",
        "source_input_hashes",
        "contract_input_hashes",
        "rule_input_hashes",
    ):
        for relative, expected in manifest.get(group, {}).items():
            path = root / relative
            if not path.is_file() or file_sha256(path) != expected:
                errors.append(f"FROZEN_HASH_MISMATCH:{group}:{relative}")
    for relative, expected in manifest.get("historical_tree_hashes", {}).items():
        if tree_hash(file_hashes(root, Path(relative))) != expected:
            errors.append(f"HISTORICAL_INPUT_MUTATED:{relative}")
    subject_state = _git_file_sha256(root, SUBJECT_COMMIT, "state/project_state.json")
    if manifest.get("current_state_subject_sha256") != subject_state:
        errors.append("CURRENT_STATE_SUBJECT_HASH_MISMATCH")
    return sorted(set(errors))


def check_or_write_input_freeze(root: Path, *, check: bool) -> dict[str, Any]:
    if check:
        manifest = read_json(root / FREEZE_PATH) if (root / FREEZE_PATH).is_file() else None
        errors = verify_input_freeze(root, manifest)
    else:
        manifest = build_input_freeze(root)
        errors = check_or_write(root / FREEZE_PATH, manifest, check=False)
        errors.extend(verify_input_freeze(root, manifest))
    return {
        "status": "PASS" if not errors else "INPUT_FREEZE_BROKEN",
        "errors": errors,
        "freeze_id": manifest.get("freeze_id") if manifest else None,
        "manifest_hash": manifest.get("manifest_hash") if manifest else None,
        "subject_commit": manifest.get("subject_commit") if manifest else None,
    }


__all__ = [
    "COMPONENT_IDS",
    "FREEZE_ID",
    "FREEZE_PATH",
    "RESULT_ROOT",
    "SUBJECT_COMMIT",
    "check_or_write_input_freeze",
    "file_hashes",
    "tree_hash",
]
