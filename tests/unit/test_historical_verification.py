import json
from copy import deepcopy

import pytest
import yaml

from cumcm_skill_lab.authorization_c1.historical_record import build_historical_record
from cumcm_skill_lab.authorization_c1.historical_verification import (
    load_policy,
    policy_entry,
    verify_file_entry,
    verify_tree_entry,
)
from cumcm_skill_lab.authorization_c1.models import git_file_bytes, sha256_bytes

VERSION = "PHASE-002D-R1/1.0.0"
WORKFLOW_PATH = "rules/workflow_rules.yaml"
WORKFLOW_HASH = "a2271121eb659f50155699c2cd3ccff2771b0fd5bb90bf3710b022d4bbb33864"


def _workflow_entry(repo_root):
    return policy_entry(load_policy(repo_root), WORKFLOW_PATH, VERSION)


def _historical_workflow(repo_root):
    entry = _workflow_entry(repo_root)
    return yaml.safe_load(
        git_file_bytes(repo_root, entry["subject_commit"], WORKFLOW_PATH).decode("utf-8")
    )


def _bytes(value):
    return yaml.safe_dump(value, sort_keys=True).encode("utf-8")


def test_subject_commit_blob_passes(repo_root):
    entry = deepcopy(_workflow_entry(repo_root))
    entry["verification_mode"] = "SUBJECT_COMMIT_BLOB"
    entry["allowed_live_fields"] = []
    assert verify_file_entry(repo_root, entry, WORKFLOW_HASH) == []


def test_subject_commit_blob_mismatch_is_rejected(repo_root):
    entry = deepcopy(_workflow_entry(repo_root))
    entry["verification_mode"] = "SUBJECT_COMMIT_BLOB"
    entry["allowed_live_fields"] = []
    assert verify_file_entry(repo_root, entry, "0" * 64) == [
        f"HISTORICAL_BLOB_HASH_MISMATCH:{WORKFLOW_PATH}"
    ]


def test_missing_subject_commit_does_not_fallback_to_current(repo_root):
    entry = deepcopy(_workflow_entry(repo_root))
    entry["subject_commit"] = "0" * 40
    errors = verify_file_entry(repo_root, entry, WORKFLOW_HASH)
    assert errors == [f"HISTORICAL_SUBJECT_READ_FAILED:{'0' * 40}:{WORKFLOW_PATH}"]


def test_missing_subject_path_does_not_fallback_to_current(repo_root):
    entry = deepcopy(_workflow_entry(repo_root))
    entry["path"] = "rules/does-not-exist.yaml"
    errors = verify_file_entry(repo_root, entry, WORKFLOW_HASH)
    assert errors == [
        f"HISTORICAL_SUBJECT_READ_FAILED:{entry['subject_commit']}:rules/does-not-exist.yaml"
    ]


def test_current_immutable_byte_mutation_is_rejected(repo_root):
    entry = policy_entry(load_policy(repo_root), "rules/evidence_rules.yaml", VERSION)
    subject = git_file_bytes(repo_root, entry["subject_commit"], entry["path"])
    errors = verify_file_entry(
        repo_root,
        entry,
        sha256_bytes(subject),
        current_bytes=subject + b"\n# mutation\n",
    )
    assert errors == ["CURRENT_IMMUTABLE_MUTATED:rules/evidence_rules.yaml"]


def test_allowed_live_task_branch_pointer_passes(repo_root):
    value = _historical_workflow(repo_root)
    value["git_delivery"]["preferred_task_branch"] = "feat/another-task"
    assert (
        verify_file_entry(
            repo_root, _workflow_entry(repo_root), WORKFLOW_HASH, current_bytes=_bytes(value)
        )
        == []
    )


def test_disallowed_live_remote_url_is_rejected(repo_root):
    value = _historical_workflow(repo_root)
    value["git_delivery"]["remote_url"] = "https://attacker.invalid/cumcm.git"
    errors = verify_file_entry(
        repo_root, _workflow_entry(repo_root), WORKFLOW_HASH, current_bytes=_bytes(value)
    )
    assert any("LIVE_POINTER_CURRENT_SCHEMA_INVALID" in item for item in errors)
    assert any("LIVE_POINTER_DISALLOWED_FIELD" in item for item in errors)


def test_force_push_policy_mutation_is_rejected(repo_root):
    value = _historical_workflow(repo_root)
    value["git_delivery"]["allow_force_push"] = True
    errors = verify_file_entry(
        repo_root, _workflow_entry(repo_root), WORKFLOW_HASH, current_bytes=_bytes(value)
    )
    assert "LIVE_POINTER_DELIVERY_INVARIANT_FAILED:git_delivery.allow_force_push" in errors


