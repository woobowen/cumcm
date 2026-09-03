"""Build and verify the immutable L0 input freeze for the C1 continuation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    CREATED_AT,
    INPUT_FREEZE_PATH,
    PR_HEAD,
    PR_NUMBER,
    RESULT_ROOT,
    STARTING_COMMIT,
    check_or_write_json,
    file_sha256,
    git_file_sha256,
    sha256_json,
)

OLD_ROOT = Path("evals/results/phase-002d-r2a")
OLD_CANDIDATE_PATH = OLD_ROOT / "authorization_candidate/candidate.json"
OLD_AUDITOR_PATHS = (
    OLD_ROOT / "subagent_outputs/final_shadow_authorization_auditor-attempt-001.json",
    OLD_ROOT / "subagent_outputs/final_shadow_authorization_auditor-attempt-002.json",
    OLD_ROOT / "subagent_outputs/final_shadow_authorization_auditor.json",
)
R1_SUBJECT_COMMIT = "d59f4b8a36fa3c15e06ec0aceb948cd2bafd2abc"
HISTORICAL_SCHEMA_SNAPSHOTS = {
    "2.1.0": "10073a2fe5b1512a16ab9a9c7907fb2b7f5ff765",
    "2.2.0": "4434e0c5df9621c7b17731a3854a80442401da2b",
    "2.3.0": "b6f469995d2de6ef492bb8f8ee90029059d4b2c3",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_binding(root: Path, relative: Path) -> dict[str, str]:
    return {"path": relative.as_posix(), "file_sha256": file_sha256(root / relative)}


def build_input_freeze(root: Path) -> dict[str, Any]:
    r1 = _read_json(root / "evals/results/phase-002d-r1/input_freeze_manifest.json")
    r2 = _read_json(root / "evals/results/phase-002d-r2/input_freeze_manifest.json")
    r2a = _read_json(root / "evals/results/phase-002d-r2a/input_freeze_manifest.json")
    old_candidate = _read_json(root / OLD_CANDIDATE_PATH)
    terminal_audit = _read_json(root / OLD_AUDITOR_PATHS[-1])
    schemas = []
    for version, commit in HISTORICAL_SCHEMA_SNAPSHOTS.items():
        schemas.append(
            {
                "schema_version": version,
                "schema_path": "contracts/project_state.schema.json",
                "subject_commit": commit,
                "schema_file_sha256": git_file_sha256(
                    root, commit, "contracts/project_state.schema.json"
                ),
            }
        )
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "freeze_id": "PHASE-002D-R2A-C1-INPUT-FREEZE-001",
        "phase": "PHASE-EVIDENCE-EXPANSION-002D",
        "subphase": (
            "PHASE-002D-R2A-C1-HISTORICAL-COMPATIBILITY-AND-CANDIDATE-BOUND-AUTHORIZATION-CLOSURE"
        ),
        "artifact_sequence_index": 0,
        "parent_artifact_hash": None,
        "created_at": CREATED_AT,
        "starting_commit": STARTING_COMMIT,
        "draft_pr": {"number": PR_NUMBER, "head_commit": PR_HEAD},
        "historical_freezes": {
            "r1": {
                **_file_binding(
                    root, Path("evals/results/phase-002d-r1/input_freeze_manifest.json")
                ),
                "freeze_id": r1["freeze_id"],
                "manifest_hash": r1["manifest_hash"],
            },
            "r2": {
                **_file_binding(
                    root, Path("evals/results/phase-002d-r2/input_freeze_manifest.json")
                ),
                "freeze_id": r2["freeze_id"],
                "manifest_hash": r2["manifest_hash"],
            },
            "r2a": {
                **_file_binding(
                    root, Path("evals/results/phase-002d-r2a/input_freeze_manifest.json")
                ),
                "freeze_id": r2a["freeze_id"],
                "manifest_hash": r2a["manifest_hash"],
            },
        },
        "old_candidate": {
            **_file_binding(root, OLD_CANDIDATE_PATH),
            "candidate_id": old_candidate["candidate_id"],
            "canonical_candidate_hash": old_candidate["candidate_hash"],
            "classification": "HISTORICAL_NON_ACTIVE_CANDIDATE",
        },
        "old_final_auditors": [
            {
                **_file_binding(root, path),
                "output_hash": _read_json(root / path)["output_hash"],
            }
            for path in OLD_AUDITOR_PATHS
        ],
        "terminal_finding": {
            "finding_id": "R2A-FINAL-002",
            "output_hash": terminal_audit["output_hash"],
            "bundle_hash": terminal_audit["bundle_hash"],
            "path": OLD_AUDITOR_PATHS[-1].as_posix(),
        },
        "protected_bindings": {
            "formal_skill_tree_hash": r2a["formal_skill_tree_hash"],
            "benchmark_hash": r2a["benchmark_manifest_hash"],
            "threshold_hash": r2a["threshold_policy_hash"],
            "protocol_hash": r2a["prospective_protocol_hash"],
            "implementation_embargo_hash": r2a["implementation_embargo_hash"],
        },
        "current_schema": {
            **_file_binding(root, Path("contracts/project_state.schema.json")),
            "schema_version": "2.4.0",
            "source": "CURRENT_TREE",
        },
        "historical_schemas": schemas,
        "workflow_rules": {
            "path": "rules/workflow_rules.yaml",
            "current_file_sha256": file_sha256(root / "rules/workflow_rules.yaml"),
            "historical_subject_commit": R1_SUBJECT_COMMIT,
            "historical_subject_file_sha256": git_file_sha256(
                root, R1_SUBJECT_COMMIT, "rules/workflow_rules.yaml"
            ),
        },
        "counters": {
            "api_calls": 0,
            "real_model_in_loop_runs": 0,
            "prototype_executions": 0,
            "third_party_executions": 0,
        },
        "historical_roots_immutable": [
            f"evals/results/{name}/"
            for name in (
                "phase-002",
                "phase-002a",
                "phase-002b",
                "phase-002c",
                "phase-002d",
                "phase-002d-r1",
                "phase-002d-r2",
                "phase-002d-r2a",
            )
        ],
    }
    body["manifest_hash"] = sha256_json(body)
    return body


def validate_input_freeze(root: Path, value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    body = dict(value)
    recorded = body.pop("manifest_hash", None)
    if recorded != sha256_json(body):
        errors.append("INPUT_FREEZE_BROKEN:MANIFEST_HASH")
    try:
        expected = build_input_freeze(root)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return [f"INPUT_FREEZE_BROKEN:SOURCE:{exc}"]
    if value != expected:
        errors.append("INPUT_FREEZE_BROKEN:BINDING_DRIFT")
    return sorted(set(errors))


def check_or_write_input_freeze(root: Path, *, check: bool) -> dict[str, Any]:
    expected = build_input_freeze(root)
    errors = validate_input_freeze(root, expected)
    errors.extend(check_or_write_json(root / INPUT_FREEZE_PATH, expected, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "freeze_id": expected["freeze_id"],
        "manifest_hash": expected["manifest_hash"],
        "artifact_sequence_index": expected["artifact_sequence_index"],
        "result_root": RESULT_ROOT.as_posix(),
    }
