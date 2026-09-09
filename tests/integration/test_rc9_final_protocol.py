"""RC9 public Final protocol: real process order, early rejection, immutable receipt review."""

import importlib.util
import json
import subprocess
import sys

import pytest


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
    with pytest.raises(ValueError, match="RC_FINAL_PREREQUISITES_NOT_ACCEPTED"):
        core.evaluate_scientific_final(case, decision_hash="a" * 64)


def prepared_science_case(repo_root, tmp_path, behavior=None):
    path = repo_root / "tests/integration/test_rc9_science_semantics.py"
    spec = importlib.util.spec_from_file_location("rc9_protocol_science", path)
    science = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(science)

    def configure(data, plan, requirements, semantic):
        if behavior:
            data["final_behavior"] = behavior

    h, core, case = science.build(repo_root, tmp_path, "optimization", mutation=configure)
    spec = importlib.util.spec_from_file_location(
        "rc9_prepare_controller", repo_root / "scripts/finalize_fresh_c_validation.py"
    )
    controller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controller)
    plan = core.read_artifact(case, "experiment_plan")["content"]
    attempts, outputs = controller._attempt_registry(core, case, plan)
    selected = controller.select_candidate(attempts, plan)
    decision = core.canonical_hash(selected)
    manifests = controller._preview_attempts(core, case, attempts, decision)
    controller._persist_manifests(core, case, manifests)
    run = "RUN-CAND-20260906"
    core.execute_scientific_check(case, run_id=run, code_path="models/independent_check.py")
    h._accepted(
        core,
        case,
        "model_comparison",
        controller._comparison_payload(plan, attempts, selected, decision),
    )
    h._accepted(
        core,
        case,
        "robustness_analysis",
        controller._robustness_payload(manifests[run], outputs[run], "CAND"),
    )
    process, receipt = cli(repo_root, case, "prepare-final", "--decision-hash", decision)
    assert process.returncode == 0, receipt
    return h, core, case, decision


@pytest.mark.parametrize("mutation", ["missing_robustness", "leakage", "empty_selection"])
def test_rehashed_invalid_predecessors_still_require_actual_gates(repo_root, tmp_path, mutation):
    h, core, case, decision = prepared_science_case(repo_root, tmp_path)
    if mutation == "missing_robustness":
        key, content = "robustness_analysis", {}
    elif mutation == "leakage":
        key = "model_comparison"
        content = core.read_artifact(case, key)["content"]
        content["leakage_checks"]["future_information"] = True
    else:
        key = "requirement_selection"
        content = core.read_artifact(case, key)["content"]
        content["requirements"] = []
    h._accepted(core, case, key, content)
    freeze = core.load_json(case / core.PREFINAL_SELECTION)
    freeze["bound_files"][core.ARTIFACT_PATHS[key]] = core.file_hash(
        case / core.ARTIFACT_PATHS[key]
    )
    freeze["freeze_sha256"] = core.canonical_hash(
        {k: v for k, v in freeze.items() if k != "freeze_sha256"}
    )
    core.write_json(case / core.PREFINAL_SELECTION, freeze)
    process, result = cli(
        repo_root,
        case,
        "evaluate-final",
        "--run-id",
        "RUN-CAND-20260906",
        "--decision-hash",
        decision,
    )
    assert process.returncode != 0, result
    assert not (case / core.SCIENTIFIC_FINAL_LEDGER).exists()
    assert not list(case.glob("runs/*/final_check.*"))


@pytest.mark.parametrize("behavior", ["FAIL_PARTIAL", "TIMEOUT"])
def test_started_failure_and_timeout_keep_partial_output_and_consume_final(
    repo_root, tmp_path, behavior
):
    _, core, case, decision = prepared_science_case(repo_root, tmp_path, behavior)
    args = (
        "evaluate-final",
        "--run-id",
        "RUN-CAND-20260906",
        "--decision-hash",
        decision,
        "--timeout-seconds",
        "1",
    )
    process, result = cli(repo_root, case, *args)
    assert process.returncode != 0, result
    ledger = core.load_json(case / core.SCIENTIFIC_FINAL_LEDGER)
    assert ledger["status"] == "FAILED" and ledger["count"] == 1
    receipt = ledger["checks"]["RUN-CAND-20260906"]
    assert len(receipt["files"]) == 3
    assert "partial" in (case / "runs/RUN-CAND-20260906/final_check.json").read_text()
    again, second = cli(repo_root, case, *args)
    assert again.returncode != 0, second
    assert "RC_SCIENTIFIC_FINAL_ALREADY_STARTED" in second["reason_codes"]
    assert ledger == core.load_json(case / core.SCIENTIFIC_FINAL_LEDGER)


def test_concurrent_final_requests_start_exactly_one_checker(repo_root, tmp_path):
    _, core, case, decision = prepared_science_case(repo_root, tmp_path)
    args = [
        sys.executable,
        str(core.SKILL_ROOT / "scripts/cumcm_case.py"),
        "evaluate-final",
        "--case-root",
        str(case),
        "--run-id",
        "RUN-CAND-20260906",
        "--decision-hash",
        decision,
    ]
    processes = [
        subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(2)
    ]
    receipts = [p.communicate(timeout=60) for p in processes]
    assert sorted(p.returncode for p in processes) == [0, 3], receipts
    ledger = core.load_json(case / core.SCIENTIFIC_FINAL_LEDGER)
    assert ledger["count"] == 1 and ledger["status"] == "SUCCESS"
    events = [
        json.loads(line) for line in (case / core.FINAL_PROTOCOL_EVENTS).read_text().splitlines()
    ]
    assert sum(e["event"] == "FINAL_STARTED" for e in events) == 1
