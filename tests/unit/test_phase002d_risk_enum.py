"""Strict direct-adoption risk values and historical compatibility replay."""

from copy import deepcopy

import pytest

from cumcm_skill_lab.adjudication.phase002c_records import (
    DIRECT_ADOPTION_RISK_LEVELS,
    evaluate_direct_adoption_gates,
    is_registered_safe_risk,
)
from cumcm_skill_lab.adjudication.phase002d_compatibility import (
    build_risk_compatibility_replay,
)


def _candidate() -> dict:
    return {
        "answer_leakage_risk": "LOW_CONFIRMED",
        "integration_conflict_risk": "LOW_REVIEWED",
        "state_management": "NONE",
        "skill_names": ["single-skill"],
        "dangerous_or_privileged_instructions": [],
        "network_dependencies": [],
    }


def _gates(candidate: dict) -> dict[str, bool]:
    return evaluate_direct_adoption_gates(
        candidate,
        {"license_status": "MIT"},
        review_status="FULL_RUNTIME_VERIFIED",
        third_party_code_executed=True,
        candidate_dependencies_installed=True,
    )


def test_registered_risk_enum_is_closed():
    assert {
        "LOW_CONFIRMED",
        "LOW_REVIEWED",
        "MEDIUM",
        "HIGH",
        "BLOCKER",
        "UNKNOWN",
        "UNVERIFIED",
    } == DIRECT_ADOPTION_RISK_LEVELS


@pytest.mark.parametrize("value", ["LOW_CONFIRMED", "LOW_REVIEWED"])
def test_only_registered_low_values_are_safe(value):
    assert is_registered_safe_risk(value)


@pytest.mark.parametrize(
    "value",
    [
        "LOW_UNKNOWN",
        "LOW_NOT_REVIEWED",
        "LOW_BUT_UNSAFE",
        "LOW_",
        "low_confirmed",
        "LOW_CONFIRMED_EXTRA",
        "",
        None,
    ],
)
def test_low_prefix_extensions_and_empty_values_are_rejected(value):
    assert not is_registered_safe_risk(value)


@pytest.mark.parametrize("value", ["UNKNOWN", "UNVERIFIED", "MEDIUM", "HIGH", "BLOCKER"])
def test_registered_nonlow_values_block_positive_adoption(value):
    assert not is_registered_safe_risk(value)


@pytest.mark.parametrize(
    ("field", "gate"),
    [
        ("answer_leakage_risk", "answer_contamination"),
        ("integration_conflict_risk", "second_orchestrator"),
    ],
)
def test_unknown_risk_field_blocks_its_gate(field, gate):
    candidate = _candidate()
    candidate[field] = "UNKNOWN"
    assert _gates(candidate)[gate] is False


@pytest.mark.parametrize(
    ("field", "gate"),
    [
        ("answer_leakage_risk", "answer_contamination"),
        ("integration_conflict_risk", "second_orchestrator"),
    ],
)
def test_missing_risk_field_blocks_its_gate(field, gate):
    candidate = _candidate()
    candidate.pop(field)
    assert _gates(candidate)[gate] is False


def test_safe_fixture_passes_all_direct_adoption_gates():
    assert all(_gates(deepcopy(_candidate())).values())


def test_phase002c_rejection_and_historical_results_are_unchanged(repo_root):
    replay = build_risk_compatibility_replay(repo_root)
    assert replay["historical_phase002c_integrity"]["passed"] is True
    assert replay["historical_rejection_invariant"] is True
    assert all(
        item["current_strict_decision"] == "AUTOMATED_REJECTED"
        for item in replay["candidate_results"]
    )
