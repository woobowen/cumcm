"""RC9 eligibility requires its own command, review and immutable subject evidence."""

import importlib.util
import json

import pytest


def module(root):
    spec = importlib.util.spec_from_file_location(
        "rc9_qualification", root / "scripts/check_phase004c6_rc9_release.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def binding(q, root, name, value):
    path = q.BASE / name
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value).encode()
    (root / path).write_bytes(data)
    return {"path": path.as_posix(), "sha256": q.digest(data)}


def command_case(q, root, monkeypatch):
    log = binding(q, root, "actual_log.json", {"stdout": "2200 passed"})
    command = {
        "argv": ["bash", "scripts/ci.sh"],
        "exit_code": 0,
        "started_at": "2026-09-09T03:00:00Z",
        "ended_at": "2026-09-09T03:01:00Z",
        "elapsed_seconds": 60,
        "executed_head": "b" * 40,
        "log": log,
    }
    receipt = {
        "subject_commit": "a" * 40,
        "kind": "full_ci",
        "status": "PASS",
        "evidence": [log],
        "commands": [command],
        "pytest_passed": 2200,
        "pytest_failed": 0,
    }
    snapshot = {"subject_commit": "a" * 40, "implementation_sha256": {"code.py": "c" * 64}}
    protocol = {"required_receipts": ["full_ci"], "minimum_full_pytest_passed": 2153}
    monkeypatch.setattr(q, "subject_mapping", lambda *a: snapshot["implementation_sha256"])
    return receipt, snapshot, protocol


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("none", None),
        ("missing", "RC9_RECEIPT_SET_INVALID"),
        ("old_subject", "RC9_RECEIPT_NOT_PASS"),
        ("failed", "RC9_COMMAND_FAILURE"),
        ("strict_instead", "RC9_FULL_CI_COMMAND_MISSING"),
        ("pytest_failed", "RC9_FULL_PYTEST_NOT_PASS"),
        ("wrong_head", "RC9_TESTED_IMPLEMENTATION_MISMATCH"),
        ("time_reversed", "RC9_COMMAND_TIME_INVALID"),
        ("changed_log", "RC9_RECEIPT_INVALID"),
    ],
)
def test_current_full_ci_is_not_replaceable_by_old_or_partial_receipts(
    repo_root, tmp_path, monkeypatch, mutation, code
):
    q = module(repo_root)
    receipt, snapshot, protocol = command_case(q, tmp_path, monkeypatch)
    command = receipt["commands"][0]
    if mutation == "old_subject":
        receipt["subject_commit"] = "d" * 40
    elif mutation == "failed":
        command["exit_code"] = 1
    elif mutation == "strict_instead":
        command["argv"] = [".venv/bin/python", "scripts/validate_repo.py", "--strict"]
    elif mutation == "pytest_failed":
        receipt["pytest_failed"] = 2
    elif mutation == "wrong_head":
        monkeypatch.setattr(q, "subject_mapping", lambda *a: {"code.py": "d" * 64})
    elif mutation == "time_reversed":
        command["ended_at"] = "2026-09-09T02:59:00Z"
    elif mutation == "changed_log":
        (tmp_path / command["log"]["path"]).write_text("changed evidence")
    snapshot["receipts"] = {"full_ci": binding(q, tmp_path, "full_ci.json", receipt)}
    if mutation == "missing":
        snapshot["receipts"] = {}
    errors = q.validate_receipts(snapshot, protocol, tmp_path)
    assert (errors == []) if code is None else any(e.startswith(code) for e in errors)


@pytest.mark.parametrize(
    "change", ["not_run", "open_finding", "wrong_subject", "no_calls", "main_only"]
)
def test_native_review_does_not_accept_substitute_or_unresolved_science(
    repo_root, tmp_path, change
):
    q = module(repo_root)
    log = binding(q, tmp_path, "native_commands.json", {"commands": ["pure math check"]})
    receipt = {
        "subject_commit": "a" * 40,
        "reviewed_subject": "a" * 40,
        "kind": "native_protocol_review",
        "status": "PASS",
        "evidence": [log],
        "mechanism": "NATIVE_READ_ONLY_AGENT",
        "actual_agent_task": "review-1",
        "material_open_findings": [],
        "actual_command_count": 1,
    }
    if change == "not_run":
        receipt["status"] = "NOT_RUN"
    elif change == "open_finding":
        receipt["material_open_findings"] = ["incorrect denominator"]
    elif change == "wrong_subject":
        receipt["reviewed_subject"] = "b" * 40
    elif change == "no_calls":
        receipt["actual_command_count"] = 0
    else:
        receipt["mechanism"] = "MAIN_AGENT_SELF_REVIEW"
    snapshot = {
        "subject_commit": "a" * 40,
        "receipts": {"native_protocol_review": binding(q, tmp_path, "native_review.json", receipt)},
    }
    errors = q.validate_receipts(
        snapshot, {"required_receipts": ["native_protocol_review"]}, tmp_path
    )
    assert errors


