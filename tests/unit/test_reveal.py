import json

from cumcm_skill_lab.eval.anonymization import expected_mapping


def test_phase_mapping_is_seeded_bijective_and_identity_free_before_reveal():
    mapping = expected_mapping(
        ["NO_PROJECT_MODELING_SKILL", "HANDSOMEZR", "YUSHUI"],
        ["ARM-A", "ARM-B", "ARM-C"],
        20260831,
    )
    assert len(set(mapping["actual_to_anonymous"].values())) == 3


def test_frozen_scores_stay_identity_hidden_after_reveal(repo_root):
    scores = list((repo_root / "evals/results/phase-002/scores").rglob("*.json"))
    assert len(scores) == 18
    for path in scores:
        score = json.loads(path.read_text(encoding="utf-8"))
        assert score["identity_revealed"] is False
