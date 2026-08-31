"""Cross-layer fail-closed cases not tied to a real network or third-party runtime."""

import copy
import json

import pytest

from cumcm_skill_lab.eval.anonymization import assert_identity_free
from cumcm_skill_lab.eval.safety import inspect_source_entry
from cumcm_skill_lab.eval.scoring import score_observation


def _observation(repo_root):
    return json.loads(
        (repo_root / "tests/fixtures/contracts/valid/eval_observation.json").read_text()
    )


def _rubric(repo_root):
    return json.loads((repo_root / "evals/rubrics/phase-002/CASE-001.json").read_text())


@pytest.mark.parametrize(
    ("path", "mode"),
    [("candidate.py", "100644"), ("candidate.sh", "100644"), ("instructions.md", "100755")],
)
def test_candidate_package_code_or_executable_fails_closed(path, mode):
    assert inspect_source_entry(path, mode, b"synthetic")


def test_candidate_identity_in_blind_input_fails_closed():
    with pytest.raises(RuntimeError, match="ANONYMIZATION_IDENTITY_LEAK"):
        assert_identity_free({"review": "candidate-x"}, ["candidate-x"])


def test_candidate_label_cannot_change_grade_or_original_output(repo_root):
    first = _observation(repo_root)
    second = copy.deepcopy(first)
    before = copy.deepcopy(first)
    first["self_reported_limitations"].append("arm flavor one")
    second["self_reported_limitations"].append("arm flavor two")
    score_one = score_observation(first, _rubric(repo_root))
    score_two = score_observation(second, _rubric(repo_root))
    assert score_one["deterministic_score"] == score_two["deterministic_score"]
    before["self_reported_limitations"].append("arm flavor one")
    assert first == before


def test_human_gate_and_integration_flags_remain_false(repo_root):
    state = json.loads((repo_root / "state/project_state.json").read_text())
    assert state["blockers"] == [
        "CODEX_TRANSPORT_BLOCKED_AFTER_THREE_ATTEMPTS",
        "BLIND_ADJUDICATION_NOT_COMPLETE",
        "META_ADJUDICATION_NOT_RUN",
        "DECISION_AUDIT_NOT_RUN",
    ]
    assert state["technical_adjudication_status"] == "AUTOMATED_ADJUDICATION_INCOMPLETE"
    assert state["automated_decision_ids"] == []
    assert state["next_phase_allowed"] is None
    assert state["base_selected"] is False
    assert state["third_party_integrated"] is False
    assert state["skill_capability_status"] == "SCAFFOLD_ONLY"
