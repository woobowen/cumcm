from cumcm_skill_lab.failure_aware.reporting import REPORT_PATHS, build_reports


def test_r1_reporting_generates_every_required_report(repo_root):
    reports = build_reports(repo_root)
    assert set(reports) == set(REPORT_PATHS)
    assert all(
        text.startswith("<!-- GENERATED FILE — DO NOT EDIT -->") for text in reports.values()
    )


def test_r1_acceptance_preserves_negative_quality_result(repo_root):
    report = build_reports(repo_root)["reports/phase-002d-r1-acceptance.md"]
    assert "FAILURE_AWARE_ADJUDICATION_COMPLETE" in report
    assert "Quality remains `EVIDENCE_INSUFFICIENT`" in report
    assert "PHASE-EVIDENCE-EXPANSION-002D" in report
    assert "Phase 003 remains locked" in report


def test_r1_reports_do_not_claim_implementation_or_training(repo_root):
    report = build_reports(repo_root)["reports/phase-002d-r1-acceptance.md"]
    assert "They are not\nimplemented" in report
    assert "Foundation-model training/fine-tuning: none" in report
    assert "zero real model\nstarts" in report
