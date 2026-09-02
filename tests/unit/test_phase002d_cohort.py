from copy import deepcopy
from pathlib import Path

import pytest

from cumcm_skill_lab.expansion.cohort import (
    build_cohort,
    continuation_shortfall,
    validate_cohort,
)


@pytest.fixture
def root() -> Path:
    return Path(__file__).resolve().parents[2]


def availability(*models: tuple[str, list[str]]) -> dict:
    return {
        "codex_cli_version": "0.147.0",
        "models": [
            {
                "id": model,
                "default": index == 0,
                "reasoning": [
                    {"reasoningEffort": effort, "description": "test"} for effort in efforts
                ],
            }
            for index, (model, efforts) in enumerate(models)
        ],
    }


def test_continuation_target_is_recomputed_from_eligible_history(root: Path):
    shortfall = continuation_shortfall(root)
    assert shortfall["target_successes"] == 14
    assert len(shortfall["cells"]) == 12


def test_missing_historical_model_forces_new_cohort(root: Path):
    cohort = build_cohort(root, availability(("gpt-5.6-sol", ["medium"])))
    assert cohort["mode"] == "NEW_MODEL_COHORT"
    assert cohort["target_successes"] == 24
    assert cohort["model"] == "gpt-5.6-sol"
    assert cohort["historical_phase002_use"] == "CROSS_MODEL_EXPLORATORY_GAP_EVIDENCE_ONLY"
    assert validate_cohort(root, cohort) == []


def test_required_reasoning_must_be_observable(root: Path):
    with pytest.raises(RuntimeError, match="NO_ALLOWED_MODEL_WITH_REQUIRED_REASONING"):
        build_cohort(root, availability(("gpt-5.6-sol", ["high"])))


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("target_successes", 14, "NEW_MODEL_COHORT_TARGET_NOT_24"),
        ("cohort_hash", "0" * 64, "COHORT_HASH_MISMATCH"),
    ],
)
def test_cohort_faults_fail_closed(root: Path, field: str, value: object, error: str):
    cohort = build_cohort(root, availability(("gpt-5.6-sol", ["medium"])))
    mutated = deepcopy(cohort)
    mutated[field] = value
    assert error in validate_cohort(root, mutated)
