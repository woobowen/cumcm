import json
from pathlib import Path

from cumcm_skill_lab.report_generation import generate_status


def _state():
    return {
        "project_id": "p",
        "phase": "phase",
        "subphase": "subphase",
        "status": "IN_PROGRESS",
        "current_plan": "plan",
        "current_branch": "branch",
        "active_skill_version": "v",
        "skill_capability_status": "SCAFFOLD_ONLY",
        "base_selected": False,
        "third_party_integrated": False,
        "technical_adjudication_status": "AUTOMATED_ADJUDICATION_INCOMPLETE",
        "automated_decision_ids": [],
        "selected_architecture": None,
        "accepted_component_specifications": [],
        "next_phase_allowed": None,
        "content_verified_commit": None,
        "delivery_receipt_for_commit": None,
        "team_compliance_review_status": "NOT_RUN",
        "updated_at": "time",
        "updated_by": "test",
        "blockers": [],
        "risks": [],
    }


def test_generated_status_and_staleness(tmp_path: Path):
    (tmp_path / "state").mkdir()
    (tmp_path / "reports").mkdir()
    state_path = tmp_path / "state/project_state.json"
    state_path.write_text(json.dumps(_state()), encoding="utf-8")
    assert generate_status(tmp_path)[0] is True
    assert generate_status(tmp_path, check=True)[0] is True
    assert "- Subphase: `subphase`" in (tmp_path / "reports/current_state.md").read_text()
    changed = _state()
    changed["status"] = "STALE"
    state_path.write_text(json.dumps(changed), encoding="utf-8")
    assert generate_status(tmp_path, check=True)[0] is False


def test_generated_status_includes_c_target_batch_fields(tmp_path: Path):
    (tmp_path / "state").mkdir()
    (tmp_path / "reports").mkdir()
    state = _state()
    state.update(
        {
            "primary_target_problem_type": "C",
            "current_batch_id": "C-TARGET-BATCH-001",
            "batch_skill_frozen": True,
            "batch_reference_unlocked": False,
        }
    )
    (tmp_path / "state/project_state.json").write_text(json.dumps(state), encoding="utf-8")

    assert generate_status(tmp_path)[0] is True
    text = (tmp_path / "reports/current_state.md").read_text(encoding="utf-8")
    assert "- Primary target problem type: `C`" in text
    assert "- Current batch: `C-TARGET-BATCH-001`" in text
    assert "- Batch Skill frozen: `true`" in text
    assert "- Batch references unlocked: `false`" in text
