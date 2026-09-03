import json
from copy import deepcopy

import pytest

import cumcm_skill_lab.authorization_c1.schema_resolution as schema_module
from cumcm_skill_lab.authorization_c1.models import git_file_bytes
from cumcm_skill_lab.authorization_c1.schema_resolution import (
    HISTORICAL_R2A_START_COMMIT,
    SchemaVersionResolver,
    migrate_state_for_comparison,
    validate_schema_identity,
)


def _historical_state(repo_root, commit=HISTORICAL_R2A_START_COMMIT):
    return json.loads(git_file_bytes(repo_root, commit, "state/project_state.json"))


def _current_state(repo_root):
    return json.loads((repo_root / "state/project_state.json").read_text(encoding="utf-8"))


def test_historical_23_state_resolves_23_schema(repo_root):
    result = SchemaVersionResolver(repo_root).resolve(
        _historical_state(repo_root),
        source="SUBJECT_COMMIT_BLOB",
        snapshot_subject_commit=HISTORICAL_R2A_START_COMMIT,
    )
    assert result["validation_result"] == "PASS"
    assert result["state_schema_version"] == "2.3.0"
    assert result["schema_subject_commit"] == HISTORICAL_R2A_START_COMMIT


def test_historical_23_does_not_require_24_candidate_binding_fields(repo_root):
    state = _historical_state(repo_root)
    assert "shadow_authorization" not in state or (
        "candidate_file_sha256" not in state["shadow_authorization"]
    )
    result = SchemaVersionResolver(repo_root).resolve(
        state,
        source="SUBJECT_COMMIT_BLOB",
        snapshot_subject_commit=HISTORICAL_R2A_START_COMMIT,
    )
    assert result["errors"] == []


def test_current_24_state_uses_current_24_schema(repo_root):
    result = SchemaVersionResolver(repo_root).resolve(
        _current_state(repo_root), source="CURRENT_TREE"
    )
    assert result["validation_result"] == "PASS"
    assert result["state_schema_version"] == "2.4.0"
    assert result["schema_subject_commit"] == "CURRENT_TREE"


def test_unknown_state_schema_version_fails_closed(repo_root):
    state = _historical_state(repo_root)
    state["schema_version"] = "9.9.9"
    result = SchemaVersionResolver(repo_root).resolve(
        state,
        source="SUBJECT_COMMIT_BLOB",
        snapshot_subject_commit=HISTORICAL_R2A_START_COMMIT,
    )
    assert "UNKNOWN_PROJECT_STATE_SCHEMA_VERSION:9.9.9" in result["errors"]


def test_state_version_and_schema_version_mismatch_is_rejected(repo_root):
    schema = json.loads(
        git_file_bytes(
            repo_root,
            HISTORICAL_R2A_START_COMMIT,
            "contracts/project_state.schema.json",
        )
    )
    assert "PROJECT_STATE_SCHEMA_VERSION_MISMATCH" in validate_schema_identity("2.4.0", schema)


def test_schema_id_mismatch_is_rejected(repo_root):
    schema = json.loads(
        git_file_bytes(
            repo_root,
            HISTORICAL_R2A_START_COMMIT,
            "contracts/project_state.schema.json",
        )
    )
    schema["$id"] = "https://attacker.invalid/project_state/v2.3"
    assert "PROJECT_STATE_SCHEMA_ID_MISMATCH" in validate_schema_identity("2.3.0", schema)


def test_historical_schema_hash_mismatch_is_rejected(repo_root):
    result = SchemaVersionResolver(repo_root).resolve(
        _historical_state(repo_root),
        source="SUBJECT_COMMIT_BLOB",
        snapshot_subject_commit=HISTORICAL_R2A_START_COMMIT,
        expected_schema_hash="0" * 64,
    )
    assert "PROJECT_STATE_SCHEMA_EXPECTED_HASH_MISMATCH" in result["errors"]


def test_wrong_snapshot_subject_commit_is_rejected(repo_root):
    result = SchemaVersionResolver(repo_root).resolve(
        _historical_state(repo_root),
        source="SUBJECT_COMMIT_BLOB",
        snapshot_subject_commit="0" * 40,
    )
    assert "HISTORICAL_PROJECT_STATE_SUBJECT_COMMIT_MISMATCH" in result["errors"]