def development_fixture(q, root, case_id, status="SCOPED_DEVELOPMENT_COMPLETE"):
    budget = {"model_cli_starts": 4, "independent_checker_starts": 4, "final_starts": 1}
    starts = {
        "model_cli_starts": 2,
        "independent_checker_starts": 4,
        "final_starts": 1 if status == "SCOPED_DEVELOPMENT_COMPLETE" else 0,
    }
    folder = root / "evals/results/phase-004c6" / case_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "development_design.json").write_text(
        json.dumps({"required_question_ids": ["REQ-A"], "budget": budget})
    )
    log = binding(q, root, case_id + "-execution.json", {"actual": "synthetic command receipt"})
    ledger = binding(
        q,
        root,
        case_id + "-budget.json",
        {"limits": budget, "events": [{"kind": k} for k, n in starts.items() for _ in range(n)]},
    )
    questions = [{"requirement_id": "REQ-A", "scope": "conditional"}]
    terminal_body = {
        "case_id": case_id,
        "subject_commit": "a" * 40,
        "status": status,
        "question_results": questions,
        "actual_starts": starts,
    }
    terminal_path = folder / "terminal/decision.json"
    terminal_path.parent.mkdir()
    terminal_path.write_text(json.dumps(terminal_body))
    terminal = {
        "path": terminal_path.relative_to(root).as_posix(),
        "sha256": q.digest(terminal_path.read_bytes()),
    }
    execution = binding(
        q,
        root,
        case_id + "-evidence.json",
        {
            "case_id": case_id,
            "subject_commit": "a" * 40,
            "budget_ledger": ledger,
            "artifacts": [log],
            "model_run_ids": ["RUN-A", "RUN-B"],
        },
    )
    return {
        "case_id": case_id,
        "subject_commit": "a" * 40,
        "independent_validation": False,
        "question_results": questions,
        "limitations": ["unknown truth"],
        "actual_starts": starts,
        "terminal_status": status,
        "terminal": terminal,
        "execution_evidence": execution,
    }


def development_bundle(q, root):
    cases = [development_fixture(q, root, "D1"), development_fixture(q, root, "D2", "INSUFFICIENT")]
    evidence = [c["terminal"] for c in cases]
    receipt = {
        "kind": "development_results",
        "subject_commit": "a" * 40,
        "status": "PASS",
        "evidence": evidence,
        "cases": cases,
    }
    protocol = {
        "required_receipts": ["development_results"],
        "required_development_cases": ["D1", "D2"],
    }
    return receipt, protocol


def test_development_does_not_upgrade_validation_or_exceed_starts(repo_root, tmp_path):
    q = module(repo_root)
    receipt, protocol = development_bundle(q, tmp_path)
    for mutate in (False, True):
        if mutate:
            receipt["cases"][1]["independent_validation"] = True
            receipt["cases"][1]["actual_starts"]["independent_checker_starts"] = 5
        snapshot = {
            "subject_commit": "a" * 40,
            "receipts": {"development_results": binding(q, tmp_path, "development.json", receipt)},
        }
        errors = q.validate_receipts(snapshot, protocol, tmp_path)
        if not mutate:
            assert (
                errors == []
            )  # An honest pre-Final negative remains eligible as negative evidence.
        else:
            assert "RC9_DEVELOPMENT_SCOPE_INVALID" in errors
            assert "RC9_DEVELOPMENT_START_BUDGET_INVALID" in errors


def test_native_result_review_binds_both_actual_case_artifact_sets(repo_root, tmp_path):
    q = module(repo_root)
    development, protocol = development_bundle(q, tmp_path)
    protocol["required_receipts"].append("native_result_review")
    review = {
        "subject_commit": "a" * 40,
        "reviewed_subject": "a" * 40,
        "kind": "native_result_review",
        "status": "PASS",
        "evidence": development["evidence"],
        "mechanism": "NATIVE_READ_ONLY_AGENT",
        "actual_agent_task": "actual-results-review",
        "actual_command_count": 1,
        "material_open_findings": [],
        "review_scope": "ACTUAL_POSTVALIDATION_DEVELOPMENT_RESULTS",
        "reviewed_development_artifacts": {
            c["case_id"]: {k: c[k] for k in ("terminal", "execution_evidence")}
            for c in development["cases"]
        },
    }
    for source_only in (False, True):
        if source_only:
            review["review_scope"] = "SOURCE_CODE_ONLY"
            review["reviewed_development_artifacts"] = {}
        snapshot = {
            "subject_commit": "a" * 40,
            "receipts": {
                "development_results": binding(q, tmp_path, "development.json", development),
                "native_result_review": binding(q, tmp_path, "review.json", review),
            },
        }
        errors = q.validate_receipts(snapshot, protocol, tmp_path)
        assert ("RC9_NATIVE_RESULT_ARTIFACT_BINDING_INVALID" in errors) is source_only
        if not source_only:
            assert errors == []
