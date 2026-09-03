"""Generate the L1 historical compatibility record from the versioned verifier."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cumcm_skill_lab.failure_aware.evidence_freeze import verify_input_freeze

from .historical_verification import (
    POLICY_PATH,
    load_policy,
    policy_entry,
    subject_tree_hash,
    verify_tree_entry,
)
from .models import (
    CREATED_AT,
    INPUT_FREEZE_PATH,
    RESULT_ROOT,
    check_or_write_json,
    file_sha256,
    sha256_json,
)

RECORD_PATH = RESULT_ROOT / "historical_verification/record.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_historical_record(root: Path) -> dict[str, Any]:
    freeze = _read_json(root / INPUT_FREEZE_PATH)
    policy = load_policy(root)
    errors = verify_input_freeze(root)
    r1_manifest = _read_json(root / "evals/results/phase-002d-r1/input_freeze_manifest.json")
    workflow_entry = next(
        item for item in policy["entries"] if item["path"] == "rules/workflow_rules.yaml"
    )
    preserved_tree_hashes: dict[str, str] = {}
    preservation_errors: list[str] = []
    for relative in dict.fromkeys(freeze["historical_roots_immutable"]):
        entry = policy_entry(policy, relative, "PHASE-002D-R2A-C1/1.0.0")
        expected = subject_tree_hash(root, entry)
        preserved_tree_hashes[relative] = expected
        preservation_errors.extend(verify_tree_entry(root, entry, expected))
    errors.extend(preservation_errors)
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_id": "PHASE-002D-R2A-C1-HISTORICAL-COMPATIBILITY-001",
        "artifact_sequence_index": 1,
        "parent_artifact_hash": freeze["manifest_hash"],
        "created_at": CREATED_AT,
        "input_freeze_hash": freeze["manifest_hash"],
        "policy_path": POLICY_PATH.as_posix(),
        "policy_file_sha256": file_sha256(root / POLICY_PATH),
        "verifier_path": "src/cumcm_skill_lab/authorization_c1/historical_verification.py",
        "verifier_file_sha256": file_sha256(
            root / "src/cumcm_skill_lab/authorization_c1/historical_verification.py"
        ),
        "verifier_adapter_hashes": {
            path: file_sha256(root / path)
            for path in (
                "src/cumcm_skill_lab/expansion/input_freeze.py",
                "src/cumcm_skill_lab/failure_aware/evidence_freeze.py",
                "src/cumcm_skill_lab/specification/models.py",
            )
        },
        "verification_modes": sorted({item["verification_mode"] for item in policy["entries"]}),
        "r1_subject_commit": r1_manifest["subject_commit"],
        "immutable_paths": sorted(
            item["path"]
            for item in policy["entries"]
            if item["verification_mode"] == "CURRENT_TREE_IMMUTABLE"
        ),
        "live_pointer_paths": ["rules/workflow_rules.yaml"],
        "allowed_live_fields": workflow_entry["allowed_live_fields"],
        "rejected_live_fields": [
            "git_delivery.remote_name",
            "git_delivery.repository",
            "git_delivery.remote_url",
            "git_delivery.protected_base_branch",
            "git_delivery.allow_force_push",
            "git_delivery.allow_agent_merge",
            "ALL_UNREGISTERED_FIELDS",
        ],
        "historical_r1_freeze_hash": r1_manifest["manifest_hash"],
        "historical_r1_freeze_errors": errors,
        "preserved_historical_tree_hashes": preserved_tree_hashes,
        "preservation_errors": preservation_errors,
        "original_failure_count_fixed": 20 if not errors else 0,
        "result": "PASS" if not errors else "FAIL",
        "no_current_file_fallback": True,
        "whole_file_ignore_allowed": False,
    }
    body["record_hash"] = sha256_json(body)
    return body


def check_or_write_historical_record(root: Path, *, check: bool) -> dict[str, Any]:
    expected = build_historical_record(root)
    errors = check_or_write_json(root / RECORD_PATH, expected, check=check)
    if expected["result"] != "PASS":
        errors.extend(expected["historical_r1_freeze_errors"])
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "record_id": expected["record_id"],
        "record_hash": expected["record_hash"],
        "fixed_failure_count": expected["original_failure_count_fixed"],
    }
