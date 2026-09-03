"""Offline replay and mutation checks for the L20 authorization record."""

from __future__ import annotations

from copy import deepcopy

from cumcm_skill_lab.authorization_c1.models import sha256_json
from cumcm_skill_lab.authorization_c2.terminal import (
    build_authorization_replay,
    validate_authorization_replay,
)


def _rehash(value):
    body = deepcopy(value)
    body.pop("replay_hash", None)
    value["replay_hash"] = sha256_json(body)


def test_c2_replay_has_all_eight_stable_variants(repo_root):
    value = build_authorization_replay(repo_root)
    assert validate_authorization_replay(repo_root, value) == []
    assert value["stable"] is True
    assert value["variant_count"] == 8
    assert all(item["stable"] for item in value["variants"].values())


def test_c2_replay_is_offline_and_executes_nothing(repo_root):
    value = build_authorization_replay(repo_root)
    assert value["mode"] == "OFFLINE_NO_MODEL_NO_NETWORK"
    for field in (
        "api_calls",
        "network_calls",
        "model_calls",
        "prototype_executions",
        "third_party_executions",
    ):
        assert value[field] == 0


def test_c2_candidate_label_permutation_preserves_decision_but_rejects_binding(repo_root):
    variant = build_authorization_replay(repo_root)["variants"]["candidate_label_permutation"]
    assert variant == {
        "stable": True,
        "decision_projection_stable": True,
        "exact_binding_rejected": True,
    }


def test_c2_historical_schema_and_live_pointer_replays_pass(repo_root):
    variants = build_authorization_replay(repo_root)["variants"]
    assert variants["historical_schema_resolver_replay"]["errors"] == []
    assert variants["historical_schema_resolver_replay"]["resolved_versions"] == [
        "2.1.0",
        "2.2.0",
        "2.3.0",
        "2.4.0",
    ]
    assert variants["live_pointer_normalization_replay"]["errors"] == []


def test_c2_replay_rejects_missing_variant_after_rehash(repo_root):
    value = build_authorization_replay(repo_root)
    del value["variants"]["decision_order_permutation"]
    value["variant_count"] = 7
    _rehash(value)
    errors = validate_authorization_replay(repo_root, value)
    assert "C2_AUTHORIZATION_REPLAY_VARIANT_SET_MISMATCH" in errors


def test_c2_replay_rejects_external_execution_after_rehash(repo_root):
    value = build_authorization_replay(repo_root)
    value["api_calls"] = 1
    _rehash(value)
    errors = validate_authorization_replay(repo_root, value)
    assert "C2_AUTHORIZATION_REPLAY_EXTERNAL_EXECUTION_PROHIBITED" in errors


def test_c2_replay_rejects_wrong_parent_after_rehash(repo_root):
    value = build_authorization_replay(repo_root)
    value["parent_artifact_hash"] = "0" * 64
    _rehash(value)
    assert "C2_AUTHORIZATION_REPLAY_NOT_REPRODUCIBLE" in validate_authorization_replay(
        repo_root, value
    )
