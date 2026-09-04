from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator, ValidationError


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_development_eval_state_is_schema_valid_and_preserves_rc1_evidence(repo_root) -> None:
    state = _load(repo_root / "state/project_state.json")
    schema = _load(repo_root / "contracts/project_state.schema.json")

    Draft202012Validator(schema).validate(state)
    assert state["technical_adjudication_status"] == "DEVELOPMENT_EVAL_RC3_READY"
    assert state["subphase"] == "CUMCM-2020-A-DEVELOPMENT-RC3"
    assert state["current_plan"] == "plans/active/PLAN-0004B-2020a-development-eval.md"
    assert state["next_phase_allowed"] == "PHASE-SKILL-VALIDATION-EVAL-004-C"
    assert state["active_skill_version"] == "0.2.0-competition-rc3"
    assert state["development_eval"]["case_id"] == "CUMCM-2020-A-DEVELOPMENT-002"
    assert state["development_eval"]["answer_access_status"] == "UNLOCKED_AFTER_FIRST_RUN"
    assert state["development_eval"]["first_run_status"] == "FROZEN"
    assert state["development_eval"]["revision_cycles_used"] == 1
    assert state["development_eval"]["stress_statuses"] == {
        "A": "PASS",
        "B": "PASS",
        "C": "PASS",
    }
    assert state["blockers"] == []
    assert state["competition_rc1"]["full_r3_status"] == "DEFERRED_NOT_PASSED"
    assert state["competition_rc1"]["real_comparison_model_starts"] == 0


@pytest.mark.parametrize(
    "path,value",
    [
        (("active_skill_version",), "0.1.0-foundation"),
        (("next_phase_allowed",), "PHASE-SKILL-DEVELOPMENT-EVAL-004"),
        (("base_selected",), True),
        (("third_party_integrated",), True),
        (("blockers",), ["fabricated"]),
        (("competition_rc1", "full_r3_status"), "PASSED"),
        (("competition_rc1", "end_to_end", "passed"), 1),
        (("competition_rc1", "negative_tests", "failed"), 1),
        (("competition_rc1", "integration_audit", "status"), "BLOCK"),
    ],
)
def test_development_first_run_state_mutations_fail_schema_closed(
    repo_root, path: tuple[str, ...], value: object
) -> None:
    state = copy.deepcopy(_load(repo_root / "state/project_state.json"))
    schema = _load(repo_root / "contracts/project_state.schema.json")
    target = state
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(state)


def test_competition_rc_consistency_checker_accepts_canonical_state(repo_root) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/check_competition_rc_consistency.py"),
            "--check",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["ok"] is True
    assert result["failed_checks"] == []
