from __future__ import annotations

import copy
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def skill_root(repo_root: Path) -> Path:
    return repo_root / ".agents/skills/cumcm-modeling-evidence"


@pytest.fixture
def case_cli(skill_root: Path):
    path = skill_root / "scripts/cumcm_case.py"
    spec = importlib.util.spec_from_file_location("cumcm_case_rc", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_skill_is_competition_rc_and_has_one_workflow_set(skill_root: Path) -> None:
    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert "0.2.0-competition-rc3" in skill
    assert "COMPETITION_RC" in skill
    assert len(list((skill_root / "workflows").glob("*.md"))) == 14
    assert len([path for path in (skill_root / "agents").glob("*.md")]) == 4
    assert not (skill_root / "reviewers").exists() or not list(
        (skill_root / "reviewers").glob("*.md")
    )


def test_cli_help_and_dry_run_are_structured(skill_root: Path, tmp_path: Path) -> None:
    cli = skill_root / "scripts/cumcm_case.py"
    help_result = subprocess.run(
        [sys.executable, str(cli), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert help_result.returncode == 0
    for command in (
        "init",
        "status",
        "validate",
        "manifest",
        "claim-check",
        "compare-check",
        "stale-check",
        "finalize",
        "handoff",
        "smoke",
    ):
        assert command in help_result.stdout

    dry_run = subprocess.run(
        [
            sys.executable,
            str(cli),
            "init",
            "--case-root",
            str(tmp_path / "case"),
            "--case-id",
            "DRY-RUN-001",
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert dry_run.returncode == 0
    assert json.loads(dry_run.stdout)["dry_run"] is True
    assert not (tmp_path / "case").exists()


def test_init_creates_isolated_workspace_and_draft_templates(case_cli, tmp_path: Path) -> None:
    case_root = tmp_path / "case"
    state = case_cli.initialize_case(case_root, "SYNTH-UNIT-001", "general")
    assert state["state"] == "CREATED"
    assert (case_root / "case_state.json").is_file()
    assert not list((case_root / "data/raw").iterdir())
    for relative in case_cli.CASE_DIRS:
        assert (case_root / relative).is_dir()
    for relative in case_cli.ARTIFACT_PATHS.values():
        assert (case_root / relative).is_file()
    final_template = json.loads((case_root / "results/final_result.json").read_text())
    assert set(final_template["content"]) == {
        "status",
        "selected_model",
        "run_id",
        "output_hash",
        "decision_hash",
        "final_metrics",
        "claim_scope",
    }
    plan_template = json.loads((case_root / "experiments/experiment_plan.json").read_text())
    assert {"required_input_hashes", "handoff_generated_at", "stop_rule"} <= set(
        plan_template["content"]
    )
    problem_template = json.loads((case_root / "problem/problem_requirements.json").read_text())
    assert problem_template["content"]["case_id"] == "SYNTH-UNIT-001"
    with pytest.raises(ValueError, match="RC_CASE_ALREADY_INITIALIZED"):
        case_cli.initialize_case(case_root, "SYNTH-UNIT-001", "general")


@pytest.mark.parametrize(
    ("payload", "context", "reason"),
    [
        ({}, None, "RC_CONTEXT_INVALID"),
        ({}, {"stage": 1, "enabled_components": ["x"]}, "RC_CONTEXT_STAGE_INVALID"),
        (
            {},
            {"stage": "PROBLEM_INTAKE", "enabled_components": "x"},
            "RC_CONTEXT_ENABLED_COMPONENTS_INVALID",
        ),
        (
            {"score": math.nan},
            {"stage": "PROBLEM_INTAKE", "enabled_components": ["x"]},
            "RC_BOUNDARY_NONFINITE_OR_NONJSON",
        ),
    ],
)
def test_boundary_fail_closed_without_input_mutation(
    case_cli, payload, context, reason: str
) -> None:
    before = copy.deepcopy((payload, context))
    result = case_cli.boundary_validate(payload, context)
    assert result.status == "BLOCK"
    assert result.accepted is False
    assert result.final is False
    assert reason in result.reason_codes
    assert (payload, context) == before


def test_state_boundary_rejects_formal_or_second_truth(case_cli) -> None:
    result = case_cli.validate_state_boundary(
        {
            "writer": "unknown",
            "formal_project_state_write": True,
            "second_state_truth": True,
            "execution_scope": "PRODUCTION",
            "state_path": "state/project_state.json",
        }
    )
    assert result.status == "BLOCK"
    assert {
        "RC_STATE_UNAUTHORIZED_WRITER",
        "RC_FORMAL_STATE_WRITE_PROHIBITED",
        "RC_SECOND_STATE_TRUTH_PROHIBITED",
        "RC_CONTEXT_EXECUTION_SCOPE_PROHIBITED",
        "RC_CASE_STATE_BINDING_INVALID",
    } <= set(result.reason_codes)


def test_templates_are_json_and_handoff_fields_match_contract(skill_root: Path) -> None:
    templates = list((skill_root / "templates").glob("*.json"))
    assert len(templates) == 14
    for path in templates:
        json.loads(path.read_text(encoding="utf-8"))
    handoff = json.loads(
        (skill_root / "templates/modeling_to_paper_handoff.json").read_text(encoding="utf-8")
    )
    assert set(handoff) == {
        "contract_version",
        "problem_requirements",
        "requirement_traceability",
        "data_dictionary",
        "data_quality_report",
        "assumptions",
        "symbols",
        "formulas",
        "sources",
        "selected_models",
        "final_runs",
        "final_metrics",
        "result_tables",
        "figure_ready_data",
        "validation_results",
        "robustness_results",
        "uncertainty",
        "failure_cases",
        "limitations",
        "claim_evidence",
        "reproduction",
        "generated_at",
        "approved_by",
    }
