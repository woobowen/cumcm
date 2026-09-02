"""Freeze and verify the Phase 002D-R2 implementation embargo."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import check_or_write, file_sha256, read_json, sha256_json

from .models import RESULT_ROOT, SUBJECT_COMMIT, file_hashes, tree_hash

EMBARGO_PATH = RESULT_ROOT / "implementation_embargo.json"
EMBARGO_ID = "PHASE-002D-R2-IMPLEMENTATION-EMBARGO-001"
CREATED_AT = "2026-09-02T13:02:23+08:00"
FORMAL_SKILL_ROOT = Path(".agents/skills/cumcm-modeling-evidence")
SRC_ROOT = Path("src/cumcm_skill_lab")
ALLOWED_PREFIXES = ("src/cumcm_skill_lab/specification/",)
PROHIBITED_PREFIXES = (
    "experiments/shadow_prototypes/",
    "src/cumcm_skill_lab/components/",
)


def _subject_tree_id(root: Path, relative: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", f"{SUBJECT_COMMIT}:{relative}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_embargo(root: Path) -> dict[str, Any]:
    skill_hashes = file_hashes(root, FORMAL_SKILL_ROOT)
    protected_src = file_hashes(root, SRC_ROOT, excluded_prefixes=ALLOWED_PREFIXES)
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "embargo_id": EMBARGO_ID,
        "phase": "PHASE-EVIDENCE-EXPANSION-002D",
        "subphase": "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL",
        "subject_commit": SUBJECT_COMMIT,
        "embargo_effective_at": CREATED_AT,
        "formal_skill_path": FORMAL_SKILL_ROOT.as_posix(),
        "formal_skill_tree_hash": tree_hash(skill_hashes),
        "formal_skill_file_hashes": skill_hashes,
        "subject_commit_src_git_tree": _subject_tree_id(root, SRC_ROOT.as_posix()),
        "protected_src_tree_hash": tree_hash(protected_src),
        "protected_src_file_hashes": protected_src,
        "allowed_specification_validator_prefixes": list(ALLOWED_PREFIXES),
        "prohibited_prototype_prefixes": list(PROHIBITED_PREFIXES),
        "prohibited_formal_skill_modification": True,
        "prohibited_component_implementation": True,
        "prohibited_shadow_prototype_execution": True,
        "embargo_release_condition": (
            "AUDITED_AUTOMATED_ACCEPTED:DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2"
        ),
        "is_component_implementation": False,
        "is_shadow_prototype": False,
    }
    body["embargo_hash"] = sha256_json(body)
    return body


def verify_embargo(root: Path, embargo: dict[str, Any] | None = None) -> list[str]:
    if embargo is None:
        if not (root / EMBARGO_PATH).is_file():
            return ["IMPLEMENTATION_EMBARGO_MISSING"]
        embargo = read_json(root / EMBARGO_PATH)
    errors: list[str] = []
    body = dict(embargo)
    recorded_hash = body.pop("embargo_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("IMPLEMENTATION_EMBARGO_HASH_MISMATCH")
    for relative, expected in embargo.get("formal_skill_file_hashes", {}).items():
        path = root / relative
        if not path.is_file() or file_sha256(path) != expected:
            errors.append(f"FORMAL_SKILL_EMBARGO_VIOLATION:{relative}")
    current_skill = file_hashes(root, FORMAL_SKILL_ROOT)
    if set(current_skill) != set(embargo.get("formal_skill_file_hashes", {})):
        errors.append("FORMAL_SKILL_TREE_MEMBERSHIP_CHANGED")
    protected = embargo.get("protected_src_file_hashes", {})
    current_protected = file_hashes(root, SRC_ROOT, excluded_prefixes=ALLOWED_PREFIXES)
    if current_protected != protected:
        errors.append("PROTECTED_SRC_TREE_CHANGED")
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    worktree_paths = [
        path.relative_to(root).as_posix()
        for prefix in PROHIBITED_PREFIXES
        if (root / prefix).exists()
        for path in (root / prefix).rglob("*")
        if path.is_file()
    ]
    for relative in sorted(set(tracked + worktree_paths)):
        if any(relative.startswith(prefix) for prefix in PROHIBITED_PREFIXES):
            errors.append(f"PROHIBITED_IMPLEMENTATION_DETECTED:{relative}")
    return sorted(set(errors))


def check_or_write_embargo(root: Path, *, check: bool) -> dict[str, Any]:
    if check:
        embargo = read_json(root / EMBARGO_PATH) if (root / EMBARGO_PATH).is_file() else None
        errors = verify_embargo(root, embargo)
    else:
        embargo = build_embargo(root)
        errors = check_or_write(root / EMBARGO_PATH, embargo, check=False)
        errors.extend(verify_embargo(root, embargo))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "embargo_id": embargo.get("embargo_id") if embargo else None,
        "embargo_hash": embargo.get("embargo_hash") if embargo else None,
        "formal_skill_tree_hash": embargo.get("formal_skill_tree_hash") if embargo else None,
    }


__all__ = ["EMBARGO_ID", "EMBARGO_PATH", "check_or_write_embargo", "verify_embargo"]
