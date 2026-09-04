from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head_commit(repo_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def command(repo_root: Path, script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo_root / "scripts" / script), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def legacy_development_start_is_locked(state: dict) -> bool:
    return (
        state.get("next_phase_allowed") == "PHASE-SKILL-VALIDATION-EVAL-004-C"
        or state.get("phase") == "PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C"
    )


def load_script(repo_root: Path, name: str):
    path = repo_root / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"test_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_development_eval_requires_accepted_rc_and_aware_monotonic_times(
    repo_root: Path, tmp_path: Path
) -> None:
    start = load_script(repo_root, "start_skill_development_eval.py")
    freeze = load_script(repo_root, "freeze_skill_first_run.py")
    project_state = tmp_path / "project_state.json"
    project_state.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="COMPETITION_RC_NOT_READY_FOR_DEVELOPMENT_EVAL"):
        start.require_competition_rc_ready(project_state)
    ready = {
        "technical_adjudication_status": "COMPETITION_SKILL_RC_READY",
        "next_phase_allowed": "PHASE-SKILL-DEVELOPMENT-EVAL-004",
        "active_skill_version": start.SKILL_VERSION,
        "competition_rc1": {"integration_audit": {"status": "PASS"}},
    }
    project_state.write_text(json.dumps(ready) + "\n", encoding="utf-8")
    start.require_competition_rc_ready(project_state)

    cross_type_ready = json.loads(json.dumps(ready))
    cross_type_ready.update(
        {
            "phase": "PHASE-SKILL-DEVELOPMENT-EVAL-004",
            "technical_adjudication_status": "DEVELOPMENT_EVAL_RC2_READY",
            "next_phase_allowed": "PHASE-SKILL-DEVELOPMENT-EVAL-004-B",
        }
    )
    project_state.write_text(json.dumps(cross_type_ready) + "\n", encoding="utf-8")
    start.require_competition_rc_ready(project_state)

    wrong_route = json.loads(json.dumps(cross_type_ready))
    wrong_route["next_phase_allowed"] = "PHASE-SKILL-VALIDATION-EVAL-004-C"
    project_state.write_text(json.dumps(wrong_route) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="COMPETITION_RC_NOT_READY_FOR_DEVELOPMENT_EVAL"):
        start.require_competition_rc_ready(project_state)

    for wrong_type in ([], True, "PASS", 0):
        wrong = json.loads(json.dumps(ready))
        wrong["competition_rc1"]["integration_audit"] = wrong_type
        project_state.write_text(json.dumps(wrong) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="COMPETITION_RC_NOT_READY_FOR_DEVELOPMENT_EVAL"):
            start.require_competition_rc_ready(project_state)

    with pytest.raises(ValueError, match="START_TIME_TIMEZONE_REQUIRED"):
        start.iso_time("2026-09-04T00:00:00")
    with pytest.raises(ValueError, match="FREEZE_TIME_TIMEZONE_REQUIRED"):
        freeze.iso_time("2026-09-04T01:00:00", "FREEZE_TIME_INVALID")
    with pytest.raises(ValueError, match="FREEZE_TIME_BEFORE_START"):
        freeze.validate_timeline("2026-09-04T02:00:00Z", "2026-09-04T01:00:00Z")
    freeze.validate_timeline("2026-09-04T00:00:00Z", "2026-09-04T02:00:00Z")
    assert freeze.REASON_CODE.fullmatch("RC_MODEL_FAILED:TIMEOUT")
    assert freeze.REASON_CODE.fullmatch("arbitrary sensitive explanation") is None

    active = json.loads(json.dumps(ready))
    active.update(
        {
            "phase": "PHASE-SKILL-DEVELOPMENT-EVAL-004",
            "technical_adjudication_status": "DEVELOPMENT_EVAL_INCOMPLETE",
            "next_phase_allowed": None,
        }
    )
    project_state.write_text(json.dumps(active) + "\n", encoding="utf-8")
    start.require_competition_rc_ready(project_state, allow_active_eval=True)
    with pytest.raises(ValueError, match="COMPETITION_RC_NOT_READY_FOR_DEVELOPMENT_EVAL"):
        start.require_competition_rc_ready(project_state, allow_active_eval=False)


def test_phase004_registry_readers_fail_closed_on_non_object_case(
    repo_root: Path, tmp_path: Path
) -> None:
    start = load_script(repo_root, "start_skill_development_eval.py")
    freeze = load_script(repo_root, "freeze_skill_first_run.py")
    registry = tmp_path / "registry.yaml"
    registry.write_text("cases:\n  - true\n", encoding="utf-8")

    for module in (start, freeze):
        with pytest.raises(ValueError, match="DEVELOPMENT_REGISTRY_INVALID"):
            module.read_registry(registry)


