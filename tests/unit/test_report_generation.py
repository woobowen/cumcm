import json
from pathlib import Path

from cumcm_skill_lab.report_generation import generate_status


def _state():
    return {
        "project_id": "p",
        "phase": "phase",
        "status": "IN_PROGRESS",
        "current_plan": "plan",
        "current_branch": "branch",
        "active_skill_version": "v",
        "skill_capability_status": "SCAFFOLD_ONLY",
        "base_selected": False,
        "third_party_integrated": False,
        "last_verified_commit": None,
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
    changed = _state()
    changed["status"] = "STALE"
    state_path.write_text(json.dumps(changed), encoding="utf-8")
    assert generate_status(tmp_path, check=True)[0] is False
