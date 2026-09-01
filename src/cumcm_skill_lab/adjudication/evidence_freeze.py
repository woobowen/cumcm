"""Freeze and verify the immutable Phase 002 evidence set against its subject commit."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .models import check_or_write, file_sha256, read_json, sha256_bytes, sha256_json

SUBJECT_COMMIT = "6a046822c33bcdf8a6821a96333bc92720e764c0"
MANIFEST_PATH = Path("evals/results/phase-002a/evidence_freeze_manifest.json")
IMMUTABLE_PREFIXES = (
    "evals/cases/phase-002/",
    "evals/configs/phase-002.yaml",
    "evals/fixtures/phase-002/",
    "evals/results/phase-002/",
    "evals/rubrics/phase-002/",
    "research/upstream_candidates/component_cards/",
    "research/upstream_candidates/dynamic_evaluation.csv",
    "research/upstream_candidates/dynamic_reviews/",
    "reports/phase-002-acceptance.md",
    "reports/upstream_dynamic_eval.md",
    "reports/upstream_gap_matrix.md",
)
REFERENCE_PATHS = (
    "src/cumcm_skill_lab/eval/scoring.py",
    "src/cumcm_skill_lab/eval/reporting.py",
    "reports/base_selection_proposal.md",
    "reports/component_portfolio_proposal.md",
    "reports/human_gate_base_selection.md",
    "research/upstream_candidates/dynamic_reviews/base_selection_proposal.json",
    "research/upstream_candidates/dynamic_reviews/component_selection_proposal.json",
)


def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=text)
    return result.stdout


def _tracked_at_subject(root: Path) -> list[str]:
    output = _git(root, "ls-tree", "-r", "--name-only", SUBJECT_COMMIT)
    assert isinstance(output, str)
    return sorted(
        path
        for path in output.splitlines()
        if any(path == prefix or path.startswith(prefix) for prefix in IMMUTABLE_PREFIXES)
        and path not in REFERENCE_PATHS
    )


def _subject_bytes(root: Path, path: str) -> bytes:
    output = _git(root, "show", f"{SUBJECT_COMMIT}:{path}", text=False)
    assert isinstance(output, bytes)
    return output


def build_manifest(root: Path) -> dict:
    immutable: dict[str, dict] = {}
    for relative in _tracked_at_subject(root):
        current = root / relative
        subject_content = _subject_bytes(root, relative)
        immutable[relative] = {
            "subject_sha256": sha256_bytes(subject_content),
            "current_sha256": file_sha256(current) if current.is_file() else None,
            "immutable": True,
        }
    references: dict[str, dict] = {}
    for relative in REFERENCE_PATHS:
        subject_content = _subject_bytes(root, relative)
        references[relative] = {
            "subject_sha256": sha256_bytes(subject_content),
            "purpose": "historical implementation or superseded derived view",
            "immutable": False,
        }
    run_files = list((root / "evals/results/phase-002/runs").rglob("*.json"))
    runs = [read_json(path) for path in run_files]
    recovery_count = len(
        list((root / "evals/results/phase-002/recoveries").rglob("*.recovery.json"))
    )
    body = {
        "schema_version": "1.0.0",
        "freeze_id": "PHASE-002-EVIDENCE-FREEZE-002A",
        "subject_commit": SUBJECT_COMMIT,
        "immutable_files": immutable,
        "historical_references": references,
        "counts": {
            "run_attempts": len(runs),
            "completed": sum(item["completion_status"] == "COMPLETED" for item in runs),
            "failed": sum(item["completion_status"] == "FAILED" for item in runs),
            "recovery_affected": recovery_count,
        },
        "phase_002_score_frozen_at": read_json(root / "evals/results/phase-002/score_freeze.json")[
            "frozen_at"
        ],
        "phase_002_identity_revealed_at": read_json(
            root / "evals/results/phase-002/reveal_record.json"
        )["revealed_at"],
    }
    body["freeze_hash"] = sha256_json(body)
    return body


def verify_manifest(root: Path, manifest: dict | None = None) -> list[str]:
    manifest = manifest or read_json(root / MANIFEST_PATH)
    errors: list[str] = []
    if manifest.get("subject_commit") != SUBJECT_COMMIT:
        errors.append("SUBJECT_COMMIT_MISMATCH")
    for relative, recorded in manifest.get("immutable_files", {}).items():
        path = root / relative
        if not path.is_file():
            errors.append(f"IMMUTABLE_MISSING:{relative}")
            continue
        current_hash = file_sha256(path)
        if current_hash != recorded["subject_sha256"]:
            errors.append(f"EVIDENCE_FREEZE_BROKEN:{relative}")
    body = dict(manifest)
    recorded_hash = body.pop("freeze_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("FREEZE_HASH_MISMATCH")
    if manifest.get("counts") != {
        "run_attempts": 20,
        "completed": 13,
        "failed": 7,
        "recovery_affected": 5,
    }:
        errors.append("PHASE_002_COUNT_MISMATCH")
    return errors


def freeze(root: Path, *, check: bool) -> dict:
    manifest = build_manifest(root)
    errors = verify_manifest(root, manifest)
    if not errors:
        errors.extend(check_or_write(root / MANIFEST_PATH, manifest, check=check))
    return {
        "status": "PASS" if not errors else "EVIDENCE_FREEZE_BROKEN",
        "freeze_hash": manifest["freeze_hash"],
        "counts": manifest["counts"],
        "errors": errors,
    }