def test_case_registry_declares_required_training_fields(repo_root: Path) -> None:
    registry = yaml.safe_load(
        (repo_root / "benchmarks/case_registry.yaml").read_text(encoding="utf-8")
    )
    assert len(registry["cases"]) == 6
    assert registry["cases"][0]["case_id"] == "CUMCM-2023-C-DEVELOPMENT-001"
    assert registry["cases"][0]["answer_access_status"] == "UNLOCKED_AFTER_FIRST_RUN"
    assert registry["cases"][0]["first_run_status"] == "FROZEN"
    assert registry["cases"][1]["case_id"] == "CUMCM-2020-A-DEVELOPMENT-002"
    assert registry["cases"][1]["answer_access_status"] == "UNLOCKED_AFTER_FIRST_RUN"
    assert registry["cases"][1]["first_run_status"] == "FROZEN"
    batch = [case for case in registry["cases"] if case.get("batch_id") == "C-TARGET-BATCH-001"]
    assert len(batch) == 3
    assert all(case["answer_access_status"] == "UNLOCKED_AFTER_FIRST_RUN" for case in batch)
    assert all(case["reference_unlock"] == "UNLOCKED_AFTER_ALL_FIRST_RUN_FREEZES" for case in batch)
    assert all(case["first_run_status"] in {"IN_PROGRESS", "FROZEN"} for case in batch)
    assert any(case["first_run_status"] == "FROZEN" for case in batch)
    assert all(
        (case["first_run_status"] == "FROZEN") == isinstance(case["first_run_freeze"], dict)
        for case in batch
    )
    validation = next(
        case for case in registry["cases"] if case.get("case_id") == "CUMCM-2024-C-VALIDATION-001"
    )
    assert validation["set_type"] == "VALIDATION"
    assert validation["answer_access_status"] == "SEALED"
    assert validation["first_run_status"] == "IN_PROGRESS"
    assert validation["first_run_freeze"] is None
    assert validation["pre_run_freeze"]["status"] == "REMOTE_DELIVERED"
    assert validation["skill_version"] == "0.2.0-competition-rc4"
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
    isolated = yaml.safe_load(registry.read_text(encoding="utf-8"))
    isolated["cases"] = []
    registry.write_text(yaml.safe_dump(isolated, sort_keys=False), encoding="utf-8")
    case_root = tmp_path / "case"
    problem = case_root / "problem/original.md"
    data = case_root / "data/raw/input.dat"
    problem.parent.mkdir(parents=True)
    data.parent.mkdir(parents=True)
    problem.write_text("opaque synthetic problem", encoding="utf-8")
    data.write_text("opaque synthetic data", encoding="utf-8")
    arguments = (
        "--registry",
        str(registry),
        "--case-id",
        "DEV-START-001",
        "--set-type",
        "DEVELOPMENT",
        "--problem-source",
        "problem/original.md",
        "--problem-hash",
        file_hash(problem),
        "--data-hash",
        f"data/raw/input.dat={file_hash(data)}",
        "--skill-commit",
        head_commit(repo_root),
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
    state = json.loads((repo_root / "state/project_state.json").read_text(encoding="utf-8"))
    if legacy_development_start_is_locked(state):
        assert started.returncode == 3
        assert json.loads(started.stdout)["reason_codes"] == [
            "COMPETITION_RC_NOT_READY_FOR_DEVELOPMENT_EVAL"
        ]
        return
    assert started.returncode == 0, started.stdout + started.stderr
    record = yaml.safe_load(registry.read_text(encoding="utf-8"))["cases"][0]
    assert record["answer_access_status"] == "SEALED"
    assert record["first_run_status"] == "IN_PROGRESS"
    assert record["skill_version"] == "0.2.0-competition-rc3"
    assert (case_root / "case_state.json").is_file()
    duplicate = command(repo_root, "start_skill_development_eval.py", *arguments)
    assert duplicate.returncode == 3
    assert json.loads(duplicate.stdout)["reason_codes"] == ["CASE_ID_ALREADY_REGISTERED"]


def test_start_rejects_nonexistent_skill_commit(repo_root: Path, tmp_path: Path) -> None:
    registry = tmp_path / "registry.yaml"
    shutil.copyfile(repo_root / "benchmarks/case_registry.yaml", registry)
    isolated = yaml.safe_load(registry.read_text(encoding="utf-8"))
    isolated["cases"] = []
    registry.write_text(yaml.safe_dump(isolated, sort_keys=False), encoding="utf-8")
    case_root = tmp_path / "case"
    problem = case_root / "problem/original.md"
    problem.parent.mkdir(parents=True)
    problem.write_text("opaque synthetic problem", encoding="utf-8")

    rejected = command(
        repo_root,
        "start_skill_development_eval.py",
        "--registry",
        str(registry),
        "--case-id",
        "DEV-COMMIT-003",
        "--set-type",
        "DEVELOPMENT",
        "--problem-source",
        "problem/original.md",
        "--problem-hash",
        file_hash(problem),
        "--skill-commit",
        "f" * 40,
        "--model",
        "MODEL-ID",
        "--reasoning",
        "medium",
        "--case-root",
        str(case_root),
    )

    state = json.loads((repo_root / "state/project_state.json").read_text(encoding="utf-8"))
    if legacy_development_start_is_locked(state):
        assert rejected.returncode == 3
        assert json.loads(rejected.stdout)["reason_codes"] == [
            "COMPETITION_RC_NOT_READY_FOR_DEVELOPMENT_EVAL"
        ]
        return
    assert rejected.returncode == 3
    assert json.loads(rejected.stdout)["reason_codes"] == ["SKILL_COMMIT_NOT_FOUND"]
    assert yaml.safe_load(registry.read_text(encoding="utf-8"))["cases"] == []


def test_freeze_binds_terminal_first_run_before_optional_unlock(
    repo_root: Path, tmp_path: Path
) -> None:
    registry = tmp_path / "registry.yaml"
    shutil.copyfile(repo_root / "benchmarks/case_registry.yaml", registry)
    isolated = yaml.safe_load(registry.read_text(encoding="utf-8"))
    isolated["cases"] = []
    registry.write_text(yaml.safe_dump(isolated, sort_keys=False), encoding="utf-8")
    case_root = tmp_path / "case"
    problem = case_root / "problem/original.md"
    raw = case_root / "data/raw/prediction_rows.json"
    problem.parent.mkdir(parents=True)
    raw.parent.mkdir(parents=True)
    problem.write_text("project-original synthetic prediction", encoding="utf-8")
    rows = [
        {
            "time": index,
            "target": 2 * index + 1 if index != 5 else None,
            "future_target": 2 * (index + 1) + 1,
        }
        for index in range(1, 13)
    ]
    rows[5]["target"] = 99
    raw.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    commit = head_commit(repo_root)
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
        "problem/original.md",
        "--problem-hash",
        file_hash(problem),
        "--data-hash",
        f"data/raw/prediction_rows.json={file_hash(raw)}",
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
        "--case-kind",
        "prediction",
    )
    state = json.loads((repo_root / "state/project_state.json").read_text(encoding="utf-8"))
    if legacy_development_start_is_locked(state):
        assert started.returncode == 3
        assert json.loads(started.stdout)["reason_codes"] == [
            "COMPETITION_RC_NOT_READY_FOR_DEVELOPMENT_EVAL"
        ]
        return
    assert started.returncode == 0, started.stdout + started.stderr
    smoke = subprocess.run(
        [
            sys.executable,
            str(repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"),
            "smoke",
            "--case-root",
            str(case_root),
            "--case-id",
            "DEV-FREEZE-002",
            "--kind",
            "prediction",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert smoke.returncode == 0, smoke.stdout + smoke.stderr
    manifest_path = sorted(case_root.glob("runs/*/manifest.json"))[0]
    manifest_original = manifest_path.read_text(encoding="utf-8")
    state_path = case_root / "case_state.json"
    state_original = state_path.read_text(encoding="utf-8")
    manifest_path.write_text(
        json.dumps({"run_id": manifest_path.parent.name, "code_commit": commit}) + "\n",
        encoding="utf-8",
    )
    tampered_state = json.loads(state_original)
    relative_manifest = str(manifest_path.relative_to(case_root))
    tampered_state["evidence_bindings"][relative_manifest] = file_hash(manifest_path)
    state_path.write_text(
        json.dumps(tampered_state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    shallow = command(
        repo_root,
        "freeze_skill_first_run.py",
        "--registry",
        str(registry),
        "--case-id",
        "DEV-FREEZE-002",
        "--case-root",
        str(case_root),
        "--freeze-output",
        str(tmp_path / "first_run_freeze.json"),
        "--worktree-commit",
        commit,
        "--freeze-time",
        "2026-09-04T01:00:00Z",
        "--dry-run",
    )
    assert shallow.returncode == 3
    assert "RC_MANIFEST_REQUIRED_BINDING_MISSING" in " ".join(
        json.loads(shallow.stdout)["reason_codes"]
    )
    manifest_path.write_text(manifest_original, encoding="utf-8")
    state_path.write_text(state_original, encoding="utf-8")
    frozen = command(
        repo_root,
        "freeze_skill_first_run.py",
        "--registry",
        str(registry),
        "--case-id",
        "DEV-FREEZE-002",
        "--case-root",
        str(case_root),
        "--freeze-output",
        str(repo_root / "evals/results/phase-004a/test-first-run-freeze.json"),
        "--worktree-commit",
        commit,
        "--freeze-time",
        "2026-09-04T01:00:00Z",
    )
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    record = yaml.safe_load(registry.read_text(encoding="utf-8"))["cases"][0]
    assert record["first_run_status"] == "FROZEN"
    assert record["answer_access_status"] == "SEALED"
    assert record["first_run_evidence"]["skill_commit"] == commit
    assert record["first_run_evidence"]["case_state"] == "READY_FOR_PAPER_HANDOFF"
    assert record["first_run_evidence"]["run_manifest_hashes"]
    (repo_root / "evals/results/phase-004a/test-first-run-freeze.json").unlink()


def test_blocked_freeze_requires_failure_evidence_and_writes_no_fake_run(
    repo_root: Path, tmp_path: Path
) -> None:
    freeze = load_script(repo_root, "freeze_skill_first_run.py")
    case_root = tmp_path / "case"
    case_root.mkdir()
    with pytest.raises(ValueError, match="FIRST_RUN_EVIDENCE_MISSING"):
        freeze.evidence_hashes(case_root, blocked=True)
    for relative in freeze.REQUIRED_BLOCKED_EVIDENCE:
        path = case_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    hashes = freeze.evidence_hashes(case_root, blocked=True)
    assert set(hashes) == set(freeze.REQUIRED_BLOCKED_EVIDENCE)
    assert not list(case_root.glob("runs/*/manifest.json"))


def test_batch_freeze_requires_complete_evidence_and_hashes_case_code_tree(
    repo_root: Path, tmp_path: Path
) -> None:
    freeze = load_script(repo_root, "freeze_skill_first_run.py")
    case_root = tmp_path / "case"
    case_root.mkdir()
    with pytest.raises(ValueError, match="FIRST_RUN_EVIDENCE_MISSING"):
        freeze.evidence_hashes(case_root, blocked=False, batch_case=True)

    for relative in freeze.BATCH_SUCCESS_EVIDENCE:
        path = case_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    code = case_root / "models/model.py"
    code.parent.mkdir(parents=True, exist_ok=True)
    code.write_text("print('model')\n", encoding="utf-8")
    plan = {
        "content": {
            "required_code_files": [
                {
                    "scope": "CASE_ROOT",
                    "path": "models/model.py",
                    "repository_path": "evals/results/case/code/model.py",
                    "sha256": file_hash(code),
                }
            ]
        }
    }
    plan_path = case_root / "experiments/experiment_plan.json"
    plan_path.write_text(json.dumps(plan) + "\n", encoding="utf-8")
    metrics_path = case_root / "evidence/first_run_metrics.json"
    metrics_path.write_text(
        json.dumps({"content": {"manual_intervention_count": 0}}) + "\n",
        encoding="utf-8",
    )

    hashes = freeze.evidence_hashes(case_root, blocked=False, batch_case=True)
    assert set(freeze.BATCH_SUCCESS_EVIDENCE).issubset(hashes)
    assert len(freeze.case_code_tree_hash(case_root, plan_path)) == 64
    assert freeze.manual_intervention_count(metrics_path) == 0

    code.write_text("print('drift')\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CASE_CODE_HASH_MISMATCH"):
        freeze.case_code_tree_hash(case_root, plan_path)


def test_freeze_separates_skill_commit_from_case_execution_commit(repo_root: Path) -> None:
    freeze = load_script(repo_root, "freeze_skill_first_run.py")
    core = freeze.load_core()
    skill_commit = "1d842a45403370916ce2c36297876e9cd1ddde1f"
    runner_path = ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
    runner_sha256 = core.git_blob_hash(skill_commit, runner_path)
    manifest = {
        "code_commit": head_commit(repo_root),
        "code_files": [
            {
                "scope": "SKILL_ROOT",
                "path": "scripts/cumcm_case.py",
                "repository_path": runner_path,
                "sha256": runner_sha256,
            },
            {
                "scope": "CASE_ROOT",
                "path": "models/case_model.py",
                "repository_path": "case/code.py",
                "sha256": "a" * 64,
            },
        ],
    }
    freeze.validate_manifest_skill_binding(core, {"skill_commit": skill_commit}, manifest)
    manifest["code_files"][0]["sha256"] = "b" * 64
    with pytest.raises(ValueError, match="RUN_SKILL_COMMIT_MISMATCH"):
        freeze.validate_manifest_skill_binding(core, {"skill_commit": skill_commit}, manifest)


def test_unlock_rejects_unverified_remote_freeze(repo_root: Path, tmp_path: Path) -> None:
    unlock = load_script(repo_root, "unlock_skill_first_run.py")
    assert unlock.parsed_time("2026-09-04T02:00:00Z", "UNLOCK_TIME_INVALID")
    with pytest.raises(ValueError, match="UNLOCK_TIME_TIMEZONE_REQUIRED"):
        unlock.parsed_time("2026-09-04T02:00:00", "UNLOCK_TIME_INVALID")
