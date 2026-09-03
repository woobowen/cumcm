"""Resolve project-state contracts by snapshot version, commit, and byte hash."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import (
    CREATED_AT,
    INPUT_FREEZE_PATH,
    RESULT_ROOT,
    check_or_write_json,
    file_sha256,
    git_file_bytes,
    sha256_bytes,
    sha256_json,
)

SCHEMA_PATH = "contracts/project_state.schema.json"
RESOLUTION_PATH = RESULT_ROOT / "schema_resolution/record.json"
MIGRATION_PATH = RESULT_ROOT / "schema_resolution/migration_2.3_to_2.4.json"
HISTORICAL_R2A_START_COMMIT = "b6f469995d2de6ef492bb8f8ee90029059d4b2c3"
SECURITY_FIELDS = (
    "selected_architecture",
    "base_selected",
    "third_party_integrated",
    "skill_capability_status",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema_identity(state_version: str, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("version") != state_version:
        errors.append("PROJECT_STATE_SCHEMA_VERSION_MISMATCH")
    parts = state_version.split(".")
    expected_id = (
        f"https://cumcm.local/contracts/project_state/v{parts[0]}.{parts[1]}"
        if len(parts) == 3
        else None
    )
    if schema.get("$id") != expected_id:
        errors.append("PROJECT_STATE_SCHEMA_ID_MISMATCH")
    return errors


class SchemaVersionResolver:
    """Fail-closed project-state Schema resolution without cross-version fallback."""

    def __init__(self, root: Path):
        self.root = root
        self.freeze = _read_json(root / INPUT_FREEZE_PATH)

    def _historical_binding(self, version: str) -> dict[str, Any] | None:
        return next(
            (
                item
                for item in self.freeze["historical_schemas"]
                if item["schema_version"] == version
            ),
            None,
        )

    def resolve(
        self,
        state: dict[str, Any],
        *,
        source: str,
        snapshot_subject_commit: str | None = None,
        expected_schema_hash: str | None = None,
    ) -> dict[str, Any]:
        version = state.get("schema_version")
        errors: list[str] = []
        schema_bytes: bytes | None = None
        schema_commit: str | None = None
        if not isinstance(version, str):
            errors.append("PROJECT_STATE_SCHEMA_VERSION_MISSING")
        elif source == "CURRENT_TREE":
            current = self.freeze["current_schema"]
            if version != current["schema_version"]:
                errors.append("CURRENT_PROJECT_STATE_SCHEMA_DOWNGRADE_REJECTED")
            if snapshot_subject_commit is not None:
                errors.append("CURRENT_PROJECT_STATE_SUBJECT_COMMIT_PROHIBITED")
            path = self.root / current["path"]
            if not path.is_file():
                errors.append("CURRENT_PROJECT_STATE_SCHEMA_MISSING")
            else:
                schema_bytes = path.read_bytes()
                schema_commit = "CURRENT_TREE"
                if sha256_bytes(schema_bytes) != current["file_sha256"]:
                    errors.append("CURRENT_PROJECT_STATE_SCHEMA_HASH_MISMATCH")
        elif source == "SUBJECT_COMMIT_BLOB":
            binding = self._historical_binding(version) if isinstance(version, str) else None
            if binding is None:
                errors.append(f"UNKNOWN_PROJECT_STATE_SCHEMA_VERSION:{version}")
            elif snapshot_subject_commit != binding["subject_commit"]:
                errors.append("HISTORICAL_PROJECT_STATE_SUBJECT_COMMIT_MISMATCH")
            else:
                schema_commit = binding["subject_commit"]
                try:
                    schema_bytes = git_file_bytes(self.root, schema_commit, binding["schema_path"])
                except ValueError:
                    errors.append("HISTORICAL_PROJECT_STATE_SCHEMA_MISSING")
                if (
                    schema_bytes is not None
                    and sha256_bytes(schema_bytes) != binding["schema_file_sha256"]
                ):
                    errors.append("HISTORICAL_PROJECT_STATE_SCHEMA_HASH_MISMATCH")
        else:
            errors.append(f"PROJECT_STATE_SCHEMA_SOURCE_INVALID:{source}")
        actual_hash = sha256_bytes(schema_bytes) if schema_bytes is not None else None
        if expected_schema_hash is not None and actual_hash != expected_schema_hash:
            errors.append("PROJECT_STATE_SCHEMA_EXPECTED_HASH_MISMATCH")
        schema: dict[str, Any] | None = None
        if schema_bytes is not None:
            try:
                schema = json.loads(schema_bytes)
            except json.JSONDecodeError:
                errors.append("PROJECT_STATE_SCHEMA_JSON_INVALID")
        if schema is not None and isinstance(version, str):
            errors.extend(validate_schema_identity(version, schema))
            errors.extend(
                f"PROJECT_STATE_SCHEMA_VALIDATION:{'/'.join(map(str, item.absolute_path))}:"
                f"{item.message}"
                for item in Draft202012Validator(schema).iter_errors(state)
            )
        record = {
            "snapshot_path": "state/project_state.json",
            "snapshot_subject_commit": snapshot_subject_commit,
            "state_schema_version": version,
            "schema_path": SCHEMA_PATH,
            "schema_source": source,
            "schema_subject_commit": schema_commit,
            "schema_file_sha256": actual_hash,
            "validation_result": "PASS" if not errors else "FAIL",
            "errors": sorted(set(errors)),
            "migration_required": False,
            "migration_artifact": None,
        }
        record["resolution_hash"] = sha256_json(record)
        return record


def migrate_state_for_comparison(
    state: dict[str, Any], *, target_schema_version: str
) -> dict[str, Any]:
    """Produce a non-authoritative comparison view while preserving all input fields."""
    source_version = state.get("schema_version")
    if source_version != "2.3.0" or target_schema_version != "2.4.0":
        if source_version == "2.4.0" and target_schema_version == "2.3.0":
            raise ValueError("PROJECT_STATE_SCHEMA_DOWNGRADE_REJECTED")
        raise ValueError(
            f"PROJECT_STATE_MIGRATION_UNREGISTERED:{source_version}:{target_schema_version}"
        )
    missing = [field for field in SECURITY_FIELDS if field not in state]
    if missing:
        raise ValueError(f"PROJECT_STATE_MIGRATION_SECURITY_FIELD_MISSING:{missing[0]}")
    migrated = deepcopy(state)
    migrated["schema_version"] = target_schema_version
    shadow = migrated.get("shadow_authorization")
    if isinstance(shadow, dict):
        for field in (
            "candidate_file_sha256",
            "canonical_candidate_hash",
            "candidate_freeze_hash",
            "replaces_non_active_candidate_id",
            "historical_compatibility_hash",
            "schema_resolution_hash",
            "candidate_closure_hash",
            "final_audit_bundle_hash",
        ):
            shadow.setdefault(field, None)
    for field in SECURITY_FIELDS:
        if migrated.get(field) != state.get(field):
            raise ValueError(f"PROJECT_STATE_MIGRATION_SECURITY_FIELD_LOST:{field}")
    return migrated


def _migration_artifact(root: Path, historical_state: dict[str, Any]) -> dict[str, Any]:
    source_copy = deepcopy(historical_state)
    migrated = migrate_state_for_comparison(source_copy, target_schema_version="2.4.0")
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "migration_id": "PROJECT-STATE-DERIVED-COMPARISON-2.3-TO-2.4-001",
        "source_schema_version": "2.3.0",
        "target_schema_version": "2.4.0",
        "source_subject_commit": HISTORICAL_R2A_START_COMMIT,
        "source_state_hash": sha256_json(historical_state),
        "source_unchanged": source_copy == historical_state,
        "security_fields_preserved": all(
            migrated[field] == historical_state[field] for field in SECURITY_FIELDS
        ),
        "migration_code_path": ("src/cumcm_skill_lab/authorization_c1/schema_resolution.py"),
        "migration_code_file_sha256": file_sha256(
            root / "src/cumcm_skill_lab/authorization_c1/schema_resolution.py"
        ),
        "derived_state": migrated,
        "authoritative_historical_truth": False,
    }
    body["migration_hash"] = sha256_json(body)
    return body


def build_schema_resolution_record(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    resolver = SchemaVersionResolver(root)
    freeze = _read_json(root / INPUT_FREEZE_PATH)
    history = _read_json(
        root / "evals/results/phase-002d-r2a-c1/historical_verification/record.json"
    )
    resolutions = []
    for binding in freeze["historical_schemas"]:
        state = json.loads(
            git_file_bytes(root, binding["subject_commit"], "state/project_state.json")
        )
        resolutions.append(
            resolver.resolve(
                state,
                source="SUBJECT_COMMIT_BLOB",
                snapshot_subject_commit=binding["subject_commit"],
                expected_schema_hash=binding["schema_file_sha256"],
            )
        )
    current_state = _read_json(root / "state/project_state.json")
    resolutions.append(resolver.resolve(current_state, source="CURRENT_TREE"))
    historical_23 = json.loads(
        git_file_bytes(root, HISTORICAL_R2A_START_COMMIT, "state/project_state.json")
    )
    migration = _migration_artifact(root, historical_23)
    errors = [error for item in resolutions for error in item["errors"]]
    if not migration["source_unchanged"] or not migration["security_fields_preserved"]:
        errors.append("PROJECT_STATE_MIGRATION_INVARIANT_FAILED")
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "record_id": "PHASE-002D-R2A-C1-SCHEMA-RESOLUTION-001",
        "artifact_sequence_index": 1,
        "parent_artifact_hash": history["record_hash"],
        "created_at": CREATED_AT,
        "historical_compatibility_hash": history["record_hash"],
        "resolutions": resolutions,
        "migration_required_for_validation": False,
        "derived_comparison_migration": {
            "path": MIGRATION_PATH.as_posix(),
            "migration_hash": migration["migration_hash"],
            "authoritative_historical_truth": False,
        },
        "unknown_version_behavior": "FAIL_CLOSED",
        "current_schema_fallback_for_history": False,
        "historical_state_rewritten": False,
        "result": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
    }
    body["record_hash"] = sha256_json(body)
    return body, migration


def check_or_write_schema_resolution(root: Path, *, check: bool) -> dict[str, Any]:
    expected, migration = build_schema_resolution_record(root)
    errors = check_or_write_json(root / MIGRATION_PATH, migration, check=check)
    errors.extend(check_or_write_json(root / RESOLUTION_PATH, expected, check=check))
    if expected["result"] != "PASS":
        errors.extend(expected["errors"])
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "record_id": expected["record_id"],
        "record_hash": expected["record_hash"],
        "resolution_count": len(expected["resolutions"]),
        "migration_hash": migration["migration_hash"],
    }


__all__ = [
    "HISTORICAL_R2A_START_COMMIT",
    "MIGRATION_PATH",
    "RESOLUTION_PATH",
    "SchemaVersionResolver",
    "build_schema_resolution_record",
    "check_or_write_schema_resolution",
    "migrate_state_for_comparison",
    "validate_schema_identity",
]
