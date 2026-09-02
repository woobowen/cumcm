import pytest

from cumcm_skill_lab.specification.reporting import REPORT_PATHS, build_reports


def test_report_set_is_complete(repo_root):
    assert set(build_reports(repo_root)) == set(REPORT_PATHS)


@pytest.mark.parametrize("report_path", REPORT_PATHS)
def test_report_is_generated_and_scope_bounded(repo_root, report_path):
    content = build_reports(repo_root)[report_path]
    assert content.startswith("<!-- GENERATED FILE — DO NOT EDIT -->")
    assert "PHASE-SKILL-INTEGRATION-003 is allowed" not in content


def test_acceptance_report_records_no_execution(repo_root):
    content = build_reports(repo_root)["reports/phase-002d-r2-acceptance.md"]
    assert "no prototype, model experiment, API call, training or" in content
    assert "architecture and base remain null/false" in content


def test_shadow_retest_does_not_make_phase_incomplete(repo_root):
    content = build_reports(repo_root)["reports/phase-002d-r2-acceptance.md"]
    assert "does not block phase completeness" in content
    assert "RETEST_REQUIRED" in content
