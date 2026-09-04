from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def command(repo_root: Path, script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo_root / "scripts" / script), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def test_case_registry_declares_required_training_fields(repo_root: Path) -> None:
    registry = yaml.safe_load(
        (repo_root / "benchmarks/case_registry.yaml").read_text(encoding="utf-8")
    )
    assert registry["cases"] == []
    assert set(registry["allowed_set_types"]) == {
        "DEVELOPMENT",
        "VALIDATION",
        "HELD_OUT",
        "STRESS",
    }
    assert set(registry["required_case_fields"]) == {
        "case_id",
        "set_type",
        "problem_source",
        "problem_hash",
        "data_hashes",
        "answer_access_status",
        "first_run_status",
        "skill_version",
        "skill_commit",
        "model",
        "reasoning",
        "start_time",
        "freeze_time",
        "unlock_time",
        "generalizable_failures",
        "problem_specific_findings",
    }


def test_start_registers_sealed_case_and_rejects_duplicate(repo_root: Path, tmp_path: Path) -> None:
    registry = tmp_path / "registry.yaml"
    shutil.copyfile(repo_root / "benchmarks/case_registry.yaml", registry)
    case_root = tmp_path / "case"
    arguments = (
        "--registry",
        str(registry),
        "--case-id",
        "DEV-START-001",
        "--set-type",
        "DEVELOPMENT",
        "--problem-source",
        "OPAQUE-SOURCE-001",
        "--problem-hash",
        "1" * 64,
        "--data-hash",
        f"input.dat={'2' * 64}",
        "--skill-commit",
        "3" * 40,
        "--model",
        "MODEL-ID",
        "--reasoning",
        "medium",
        "--start-time",
        "2026-09-04T00:00:00Z",
        "--case-root",
        str(case_root),
    )
    started = command(repo_root, "start_skill_development_eval.py", *arguments)
    assert started.returncode == 0, started.stdout + started.stderr
    record = yaml.safe_load(registry.read_text(encoding="utf-8"))["cases"][0]
    assert record["answer_access_status"] == "SEALED"
    assert record["first_run_status"] == "IN_PROGRESS"
    assert record["skill_version"] == "0.2.0-competition-rc1"
    assert (case_root / "case_state.json").is_file()
    duplicate = command(repo_root, "start_skill_development_eval.py", *arguments)
    assert duplicate.returncode == 3
    assert json.loads(duplicate.stdout)["reason_codes"] == ["CASE_ID_ALREADY_REGISTERED"]


def test_freeze_binds_terminal_first_run_before_optional_unlock(
    repo_root: Path, tmp_path: Path
) -> None:
    registry = tmp_path / "registry.yaml"
    shutil.copyfile(repo_root / "benchmarks/case_registry.yaml", registry)
    case_root = tmp_path / "case"
    run_dir = case_root / "runs/RUN-FAILED"
    run_dir.mkdir(parents=True)
    commit = "4" * 40
    (case_root / "case_state.json").write_text(
        json.dumps(
            {
                "case_id": "DEV-FREEZE-002",
                "skill_version": "0.2.0-competition-rc1",
                "state": "REJECTED",
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": "RUN-FAILED", "code_commit": commit}),
        encoding="utf-8",
    )
    started = command(
        repo_root,
        "start_skill_development_eval.py",
        "--registry",
        str(registry),
        "--case-id",
        "DEV-FREEZE-002",
        "--set-type",
        "DEVELOPMENT",
        "--problem-source",
        "OPAQUE-SOURCE-002",
        "--problem-hash",
        "5" * 64,
        "--skill-commit",
        commit,
        "--model",
        "MODEL-ID",
        "--reasoning",
        "medium",
        "--start-time",
        "2026-09-04T00:00:00Z",
        "--case-root",
        str(case_root),
    )
    assert started.returncode == 0, started.stdout + started.stderr
    frozen = command(
        repo_root,
        "freeze_skill_first_run.py",
        "--registry",
        str(registry),
        "--case-id",
        "DEV-FREEZE-002",
        "--case-root",
        str(case_root),
        "--freeze-time",
        "2026-09-04T01:00:00Z",
    )
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    record = yaml.safe_load(registry.read_text(encoding="utf-8"))["cases"][0]
    assert record["first_run_status"] == "FROZEN"
    assert record["answer_access_status"] == "SEALED"
    assert record["first_run_evidence"]["skill_commit"] == commit
    assert record["first_run_evidence"]["case_state"] == "REJECTED"
    assert record["first_run_evidence"]["run_manifest_hashes"]