def test_current_schema_cannot_substitute_for_historical_state(repo_root):
    result = SchemaVersionResolver(repo_root).resolve(
        _historical_state(repo_root), source="CURRENT_TREE"
    )
    assert "CURRENT_PROJECT_STATE_SCHEMA_DOWNGRADE_REJECTED" in result["errors"]


def test_missing_historical_schema_fails_closed(repo_root, monkeypatch):
    state = _historical_state(repo_root)

    def missing(*_args, **_kwargs):
        raise ValueError("missing")

    monkeypatch.setattr(schema_module, "git_file_bytes", missing)
    result = SchemaVersionResolver(repo_root).resolve(
        state,
        source="SUBJECT_COMMIT_BLOB",
        snapshot_subject_commit=HISTORICAL_R2A_START_COMMIT,
    )
    assert "HISTORICAL_PROJECT_STATE_SCHEMA_MISSING" in result["errors"]


def test_migration_is_deterministic(repo_root):
    state = _historical_state(repo_root)
    first = migrate_state_for_comparison(state, target_schema_version="2.4.0")
    second = migrate_state_for_comparison(state, target_schema_version="2.4.0")
    assert first == second


def test_migration_does_not_mutate_historical_source(repo_root):
    state = _historical_state(repo_root)
    original = deepcopy(state)
    migrate_state_for_comparison(state, target_schema_version="2.4.0")
    assert state == original


def test_migration_rejects_security_field_loss(repo_root):
    state = _historical_state(repo_root)
    del state["third_party_integrated"]
    with pytest.raises(ValueError, match="PROJECT_STATE_MIGRATION_SECURITY_FIELD_MISSING"):
        migrate_state_for_comparison(state, target_schema_version="2.4.0")


def test_current_state_downgrade_is_rejected(repo_root):
    with pytest.raises(ValueError, match="PROJECT_STATE_SCHEMA_DOWNGRADE_REJECTED"):
        migrate_state_for_comparison(_current_state(repo_root), target_schema_version="2.3.0")


def test_derived_migration_validates_only_as_current_comparison(repo_root):
    migrated = migrate_state_for_comparison(
        _historical_state(repo_root), target_schema_version="2.4.0"
    )
    result = SchemaVersionResolver(repo_root).resolve(migrated, source="CURRENT_TREE")
    assert result["validation_result"] == "PASS"


def test_c1_current_state_requires_shadow_authorization(repo_root):
    state = _current_state(repo_root)
    del state["shadow_authorization"]
    result = SchemaVersionResolver(repo_root).resolve(state, source="CURRENT_TREE")
    assert "C1_PROJECT_STATE_SHADOW_AUTHORIZATION_REQUIRED" in result["errors"]


def test_c1_current_state_rejects_old_freeze_identity(repo_root):
    state = _current_state(repo_root)
    state["shadow_authorization"]["input_freeze_id"] = "PHASE-002D-R2A-INPUT-FREEZE-001"
    state["shadow_authorization"]["input_freeze_hash"] = "0" * 64
    result = SchemaVersionResolver(repo_root).resolve(state, source="CURRENT_TREE")
    assert "C1_PROJECT_STATE_INPUT_FREEZE_ID_MISMATCH" in result["errors"]
    assert "C1_PROJECT_STATE_INPUT_FREEZE_HASH_MISMATCH" in result["errors"]


def test_migration_record_fails_closed_on_target_schema_invalid(repo_root, monkeypatch):
    original = schema_module.migrate_state_for_comparison

    def invalid_migration(state, *, target_schema_version):
        migrated = original(state, target_schema_version=target_schema_version)
        migrated["selected_architecture"] = "ARCH-ATTACKER"
        return migrated

    monkeypatch.setattr(schema_module, "migrate_state_for_comparison", invalid_migration)
    record, migration = schema_module.build_schema_resolution_record(repo_root)
    assert migration["target_schema_validation_result"] == "FAIL"
    assert "PROJECT_STATE_MIGRATION_TARGET_SCHEMA_INVALID" in record["errors"]


def test_schema_resolution_sequence_strictly_follows_history(repo_root):
    history = json.loads(
        (
            repo_root / "evals/results/phase-002d-r2a-c1/historical_verification/record.json"
        ).read_text(encoding="utf-8")
    )
    record, _ = schema_module.build_schema_resolution_record(repo_root)
    assert record["parent_artifact_hash"] == history["record_hash"]
    assert record["artifact_sequence_index"] == history["artifact_sequence_index"] + 1
