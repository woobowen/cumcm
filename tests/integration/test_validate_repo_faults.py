import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from cumcm_skill_lab.repo_validation import validate_repo
from cumcm_skill_lab.report_generation import generate_status


def _copy_project(source: Path, target: Path):
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", ".cache", "__pycache__", ".pytest_cache", ".ruff_cache"
        ),
    )
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True)


@pytest.fixture
def project_copy(repo_root: Path, tmp_path: Path) -> Path:
    target = tmp_path / "project"
    _copy_project(repo_root, target)
    generate_status(target)
    return target


def _ids(result):
    return {item["id"] for item in result["errors"]}


def test_clean_project_passes_strict(project_copy: Path):
    result = validate_repo(project_copy, strict=True)
    assert result["errors"] == []


def test_second_same_name_skill_fails(project_copy: Path):
    source = project_copy / ".agents/skills/cumcm-modeling-evidence"
    shutil.copytree(source, project_copy / ".agents/skills/duplicate")
    assert "SKILL_DUPLICATE_NAME" in _ids(validate_repo(project_copy, strict=True))


def test_candidate_in_discovery_fails(project_copy: Path):
    skill = project_copy / ".agents/skills/candidate"
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: candidate\ndescription: Use for candidate. Do not use for formal work.\n---\n",
        encoding="utf-8",
    )
    (skill / "agents/openai.yaml").write_text(
        "policy:\n  allow_implicit_invocation: false\n", encoding="utf-8"
    )
    result = validate_repo(project_copy, strict=True)
    assert "SKILL_COUNT" in _ids(result)


def test_missing_schema_version_fails(project_copy: Path):
    path = project_copy / "contracts/project_state.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    del schema["version"]
    path.write_text(json.dumps(schema), encoding="utf-8")
    assert "SCHEMA_VERSION" in _ids(validate_repo(project_copy, strict=True))


def test_stale_report_fails(project_copy: Path):
    path = project_copy / "state/project_state.json"
    state = json.loads(path.read_text(encoding="utf-8"))
    state["status"] = "STALE"
    path.write_text(json.dumps(state), encoding="utf-8")
    assert "STATUS_REPORT_STALE" in _ids(validate_repo(project_copy, strict=True))


def test_synthetic_secret_fails(project_copy: Path):
    (project_copy / "leaked.txt").write_text("sk-" + "z" * 24, encoding="utf-8")
    assert "SECRET_OPENAI_KEY" in _ids(validate_repo(project_copy, strict=True))


def test_vault_reference_fails(project_copy: Path):
    (project_copy / "benchmarks/bad.txt").write_text(
        "load benchmark-vault/private.json", encoding="utf-8"
    )
    assert "LEAKAGE_VAULT_REFERENCE" in _ids(validate_repo(project_copy, strict=True))


def test_tracked_candidate_cache_fails(project_copy: Path):
    path = project_copy / ".cache/upstream/candidate"
    path.mkdir(parents=True)
    (path / "README.md").write_text("synthetic", encoding="utf-8")
    subprocess.run(
        ["git", "add", "-f", ".cache/upstream/candidate/README.md"],
        cwd=project_copy,
        check=True,
    )
    assert "UPSTREAM_CACHE_TRACKED" in _ids(validate_repo(project_copy, strict=True))


def test_duplicate_remote_truth_fails(project_copy: Path):
    workflow = project_copy / "rules/workflow_rules.yaml"
    remote_url = yaml.safe_load(workflow.read_text(encoding="utf-8"))["git_delivery"]["remote_url"]
    (project_copy / "README.md").write_text(remote_url, encoding="utf-8")
    assert "GIT_DELIVERY_REMOTE_TRUTH_COUNT" in _ids(validate_repo(project_copy, strict=True))
