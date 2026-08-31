import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from cumcm_skill_lab.eval.case_generation import materialize
from cumcm_skill_lab.eval.models import sha256_text
from cumcm_skill_lab.eval.runner import _classify_failure, run_evaluation


def _git(root: Path, *args: str):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _runner_project(repo_root: Path, tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "runner-project"
    root.mkdir()
    materialize(root)
    (root / "contracts").mkdir()
    for name in ("eval_observation.schema.json", "eval_run.schema.json"):
        (root / "contracts" / name).write_bytes((repo_root / "contracts" / name).read_bytes())
    arms = ["BASE", "CANDIDATE-ONE", "CANDIDATE-TWO"]
    for arm in arms:
        package = root / ".cache/upstream-eval/packages" / arm
        package.mkdir(parents=True)
        instruction = f"Anonymous mechanism policy {arm[-1:]}\n"
        (package / "normalized_instruction.txt").write_text(instruction, encoding="utf-8")
        (package / "package_manifest.json").write_text(
            json.dumps(
                {
                    "status": "PACKAGE_SAFE",
                    "package_hash": sha256_text(instruction),
                }
            ),
            encoding="utf-8",
        )
    review = root / "research/upstream_candidates/dynamic_reviews"
    review.mkdir(parents=True)
    (review / "package_safety_review.json").write_text(
        json.dumps({"arms": [{"candidate_id": None}]}), encoding="utf-8"
    )
    config = {
        "seed": 17,
        "cases": ["CASE-001"],
        "arms": [{"arm_id": arm} for arm in arms],
        "model": "mock",
        "reasoning_setting": "medium",
        "sandbox": "workspace-write",
        "timeout_seconds": 20,
        "maximum_runs": 20,
        "network_policy": "DISABLED_REQUIRED",
        "mcp_policy": "DISABLED_REQUIRED",
        "anonymization_policy": {
            "labels": ["ARM-A", "ARM-B", "ARM-C"],
            "map_path": ".cache/upstream-eval/arm-map.json",
        },
    }
    config_path = root / "phase.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    _git(root, "init", "-q", "-b", "eval")
    _git(root, "config", "user.email", "eval@example.invalid")
    _git(root, "config", "user.name", "Eval Fixture")
    _git(root, "add", "contracts", "evals", "phase.yaml", "research")
    _git(root, "commit", "-qm", "runner fixture")
    return root, config_path


def test_mock_runner_isolates_three_arms_and_preserves_equal_task_hash(repo_root, tmp_path):
    root, config_path = _runner_project(repo_root, tmp_path)
    mock = repo_root / "tests/fixtures/mock_codex.py"
    results = run_evaluation(
        root,
        config_path,
        execution_kind="MOCK",
        command_prefix=[sys.executable, str(mock)],
    )
    assert len(results) == 3
    assert {item["anonymous_arm_id"] for item in results} == {"ARM-A", "ARM-B", "ARM-C"}
    assert {item["task_input_hash"] for item in results}.__len__() == 1
    assert all(item["completion_status"] == "COMPLETED" for item in results)
    assert all(item["schema_valid"] for item in results)
    assert all(item["workspace_has_remote"] is False for item in results)
    assert len(list((root / "evals/results/phase-002/observations").rglob("*.json"))) == 3
    assert len(list((root / ".cache/upstream-eval/raw-traces").rglob("*.jsonl"))) == 3
    assert not list((root / "evals/results/phase-002").rglob("*CANDIDATE*"))


def test_existing_run_is_not_overwritten(repo_root, tmp_path):
    root, config_path = _runner_project(repo_root, tmp_path)
    mock = repo_root / "tests/fixtures/mock_codex.py"
    first = run_evaluation(
        root,
        config_path,
        execution_kind="MOCK",
        command_prefix=[sys.executable, str(mock)],
        max_new_runs=1,
    )
    second = run_evaluation(
        root,
        config_path,
        execution_kind="MOCK",
        command_prefix=[sys.executable, str(mock)],
        max_new_runs=1,
    )
    assert first[0] == second[0]


def test_failure_classification_is_explicit():
    assert _classify_failure(None, "", True) == "TIMEOUT"
    assert _classify_failure(1, "Authentication failed", False) == "AUTH_BLOCKED"
    assert _classify_failure(1, "quota exceeded", False) == "QUOTA_BLOCKED"
    assert _classify_failure(7, "bad output", False) == "FAILED"


def _run_fault(repo_root, tmp_path, monkeypatch, mode: str, *, timeout: int = 20):
    root, config_path = _runner_project(repo_root, tmp_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["timeout_seconds"] = timeout
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    monkeypatch.setenv("MOCK_CODEX_MODE", mode)
    return root, run_evaluation(
        root,
        config_path,
        execution_kind="MOCK",
        command_prefix=[sys.executable, str(repo_root / "tests/fixtures/mock_codex.py")],
        arm_filter=["BASE"],
    )[0]


def test_sensitive_environment_is_removed(repo_root, tmp_path, monkeypatch):
    monkeypatch.setenv("EVAL_FAKE_TOKEN", "synthetic-secret")
    root, result = _run_fault(repo_root, tmp_path, monkeypatch, "normal")
    observation = next((root / "evals/results/phase-002/observations").rglob("*.json"))
    assert result["completion_status"] == "COMPLETED"
    assert "env-secret-visible=False" in json.loads(observation.read_text())["claims"]
    assert "synthetic-secret" not in json.dumps(result)


@pytest.mark.parametrize("mode", ["annotated_file", "none_markers"])
def test_artifact_annotations_and_explicit_none_markers_are_valid(
    repo_root, tmp_path, monkeypatch, mode
):
    _, result = _run_fault(repo_root, tmp_path, monkeypatch, mode)
    assert result["completion_status"] == "COMPLETED"
    assert result["schema_valid"] is True


@pytest.mark.parametrize(
    ("mode", "expected_error"),
    [
        ("invalid_schema", "Additional properties are not allowed"),
        ("missing_file", "NONEXISTENT_ARTIFACT_REFERENCE"),
        ("secret_output", "SECRET_IN_OBSERVATION"),
        ("private_path", "PRIVATE_PATH_IN_OBSERVATION"),
        ("write_input", "FROZEN_INPUT_MUTATION"),
        ("network_trace", "FORBIDDEN_NETWORK_COMMAND"),
        ("mcp_trace", "FORBIDDEN_MCP_EVENT"),
        ("reported_prohibition", "PROHIBITED_ACTION_REPORTED"),
    ],
)
def test_publication_and_policy_faults_fail_closed(
    repo_root, tmp_path, monkeypatch, mode, expected_error
):
    root, result = _run_fault(repo_root, tmp_path, monkeypatch, mode)
    assert result["completion_status"] == "FAILED"
    assert result["schema_valid"] is False
    assert expected_error in result["error_summary"]
    assert not list((root / "evals/results/phase-002/observations").rglob("*.json"))


@pytest.mark.parametrize(
    ("mode", "expected_status", "timeout"),
    [
        ("auth", "AUTH_BLOCKED", 20),
        ("quota", "QUOTA_BLOCKED", 20),
        ("nonzero", "FAILED", 20),
        ("timeout", "TIMEOUT", 1),
    ],
)
def test_process_failures_are_retained(
    repo_root, tmp_path, monkeypatch, mode, expected_status, timeout
):
    root, result = _run_fault(repo_root, tmp_path, monkeypatch, mode, timeout=timeout)
    assert result["completion_status"] == expected_status
    assert len(list((root / "evals/results/phase-002/runs").rglob("*.json"))) == 1


def test_raw_trace_cache_is_ignored_and_untracked(repo_root):
    check = subprocess.run(
        ["git", "check-ignore", ".cache/upstream-eval/raw-traces/example.jsonl"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0
    tracked = subprocess.run(
        ["git", "ls-files", ".cache/upstream-eval"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert tracked.stdout == ""


def test_failed_cell_gets_one_append_only_retry(repo_root, tmp_path, monkeypatch):
    root, config_path = _runner_project(repo_root, tmp_path)
    mock = [sys.executable, str(repo_root / "tests/fixtures/mock_codex.py")]
    monkeypatch.setenv("MOCK_CODEX_MODE", "invalid_schema")
    first = run_evaluation(
        root,
        config_path,
        execution_kind="MOCK",
        command_prefix=mock,
        arm_filter=["BASE"],
    )[0]
    monkeypatch.setenv("MOCK_CODEX_MODE", "normal")
    retried = run_evaluation(
        root,
        config_path,
        execution_kind="MOCK",
        command_prefix=mock,
        arm_filter=["BASE"],
        retry_failed_once=True,
    )[0]
    assert first["completion_status"] == "FAILED"
    assert retried["completion_status"] == "COMPLETED"
    assert retried["run_index"] == 2
    run_paths = sorted((root / "evals/results/phase-002/runs").rglob("*.json"))
    assert [path.name for path in run_paths] == ["run-001.json", "run-002.json"]
