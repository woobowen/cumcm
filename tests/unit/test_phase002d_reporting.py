from copy import deepcopy

from cumcm_skill_lab.expansion.reporting import build_command_ledger, build_reports


def test_command_ledger_distinguishes_pilot_and_scored_starts(repo_root):
    ledger = build_command_ledger(repo_root)
    assert ledger["entry_count"] == 30
    assert ledger["real_pilot_starts"] == 2
    assert ledger["real_scored_starts"] == 28


def test_command_ledger_reports_zero_native_subagents(repo_root):
    assert build_command_ledger(repo_root)["native_subagent_runs"] == 0


def test_every_real_command_has_duration_result_hash_and_token_record(repo_root):
    entries = build_command_ledger(repo_root)["entries"]
    assert all(entry["duration_seconds"] >= 0 for entry in entries)
    assert all(len(entry["evidence_hash"]) == 64 for entry in entries)
    assert all("token_usage" in entry for entry in entries)


def test_terminal_reports_are_generated_from_machine_records(repo_root):
    ledger = build_command_ledger(repo_root)
    reports = build_reports(repo_root, ledger)
    assert (
        "EVIDENCE_EXPANSION_INCOMPLETE"
        in reports[__import__("pathlib").Path("reports/phase-002d-acceptance.md")]
    )


def test_subagent_report_does_not_claim_pass(repo_root):
    reports = build_reports(repo_root, build_command_ledger(repo_root))
    report = reports[__import__("pathlib").Path("reports/phase002d_subagent_audit.md")]
    assert "zero Subagents ran" in report
    assert "PRECONDITION_LOCKED" in report


def test_decision_report_has_no_phase002d_decision_id(repo_root):
    reports = build_reports(repo_root, build_command_ledger(repo_root))
    report = reports[__import__("pathlib").Path("reports/phase002d_automated_decisions.md")]
    assert "Phase 002D decision IDs: none" in report


def test_report_generation_is_deterministic(repo_root):
    first = build_reports(repo_root, build_command_ledger(repo_root))
    second = deepcopy(build_reports(repo_root, build_command_ledger(repo_root)))
    assert first == second
