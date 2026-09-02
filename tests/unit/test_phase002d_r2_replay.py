import pytest

from cumcm_skill_lab.specification.replay import build_replay, validate_replay


@pytest.fixture
def replay(repo_root):
    return build_replay(repo_root)


@pytest.mark.parametrize(
    "variant",
    (
        "original_rebuild",
        "decision_order_permutation",
        "evidence_order_permutation",
        "target_label_permutation",
        "seed_manifest_verification",
    ),
)
def test_replay_variant_is_stable(replay, variant):
    assert replay["variants"][variant] is True


def test_replay_is_offline(replay):
    assert replay["offline"] is True
    assert replay["network_calls"] == 0
    assert replay["model_calls"] == 0
    assert replay["api_calls"] == 0


def test_replay_never_executes_prototype_or_third_party(replay):
    assert replay["prototype_executions"] == 0
    assert replay["third_party_executions"] == 0


def test_replay_does_not_read_private_values(replay):
    assert replay["seed_manifest"]["checks"]["private_values_read"] is False


def test_replay_hash_validates(replay):
    assert validate_replay(replay) == []
