import json
import subprocess
from pathlib import Path

from cumcm_skill_lab.eval.models import load_json, write_json
from cumcm_skill_lab.eval.recovery import recover_observations


def _git(root: Path, *args: str):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _project(repo_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "recovery-project"
    (root / "contracts").mkdir(parents=True)
    for name in (
        "eval_observation.schema.json",
        "eval_recovery.schema.json",
        "eval_run.schema.json",
    ):
        (root / "contracts" / name).write_bytes((repo_root / "contracts" / name).read_bytes())
    review = root / "research/upstream_candidates/dynamic_reviews"
    review.mkdir(parents=True)
    write_json(review / "package_safety_review.json", {"arms": [{"candidate_id": None}]})
    run = load_json(repo_root / "tests/fixtures/contracts/valid/eval_run.json")
    run.update(
        {
            "evaluation_id": "PHASE-002-FIRST-ROUND",
            "case_id": "CASE-002",
            "anonymous_arm_id": "ARM-A",
            "completion_status": "FAILED",
            "schema_valid": False,
            "error_summary": (
                "NONEXISTENT_ARTIFACT_REFERENCE:code_artifacts:"
                "Inline Python was used; no file was created."
            ),
        }
    )
    run_path = root / "evals/results/phase-002/runs/ARM-A/CASE-002/run-001.json"
    write_json(run_path, run)
    observation = load_json(repo_root / "tests/fixtures/contracts/valid/eval_observation.json")
    observation.update(
        {
            "evaluation_id": "PHASE-002-FIRST-ROUND",
            "case_id": "CASE-002",
            "anonymous_arm_id": "ARM-A",
            "code_artifacts": ["Inline Python was used; no file was created."],
            "files_created": [],
        }
    )
    raw_path = (
        root / ".cache/upstream-eval/raw-outputs/PHASE-002-FIRST-ROUND/ARM-A/CASE-002/run-001.json"
    )
    write_json(raw_path, observation)
    _git(root, "init", "-q", "-b", "eval")
    _git(root, "config", "user.email", "eval@example.invalid")
    _git(root, "config", "user.name", "Recovery Fixture")
    _git(root, "add", "contracts", "evals", "research")
    _git(root, "commit", "-qm", "recovery fixture")
    return root


def test_recovery_is_append_only_hash_bound_and_checkable(repo_root, tmp_path):
    root = _project(repo_root, tmp_path)
    generated = recover_observations(root, recovered_at="2026-08-31T00:00:00Z")
    assert generated["status"] == "PASS"
    assert generated["recovered"] == ["RECOVERY-ARM-A-CASE-002-RUN-001"]
    source_run = root / "evals/results/phase-002/runs/ARM-A/CASE-002/run-001.json"
    assert json.loads(source_run.read_text())["completion_status"] == "FAILED"
    checked = recover_observations(root, check=True)
    assert checked["status"] == "PASS"


def test_recovery_detects_post_recovery_observation_mutation(repo_root, tmp_path):
    root = _project(repo_root, tmp_path)
    assert recover_observations(root)["status"] == "PASS"
    observation = root / "evals/results/phase-002/observations/ARM-A/CASE-002/run-001.json"
    data = load_json(observation)
    data["claims"].append("mutated")
    write_json(observation, data)
    result = recover_observations(root, check=True)
    assert result["status"] == "FAIL"
    assert any("observation_hash" in error for error in result["errors"])
