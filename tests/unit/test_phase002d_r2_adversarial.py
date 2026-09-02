import pytest

from cumcm_skill_lab.specification.adversarial_closure import evaluate_closures

FINDING_IDS = (
    "XI-001",
    "XI-002",
    "XI-003",
    "XI-004",
    "XI-005",
    "XI-006",
    "PBI-001",
    "PBI-002",
    "PBI-003",
    "PBI-004",
    "PBI-005",
    "PBI-006",
    "TP-B1",
    "TP-B2",
    "TP-B3",
    "TP-E1",
    "TP-E2",
    "TP-E3",
    "CC-001",
    "CC-002",
    "CC-003",
    "CC-004",
    "CC-005",
    "CC-006",
    "CRP-001",
    "CRP-002",
    "CRP-003",
    "CRP-004",
    "CRP-005",
)


@pytest.mark.parametrize("finding_id", FINDING_IDS, ids=FINDING_IDS)
def test_every_blocker_and_error_has_deterministic_closure(repo_root, finding_id):
    passed, evidence = evaluate_closures(repo_root)[finding_id]
    assert passed, evidence
