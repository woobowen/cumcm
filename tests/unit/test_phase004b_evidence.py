from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

from cumcm_skill_lab.historical_compat import competition_rc_successor

CASE_ROOT = Path("evals/results/phase-004b/CUMCM-2020-A-DEVELOPMENT-002")


def load_json(repo_root: Path, relative: Path | str) -> dict:
    return json.loads((repo_root / relative).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_phase004b_freeze_is_sealed_and_byte_bound(repo_root: Path) -> None:
    path = repo_root / CASE_ROOT / "first_run/first_run_freeze.json"
    value = load_json(repo_root, path.relative_to(repo_root))
    registry = yaml.safe_load(
        (repo_root / "benchmarks/case_registry.yaml").read_text(encoding="utf-8")
    )
    case = next(
        item for item in registry["cases"] if item["case_id"] == "CUMCM-2020-A-DEVELOPMENT-002"
    )

    assert value["answer_access_status"] == "SEALED"
    assert value["first_run_status"] == "FROZEN"
    assert value["blocked_reason_code"] == "RC_RUN_SUCCESS_SET_INSUFFICIENT"
    assert case["first_run_freeze"]["sha256"] == sha256(path)
    assert case["unlock_receipt"]["freeze_commit"] == ("b742e8e042a1e9f0c161806c89c1b5917abe5693")
    assert case["unlock_receipt"]["verified_remote_sha"] == (
        "b742e8e042a1e9f0c161806c89c1b5917abe5693"
    )


def test_phase004b_development_regression_is_complete_and_not_blind(
    repo_root: Path,
) -> None:
    value = load_json(repo_root, CASE_ROOT / "rc3/development_regression_evidence.json")
    runs = value["runs"]

    assert value["skill"]["version"] == "0.2.0-competition-rc3"
    assert value["evidence_class"] == "DEVELOPMENT_REGRESSION_NOT_BLIND_NOT_VALIDATION"
    assert value["answer_access_status"] == "UNLOCKED_AFTER_FIRST_RUN"
    assert value["final_state"] == "READY_FOR_PAPER_HANDOFF"
    assert value["selected_model"] == "PRIMARY_ASYMMETRIC_FIRST_ORDER"
    assert len(runs) == 6
    assert all(run["exit_code"] == 0 and run["outcome"] == "SUCCESS" for run in runs)
    assert len({run["manifest_sha256"] for run in runs}) == 6
    assert value["handoff"]["contract"] == "modeling-to-paper/v1"
    assert value["handoff"]["claim_count"] == 6
    assert value["scientific_validity"]["constraint_feasibility"] == ("PASS_SELECTED_RUN_ONLY")
    assert value["scientific_validity"]["external_validity"] == "NOT_ESTABLISHED"
    assert (
        value["numerical_validation"]["maximum_absolute_temperature_difference_c"]
        < (value["numerical_validation"]["refinement_threshold_c"])
    )


def test_phase004b_stress_semantics_and_stale_propagation(repo_root: Path) -> None:
    values = {
        key: load_json(repo_root, CASE_ROOT / f"stress/stress_{key.lower()}_evidence.json")
        for key in "ABC"
    }

    assert values["A"]["conversion_metadata"]["time_to_seconds"] == 60.0
    assert values["A"]["reference_comparison"]["tolerance_pass"] is True
    assert values["B"]["process_representation"]["coordinate_sort_required"] is True
    assert values["B"]["reference_comparison"]["tolerance_pass"] is True
    assert values["C"]["observation_degradation"]["noise_seed"] == 20260907
    assert values["C"]["uncertainty"]["reported_parameter_significant_digits"] == 4
    assert (
        values["C"]["uncertainty"]["stress_validation_rmse_c"]
        > (values["C"]["uncertainty"]["original_validation_rmse_c"])
    )
    for value in values.values():
        assert value["result"] == "PASS"
        assert value["final_state"] == "READY_FOR_PAPER_HANDOFF"
        assert value["stale_probe"]["status"] == "STALE"
        assert value["stale_probe"]["reason_code"] == "RC_UPSTREAM_DEPENDENCY_STALE"
        assert len(value["runs"]) == 2
        assert all(run["exit_code"] == 0 for run in value["runs"])


def test_phase004b_cross_case_replay_preserves_rc2_outputs(repo_root: Path) -> None:
    value = load_json(
        repo_root,
        CASE_ROOT / "cross_case_regression/cumcm_2023c_rc3.json",
    )

    assert value["result"] == "PASS"
    assert value["skill_version"] == "0.2.0-competition-rc3"
    assert value["selected_model"] == "PIPELINE-HIERARCHICAL-STOCHASTIC"
    assert value["final_state"] == "READY_FOR_PAPER_HANDOFF"
    assert all(value["comparison_to_rc2"].values())
    assert all(result == "PASS" for result in value["executor_checks"].values())
    assert value["handoff"]["contract"] == "modeling-to-paper/v1"
    assert value["stale_probe"]["status"] == "STALE"
    assert len(value["runs"]) == 3
    assert all(run["exit_code"] == 0 for run in value["runs"])


def test_phase004c_handoff_freezes_rc3_without_starting_validation(
    repo_root: Path,
) -> None:
    release = load_json(repo_root, CASE_ROOT / "rc3/skill_release.json")
    handoff = load_json(repo_root, "evals/results/phase-004b/phase004c_validation_handoff.json")

    assert handoff["status"] == "READY_FOR_VALIDATION_INTAKE_NOT_STARTED"
    assert handoff["validation_started"] is False
    assert handoff["answer_access_policy"] == "SEALED_UNTIL_VALIDATION_RESULT_FREEZE"
    assert handoff["next_phase"] == "PHASE-SKILL-VALIDATION-EVAL-004-C"
    assert handoff["no_post_result_tuning"] is True
    assert handoff["frozen_skill"]["version"] == release["formal_skill"]["version"]
    assert handoff["frozen_skill"]["commit"] == release["formal_skill"]["commit"]
    assert handoff["frozen_skill"]["git_tree"] == release["formal_skill"]["git_tree"]
    assert len(handoff["development_cases"]) == 2


def test_phase004b_training_checker_accepts_complete_evidence(repo_root: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/check_skill_training_consistency.py"),
            "--check",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout)["ok"] is True


def test_rc3_ready_state_replays_frozen_predecessors_from_git(repo_root: Path) -> None:
    assert competition_rc_successor(repo_root) is True
