"""Freeze non-compensable fresh-episode routing before numerical results exist."""

import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[2] / "scripts/check_c_target_2019c_validation.py"
SPEC = importlib.util.spec_from_file_location("fresh_validation_routing", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def facts():
    return {
        "skill_unchanged": True,
        "answer_sealed": True,
        "one_shot_and_timebox_respected": True,
        "uncompensable_model_failures": [],
        "empirical_primary_requirement_satisfied": True,
        "pipeline_pass_requirements": dict.fromkeys(MODULE.PIPELINE_REQUIREMENTS, True),
    }


def test_complete_evidence_permits_only_pass():
    assert MODULE.terminal_outcome(facts()) == ("C_TARGET_VALIDATION_PASSED", [])


def test_simulation_and_handoff_cannot_replace_primary_empirical_data():
    value = facts()
    value["empirical_primary_requirement_satisfied"] = False
    assert MODULE.terminal_outcome(value) == (
        "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT",
        ["VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING"],
    )


@pytest.mark.parametrize("missing", sorted(MODULE.PIPELINE_REQUIREMENTS))
def test_each_pipeline_requirement_is_mandatory(missing):
    value = facts()
    del value["pipeline_pass_requirements"][missing]
    assert MODULE.terminal_outcome(value)[0] == "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT"


@pytest.mark.parametrize(
    "field,expected",
    [
        ("skill_unchanged", "VALIDATION_CANDIDATE_DRIFT"),
        ("answer_sealed", "FIRST_RUN_CONTAMINATION_SUSPECTED"),
        ("one_shot_and_timebox_respected", "C_TARGET_VALIDATION_FAILED"),
    ],
)
def test_chronology_and_freeze_failures_precede_empirical_insufficiency(field, expected):
    value = facts()
    value[field] = False
    value["empirical_primary_requirement_satisfied"] = False
    assert MODULE.terminal_outcome(value)[0] == expected


def test_model_hard_failure_cannot_be_hidden_by_missing_data():
    value = facts()
    value["uncompensable_model_failures"] = ["UNSAFE_DISPATCH_ACCEPTED"]
    value["empirical_primary_requirement_satisfied"] = False
    assert MODULE.terminal_outcome(value) == (
        "C_TARGET_VALIDATION_FAILED",
        ["UNSAFE_DISPATCH_ACCEPTED"],
    )