def test_main_protection_deletion_is_rejected(repo_root):
    value = _historical_workflow(repo_root)
    del value["git_delivery"]["protected_base_branch"]
    errors = verify_file_entry(
        repo_root, _workflow_entry(repo_root), WORKFLOW_HASH, current_bytes=_bytes(value)
    )
    assert any("git_delivery.protected_base_branch" in item for item in errors)


def test_unregistered_live_field_change_is_rejected(repo_root):
    value = _historical_workflow(repo_root)
    value["stale_source"] = "ATTACKER.md"
    errors = verify_file_entry(
        repo_root, _workflow_entry(repo_root), WORKFLOW_HASH, current_bytes=_bytes(value)
    )
    assert f"LIVE_POINTER_DISALLOWED_FIELD:{WORKFLOW_PATH}:stale_source" in errors


def test_whole_file_replacement_is_rejected(repo_root):
    errors = verify_file_entry(
        repo_root,
        _workflow_entry(repo_root),
        WORKFLOW_HASH,
        current_bytes=b"git_delivery:\n  preferred_task_branch: feat/only\n",
    )
    assert any("LIVE_POINTER_CURRENT_SCHEMA_INVALID" in item for item in errors)
    assert any("LIVE_POINTER_DISALLOWED_FIELD" in item for item in errors)


def test_yaml_mapping_key_order_is_semantically_stable(repo_root):
    value = _historical_workflow(repo_root)
    reordered = dict(reversed(list(value.items())))
    assert (
        verify_file_entry(
            repo_root, _workflow_entry(repo_root), WORKFLOW_HASH, current_bytes=_bytes(reordered)
        )
        == []
    )


def test_current_workflow_schema_invalid_is_rejected(repo_root):
    value = _historical_workflow(repo_root)
    value["rules"] = []
    errors = verify_file_entry(
        repo_root, _workflow_entry(repo_root), WORKFLOW_HASH, current_bytes=_bytes(value)
    )
    assert any("LIVE_POINTER_CURRENT_SCHEMA_INVALID" in item for item in errors)


def test_policy_has_no_broad_file_ignore(repo_root):
    policy = load_policy(repo_root)
    entry = policy_entry(policy, WORKFLOW_PATH, VERSION)
    assert entry["verification_mode"] == "LIVE_SEMANTIC_POINTER"
    assert entry["allowed_live_fields"] == ["git_delivery.preferred_task_branch"]
    assert all("*" not in field and "." in field for field in entry["allowed_live_fields"])


def test_historical_tree_checks_subject_and_current(repo_root):
    entry = policy_entry(load_policy(repo_root), "evals/results/phase-002/", VERSION)
    expected = "12bb666a5532ec810bba842971c20cd4d8635268360cfd901a60bd9def650e3e"
    assert verify_tree_entry(repo_root, entry, expected) == []


def test_c1_immutable_subject_commit_retarget_is_rejected(repo_root, monkeypatch):
    import cumcm_skill_lab.authorization_c1.historical_record as record_module

    mutated = deepcopy(record_module.load_policy(repo_root))
    for entry in mutated["entries"]:
        if (
            entry["manifest_version"] == "PHASE-002D-R2A-C1/1.0.0"
            and entry["verification_mode"] == "CURRENT_TREE_IMMUTABLE"
        ):
            entry["subject_commit"] = "3106454daf234aff50af5ec1941c35ac548b7274"
    monkeypatch.setattr(record_module, "load_policy", lambda _root: mutated)
    record = build_historical_record(repo_root)
    assert record["result"] == "FAIL"
    assert any(
        item.startswith("C1_HISTORICAL_SUBJECT_RETARGETED:")
        for item in record["preservation_errors"]
    )


@pytest.mark.parametrize(
    "payload",
    [
        b"version: 1\nversion: 1\n",
        b"git_delivery:\n  allow_force_push: true\n  allow_force_push: false\n",
    ],
)
def test_live_pointer_duplicate_yaml_key_is_rejected(repo_root, payload):
    errors = verify_file_entry(
        repo_root, _workflow_entry(repo_root), WORKFLOW_HASH, current_bytes=payload
    )
    assert any(item.startswith("LIVE_POINTER_PARSE_FAILED:") for item in errors)


def test_derived_observation_is_recomputed_from_authoritative_state(repo_root):
    record = build_historical_record(repo_root)
    assert record["derived_observation_errors"] == []


def test_successor_record_keeps_frozen_adapter_blob_hashes(repo_root):
    expected = build_historical_record(repo_root)
    stored = json.loads(
        (
            repo_root / "evals/results/phase-002d-r2a-c1/historical_verification/record.json"
        ).read_text(encoding="utf-8")
    )
    assert expected["verifier_adapter_hashes"] == stored["verifier_adapter_hashes"]
    assert expected["record_hash"] == stored["record_hash"]
