"""Input-driven report generation for the completed C1/C2 continuation."""

from __future__ import annotations

from copy import deepcopy

from cumcm_skill_lab.authorization_c2.reporting import (
    REPORT_PATHS,
    build_reports,
    closure_status,
)


def test_c2_reports_are_generated_from_bound_artifacts(repo_root):
    reports = build_reports(repo_root)
    assert set(reports) == set(REPORT_PATHS)
    authorization = reports[REPORT_PATHS[6]]
    assert "DECISION-SHADOW-PROTOTYPE-AUTHORIZATION-002D-R2A-C2" in authorization
    assert "ed5ab9b1d850ecc84b09020ae9af58358dfebd2ff1b08c1913c1b00a7cff2473" in authorization


def test_c2_acceptance_status_fails_closed_on_audit_or_validation(repo_root):
    audit = {"verdict": "PASS", "unresolved_blockers": [], "output_hash": "a"}
    seal = {"final_audit_output_hash": "a", "authorization_hash": "b"}
    replay = {"stable": True, "active_decision_hash": "b"}
    state = {
        "technical_adjudication_status": "SHADOW_PROTOTYPE_AUTHORIZATION_COMPLETE",
        "shadow_authorization": {"active_decision_hash": "b"},
    }
    validation = {"overall_status": "PASS", "remote_ci": {"status": "PASS"}}
    assert closure_status(audit, seal, replay, state, validation) == (
        "SHADOW_AUTHORIZATION_CLOSURE_COMPLETE"
    )
    failed_audit = deepcopy(audit)
    failed_audit["verdict"] = "FAIL"
    assert closure_status(failed_audit, seal, replay, state, validation) == (
        "SHADOW_AUTHORIZATION_CLOSURE_INCOMPLETE"
    )
    validation["remote_ci"]["status"] = "PENDING"
    assert closure_status(audit, seal, replay, state, validation) == (
        "SHADOW_AUTHORIZATION_CLOSURE_INCOMPLETE"
    )


def test_historical_incomplete_acceptance_report_is_not_in_c2_outputs(repo_root):
    reports = build_reports(repo_root)
    assert REPORT_PATHS[8].as_posix() == "reports/phase-002d-r2a-c1-acceptance.md"
    assert "reports/phase-002d-r2a-acceptance.md" not in {path.as_posix() for path in reports}


def test_all_current_reports_have_generated_marker(repo_root):
    assert all(
        text.startswith("<!-- GENERATED FILE — DO NOT EDIT -->\n")
        for text in build_reports(repo_root).values()
    )
