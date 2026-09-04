from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from scripts.check_target_problem_policy import evaluate


def _copy_target_inputs(repo_root: Path, target: Path) -> Path:
    for relative in (
        "rules/target_problem_policy.yaml",
        "rules/workflow_rules.yaml",
        "benchmarks/case_registry.yaml",
        "state/project_state.json",
        "plans/active/PLAN-0004C-C-target-batch-generalization.md",
        ".agents/skills/cumcm-modeling-evidence/SKILL.md",
    ):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_root / relative, destination)
    return target


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_yaml(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def test_target_problem_policy_accepts_canonical_strategy(repo_root: Path) -> None:
    result = evaluate(repo_root)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["planned_independent_c_share"] == 0.8
    assert result["realized_independent_c_share"] == 0.5
    assert result["batch_case_count"] == 3
    assert result["held_out_reservation_count"] == 1
    assert result["formal_skill_count"] == 1


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("primary_target", "A", "TARGET_POLICY_FIELD_MISMATCH:primary_target"),
        ("validation_target", "A", "TARGET_POLICY_FIELD_MISMATCH:validation_target"),
        ("a_problem_role", "PRIMARY", "TARGET_POLICY_FIELD_MISMATCH:a_problem_role"),
        (
            "post_result_same_case_validation_rerun",
            "ALLOWED",
            "TARGET_POLICY_FIELD_MISMATCH:post_result_same_case_validation_rerun",
        ),
    ],
)
def test_target_problem_policy_rejects_policy_drift(
    repo_root: Path, tmp_path: Path, field: str, value: object, reason: str
) -> None:
    root = _copy_target_inputs(repo_root, tmp_path / "project")
    path = root / "rules/target_problem_policy.yaml"
    policy = _yaml(path)
    policy[field] = value
    _write_yaml(path, policy)

    assert reason in evaluate(root)["errors"]


def test_target_problem_policy_rejects_allocation_below_eighty_percent(
    repo_root: Path, tmp_path: Path
) -> None:
    root = _copy_target_inputs(repo_root, tmp_path / "project")
    path = root / "benchmarks/case_registry.yaml"
    registry = _yaml(path)
    registry["planned_cases"].append(
        {
            "case_id": "AUXILIARY-A-EXTRA",
            "set_type": "DEVELOPMENT",
            "target_problem_type": "A",
            "evidence_role": "AUXILIARY_TRANSFER_ONLY",
            "independent_problem": True,
        }
    )
    _write_yaml(path, registry)

    result = evaluate(root)
    assert "TARGET_INDEPENDENT_C_ALLOCATION_SHARE_TOO_LOW" in result["errors"]


def test_target_problem_policy_rejects_batch_position_and_skill_drift(
    repo_root: Path, tmp_path: Path
) -> None:
    root = _copy_target_inputs(repo_root, tmp_path / "project")
    path = root / "benchmarks/case_registry.yaml"
    registry = _yaml(path)
    batch = [
        item
        for item in [*registry["planned_cases"], *registry["cases"]]
        if item.get("batch_id") == "C-TARGET-BATCH-001"
    ]
    batch[1]["batch_position"] = 1
    batch[2]["formal_skill_commit"] = "0" * 40
    _write_yaml(path, registry)

    errors = evaluate(root)["errors"]
    assert "TARGET_BATCH_POSITION_SET_INVALID" in errors
    assert any(error.startswith("TARGET_BATCH_CASE_CONTRACT_INVALID:") for error in errors)


def test_target_problem_policy_rejects_registered_input_evidence_drift(
    repo_root: Path, tmp_path: Path
) -> None:
    root = _copy_target_inputs(repo_root, tmp_path / "project")
    path = root / "benchmarks/case_registry.yaml"
    registry = _yaml(path)
    batch = [item for item in registry["cases"] if item.get("batch_id") == "C-TARGET-BATCH-001"]
    batch[0]["official_package_sha256"] = "UNKNOWN"
    _write_yaml(path, registry)

    errors = evaluate(root)["errors"]
    assert any(error.startswith("TARGET_BATCH_REGISTERED_INPUT_INVALID:") for error in errors)


def test_target_problem_policy_rejects_held_out_access_or_metadata(
    repo_root: Path, tmp_path: Path
) -> None:
    root = _copy_target_inputs(repo_root, tmp_path / "project")
    path = root / "benchmarks/case_registry.yaml"
    registry = _yaml(path)
    reservation = registry["held_out_reservations"][0]
    reservation["archive_accessed"] = True
    reservation["official_title"] = "forbidden"
    _write_yaml(path, registry)

    errors = evaluate(root)["errors"]
    assert "TARGET_HELD_OUT_RESERVATION_INVALID" in errors
    assert "TARGET_HELD_OUT_FORBIDDEN_FIELD:official_title" in errors


def test_target_problem_policy_rejects_state_and_plan_drift(
    repo_root: Path, tmp_path: Path
) -> None:
    root = _copy_target_inputs(repo_root, tmp_path / "project")
    state_path = root / "state/project_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["batch_skill_frozen"] = False
    state_path.write_text(json.dumps(state), encoding="utf-8")
    plan_path = root / "plans/active/PLAN-0004C-C-target-batch-generalization.md"
    plan_path.write_text("missing bindings\n", encoding="utf-8")

    errors = evaluate(root)["errors"]
    assert "TARGET_STATE_FIELD_MISMATCH:batch_skill_frozen" in errors
    assert any(error.startswith("TARGET_ACTIVE_PLAN_TOKEN_MISSING:") for error in errors)
