import pytest

from cumcm_skill_lab.specification.state_transition import (
    build_final_state,
    validate_final_state,
)


@pytest.mark.parametrize(
    ("field", "expected"),
    (
        ("technical_adjudication_status", "SPECIFICATION_PROTOCOL_COMPLETE"),
        ("selected_architecture", None),
        ("base_selected", False),
        ("third_party_integrated", False),
        ("skill_capability_status", "SCAFFOLD_ONLY"),
        (
            "next_phase_allowed",
            "PHASE-002D-R2-CLEAN-ROOM-SPECIFICATION-AND-PROSPECTIVE-PROTOCOL",
        ),
    ),
)
def test_final_state_preserves_scope_boundaries(repo_root, field, expected):
    assert build_final_state(repo_root)[field] == expected


def test_final_state_records_audited_protocol(repo_root):
    protocol = build_final_state(repo_root)["specification_protocol"]
    assert protocol["decision_audit_status"] == "PASS"
    assert protocol["replay_stable"] is True
    assert protocol["real_model_starts"] == 0
    assert protocol["prototype_executions"] == 0
    assert protocol["third_party_executions"] == 0


def test_final_state_validates(repo_root):
    assert validate_final_state(repo_root, build_final_state(repo_root)) == []
