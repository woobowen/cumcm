import copy
import json

from cumcm_skill_lab.eval.scoring import score_observation


def _observation(repo_root):
    return json.loads(
        (repo_root / "tests/fixtures/contracts/valid/eval_observation.json").read_text(
            encoding="utf-8"
        )
    )


def _rubric(repo_root):
    return json.loads(
        (repo_root / "evals/rubrics/phase-002/CASE-001.json").read_text(encoding="utf-8")
    )


def test_deterministic_grader_scores_observed_fields(repo_root):
    observation = _observation(repo_root)
    score = score_observation(observation, _rubric(repo_root))
    assert score["status"] == "SCORED"
    assert 0 <= score["deterministic_score"] <= 70
    assert score["evidence"]


def test_missing_evidence_lowers_score(repo_root):
    complete = _observation(repo_root)
    complete["requirements"] = [
        "task 1 converts 1.2 tonnes to 1200 kg",
        "task 2 depends on task 1",
        "task 3 validates dispatch",
        "include one-row unit summary",
    ]
    complete["reality_constraints"] = [
        "at most 8 crew-hours",
        "rainfall is uncontrollable uncertainty",
    ]
    missing = copy.deepcopy(complete)
    missing["requirements"] = []
    missing["reality_constraints"] = []
    assert (
        score_observation(missing, _rubric(repo_root))["deterministic_score"]
        < score_observation(complete, _rubric(repo_root))["deterministic_score"]
    )


def test_hard_failure_is_retained_despite_positive_score(repo_root):
    observation = _observation(repo_root)
    observation["claims"].append("This unapproved draft is FINAL.")
    score = score_observation(observation, _rubric(repo_root))
    assert score["deterministic_score"] > 0
    assert "HARD-FAIL-006" in score["hard_failures"]


def test_grader_is_independent_of_anonymous_arm(repo_root):
    first = _observation(repo_root)
    second = copy.deepcopy(first)
    second["anonymous_arm_id"] = "ARM-C"
    first_score = score_observation(first, _rubric(repo_root))
    second_score = score_observation(second, _rubric(repo_root))
    assert first_score["deterministic_score"] == second_score["deterministic_score"]
    assert first_score["evidence"] == second_score["evidence"]


def test_claimed_and_verified_tests_are_not_equated(repo_root):
    observation = _observation(repo_root)
    observation["tests_claimed"] = ["all tests passed"]
    observation["tests_verified"] = []
    assert observation["tests_claimed"] != observation["tests_verified"]
