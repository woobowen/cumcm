"""RC9 public Final protocol: real process order, early rejection, immutable receipt review."""

import importlib.util
import json
import subprocess
import sys


def helper(repo_root):
    path = repo_root / "tests/integration/test_rc8_nonpredictive_and_final_lifecycle.py"
    spec = importlib.util.spec_from_file_location("rc9_protocol_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cli(repo_root, case, *args):
    process = subprocess.run(
        [
            sys.executable,
            str(repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"),
            *args,
            "--case-root",
            str(case),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    return process, json.loads(process.stdout)


def test_public_early_final_retains_request_and_starts_no_checker(repo_root, tmp_path):
    _, core, case = helper(repo_root)._nonpredictive(repo_root, tmp_path)
    process, result = cli(
        repo_root,
        case,
        "evaluate-final",
        "--run-id",
        "RUN-CAND-20260906",
        "--decision-hash",
        "a" * 64,
    )
    assert process.returncode != 0, result
    assert "RC_FINAL_PREREQUISITES_NOT_ACCEPTED" in result["reason_codes"]
    events = [
        json.loads(line) for line in (case / core.FINAL_PROTOCOL_EVENTS).read_text().splitlines()
    ]
    assert [e["event"] for e in events] == ["FINAL_REQUESTED", "FINAL_REQUEST_REJECTED"]
    assert not (case / core.SCIENTIFIC_FINAL_LEDGER).exists()
    assert not list(case.glob("runs/*/final_check.*"))


def test_public_completion_accepts_development_then_independent_final_once(repo_root, tmp_path):
    h, core, case = helper(repo_root)._nonpredictive(repo_root, tmp_path)
    core.execute_scientific_check(
        case, run_id="RUN-CAND-20260906", code_path="models/independent_check.py"
    )
    process, result = h._run_controller(repo_root, case)
    assert process.returncode == 0, (result, process.stderr)
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    events = [
        json.loads(line) for line in (case / core.FINAL_PROTOCOL_EVENTS).read_text().splitlines()
    ]
    names = [e["event"] for e in events]
    assert names == [
        "DEVELOPMENT_GATES_ACCEPTED",
        "SELECTION_FROZEN",
        "FINAL_REQUESTED",
        "FINAL_AUTHORIZED",
        "FINAL_STARTED",
        "FINAL_RECEIPT_ACCEPTED",
    ]
    freeze = core.load_json(case / core.PREFINAL_SELECTION)
    ledger = core.load_json(case / core.SCIENTIFIC_FINAL_LEDGER)
    assert ledger["count"] == 1 and ledger["test_access_count"] == 0
    assert freeze["accepted_at"] <= ledger["started_at"] <= ledger["ended_at"]
    assert core.read_artifact(case, "model_comparison")["content"]["test_access"]["count"] == 0
    before = {
        p.relative_to(case).as_posix(): (p.stat().st_mtime_ns, core.file_hash(p))
        for p in case.glob("runs/*/final_check.*")
    }
    for _ in range(2):
        reviewed, receipt = cli(
            repo_root,
            case,
            "evaluate-final",
            "--review-existing",
            "--run-id",
            "RUN-CAND-20260906",
            "--decision-hash",
            freeze["decision_hash"],
        )
        assert reviewed.returncode == 0, receipt
    assert before == {
        p.relative_to(case).as_posix(): (p.stat().st_mtime_ns, core.file_hash(p))
        for p in case.glob("runs/*/final_check.*")
    }
    assert core.load_json(case / core.SCIENTIFIC_FINAL_LEDGER) == ledger


def test_missing_freeze_rejects_before_capture_or_data_hashing(repo_root, tmp_path, monkeypatch):
    _, core, case = helper(repo_root)._nonpredictive(repo_root, tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("raw/capture access occurred before prerequisites")

    monkeypatch.setattr(core, "verify_current_capture_files", forbidden)
    monkeypatch.setattr(core, "file_hash", forbidden)
    import pytest

    with pytest.raises(ValueError, match="RC_FINAL_PREREQUISITES_NOT_ACCEPTED"):
        core.evaluate_scientific_final(case, decision_hash="a" * 64)
