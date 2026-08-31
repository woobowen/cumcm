import json

import pytest

from cumcm_skill_lab.eval.anonymization import (
    assert_identity_free,
    expected_mapping,
    load_or_create_mapping,
)


def test_anonymous_map_is_seeded_and_bijective(tmp_path):
    arms = ["BASE", "ONE", "TWO"]
    labels = ["ARM-A", "ARM-B", "ARM-C"]
    first = expected_mapping(arms, labels, 7)
    second = expected_mapping(arms, labels, 7)
    assert first == second
    assert set(first["actual_to_anonymous"].values()) == set(labels)
    path = tmp_path / "map.json"
    assert load_or_create_mapping(path, arms, labels, 7) == first
    assert load_or_create_mapping(path, arms, labels, 7) == first


def test_anonymous_map_mismatch_fails_closed(tmp_path):
    path = tmp_path / "map.json"
    path.write_text(json.dumps({"wrong": True}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="ANONYMIZATION_MAP_MISMATCH"):
        load_or_create_mapping(path, ["A"], ["ARM-A"], 1)


def test_candidate_identity_is_rejected_from_blind_record():
    with pytest.raises(RuntimeError, match="ANONYMIZATION_IDENTITY_LEAK"):
        assert_identity_free({"note": "candidate-secret"}, ["candidate-secret"])
