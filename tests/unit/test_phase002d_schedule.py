from copy import deepcopy
from pathlib import Path

import pytest

from cumcm_skill_lab.expansion.schedule import build_schedule, validate_schedule


@pytest.fixture
def root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_schedule_is_deterministic_and_balanced(root: Path):
    first = build_schedule(root, mode="new-cohort", generated_at="frozen")
    second = build_schedule(root, mode="new-cohort", generated_at="frozen")
    assert first == second
    assert len(first["blocks"]) == 8
    assert len(first["primary_queue"]) == 24
    assert len(first["retry_queue"]) == 48
    assert validate_schedule(root, first) == []


def test_each_block_contains_each_anonymous_arm_once(root: Path):
    schedule = build_schedule(root, mode="new-cohort", generated_at="frozen")
    for block in schedule["blocks"]:
        assert set(block["anonymous_arm_order"]) == {"ARM-A", "ARM-B", "ARM-C"}


def test_schedule_is_not_arm_first(root: Path):
    schedule = build_schedule(root, mode="new-cohort", generated_at="frozen")
    first_six = [arm for block in schedule["blocks"] for arm in block["anonymous_arm_order"]][:6]
    assert len(set(first_six)) == 3


def test_schedule_mode_must_match_frozen_cohort(root: Path):
    with pytest.raises(RuntimeError, match="SCHEDULE_MODE_COHORT_MISMATCH"):
        build_schedule(root, mode="continuation", generated_at="frozen")


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("schedule_hash", "0" * 64, "SCHEDULE_HASH_MISMATCH"),
        ("primary_queue", ["duplicate"] * 24, "PRIMARY_ATTEMPT_ID_DUPLICATE"),
    ],
)
def test_schedule_faults_fail_closed(root: Path, field: str, value: object, expected: str):
    schedule = build_schedule(root, mode="new-cohort", generated_at="frozen")
    mutated = deepcopy(schedule)
    mutated[field] = value
    assert expected in validate_schedule(root, mutated)
