import json

from cumcm_skill_lab.eval.score_pipeline import combine_score


def test_combined_score_is_70_plus_30_and_stays_anonymous(repo_root):
    observation = json.loads(
        (repo_root / "tests/fixtures/contracts/valid/eval_observation.json").read_text()
    )
    run = json.loads((repo_root / "tests/fixtures/contracts/valid/eval_run.json").read_text())
    review = json.loads((repo_root / "tests/fixtures/contracts/valid/eval_review.json").read_text())
    rubric = json.loads((repo_root / "evals/rubrics/phase-002/CASE-001.json").read_text())
    review.update(
        {
            "evaluation_id": run["evaluation_id"],
            "case_id": run["case_id"],
            "anonymous_arm_id": run["anonymous_arm_id"],
            "run_index": run["run_index"],
        }
    )
    score = combine_score(
        observation,
        run,
        rubric,
        review,
        recovered=False,
        frozen_at="2026-08-31T00:00:00Z",
    )
    assert score["total_score"] == score["deterministic_score"] + score["reviewer_score"]
    assert score["identity_revealed"] is False
    assert len(score["initial_score_hash"]) == 64


def test_recovered_score_retains_low_confidence_and_failure_effect(repo_root):
    observation = json.loads(
        (repo_root / "tests/fixtures/contracts/valid/eval_observation.json").read_text()
    )
    run = json.loads((repo_root / "tests/fixtures/contracts/valid/eval_run.json").read_text())
    review = json.loads((repo_root / "tests/fixtures/contracts/valid/eval_review.json").read_text())
    rubric = json.loads((repo_root / "evals/rubrics/phase-002/CASE-001.json").read_text())
    run["completion_status"] = "FAILED"
    run["schema_valid"] = False
    score = combine_score(
        observation,
        run,
        rubric,
        review,
        recovered=True,
        frozen_at="2026-08-31T00:00:00Z",
    )
    assert score["status"] == "SCORED"
    assert score["affected_by_run_failure"] is True
    assert score["confidence"] == "LOW"
