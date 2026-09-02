from copy import deepcopy

import pytest

from cumcm_skill_lab.expansion.attempt_ledger import (
    append_attempt,
    build_ledger,
    load_attempts,
)
from cumcm_skill_lab.expansion.eligibility import evaluate_primary_eligibility
from cumcm_skill_lab.expansion.models import read_json
from cumcm_skill_lab.expansion.oracle import evaluate_oracle
from cumcm_skill_lab.expansion.runner import (
    _command,
    _process_evidence,
    mock_attempt_fixture,
    next_planned_attempts,
    run_batch,
)
from cumcm_skill_lab.expansion.schedule import SCHEDULE_PATH
from cumcm_skill_lab.expansion.scoring import score_coverage

HASH = "a" * 64


def _attempt() -> dict:
    return {
        "attempt_id": "EXP-CASE-001-ARM-A-R1-A01",
        "cohort_id": "COHORT-1",
        "case_id": "CASE-001",
        "anonymous_arm_id": "ARM-A",
        "repeat_id": 1,
        "fresh_session": True,
        "resume_used": False,
        "parser_recovery_used": False,
        "schema_valid": True,
        "exit_code": 0,
        "completion_status": "COMPLETED",
        "task_input_hash": HASH,
        "fixture_hash": HASH,
        "package_hash": HASH,
        "prompt_hash": HASH,
        "cohort_hash": HASH,
        "model": "gpt-test",
        "reasoning_setting": "medium",
        "sandbox": "workspace-write",
        "transport_profile": "PROXY_INHERITED",
        "policy_hash": HASH,
        "schema_hash": HASH,
        "oracle_hash": HASH,
        "scorer_hash": HASH,
        "runner_hash": HASH,
        "hard_failures": [],
        "input_mutated": False,
        "result_hashes": {"observation": HASH},
    }


def _expected(attempt: dict) -> dict:
    keys = (
        "task_input_hash",
        "fixture_hash",
        "package_hash",
        "prompt_hash",
        "cohort_hash",
        "model",
        "reasoning_setting",
        "sandbox",
        "transport_profile",
        "policy_hash",
        "schema_hash",
        "oracle_hash",
        "scorer_hash",
        "runner_hash",
    )
    return {key: attempt[key] for key in keys}


def _oracle(status: str = "PASS") -> dict:
    return {"executed": True, "status": status}


def _process(passed: bool = True) -> dict:
    return {"passed": passed}


def test_primary_eligibility_accepts_clean_fresh_attempt():
    attempt = _attempt()
    result = evaluate_primary_eligibility(
        attempt=attempt, oracle=_oracle(), process=_process(), expected=_expected(attempt)
    )
    assert result["classification"] == "PRIMARY_ELIGIBLE"
    assert result["primary_eligible"] is True
    assert result["exclusion_reasons"] == []


def test_oracle_failure_is_outcome_evidence_not_selection_bias():
    attempt = _attempt()
    result = evaluate_primary_eligibility(
        attempt=attempt,
        oracle=_oracle("FAIL"),
        process=_process(),
        expected=_expected(attempt),
    )
    assert result["primary_eligible"] is True
    assert result["oracle_status"] == "FAIL"
    assert result["oracle_outcome_used_for_selection"] is False


@pytest.mark.parametrize(
    ("field", "value", "exclusion"),
    [
        ("fresh_session", False, "FRESH_SESSION"),
        ("resume_used", True, "NOT_RESUMED"),
        ("parser_recovery_used", True, "NOT_PARSER_RECOVERED"),
        ("schema_valid", False, "SCHEMA_VALID"),
        ("exit_code", 1, "LEGAL_EXIT"),
        ("completion_status", "FAILED", "COMPLETION_COMPLETE"),
        ("input_mutated", True, "INPUT_UNCHANGED"),
        ("hard_failures", ["IDENTITY_LEAK"], "NO_HARD_FAILURE"),
    ],
)
def test_primary_eligibility_faults_fail_closed(field, value, exclusion):
    attempt = _attempt()
    attempt[field] = value
    result = evaluate_primary_eligibility(
        attempt=attempt, oracle=_oracle(), process=_process(), expected=_expected(attempt)
    )
    assert result["primary_eligible"] is False
    assert exclusion in result["exclusion_reasons"]


@pytest.mark.parametrize(
    "field",
    [
        "task_input_hash",
        "fixture_hash",
        "package_hash",
        "prompt_hash",
        "cohort_hash",
        "model",
        "reasoning_setting",
        "sandbox",
        "transport_profile",
        "policy_hash",
        "schema_hash",
        "oracle_hash",
        "scorer_hash",
        "runner_hash",
    ],
)
def test_frozen_binding_mismatch_is_excluded(field):
    attempt = _attempt()
    expected = _expected(attempt)
    expected[field] = "different"
    result = evaluate_primary_eligibility(
        attempt=attempt, oracle=_oracle(), process=_process(), expected=expected
    )
    assert result["primary_eligible"] is False
    assert any(reason.endswith("_MATCH") for reason in result["exclusion_reasons"])


def test_missing_observation_is_excluded():
    attempt = _attempt()
    attempt["result_hashes"]["observation"] = None
    result = evaluate_primary_eligibility(
        attempt=attempt, oracle=_oracle(), process=_process(), expected=_expected(attempt)
    )
    assert "RESULT_PRESENT" in result["exclusion_reasons"]


def test_unexecuted_oracle_is_excluded():
    attempt = _attempt()
    result = evaluate_primary_eligibility(
        attempt=attempt,
        oracle={"executed": False, "status": "NOT_RUN"},
        process=_process(),
        expected=_expected(attempt),
    )
    assert "ORACLE_EXECUTED" in result["exclusion_reasons"]


def test_failed_process_evidence_is_excluded():
    attempt = _attempt()
    result = evaluate_primary_eligibility(
        attempt=attempt, oracle=_oracle(), process=_process(False), expected=_expected(attempt)
    )
    assert "PROCESS_VERIFIED" in result["exclusion_reasons"]


def test_schedule_primary_queue_is_followed(repo_root):
    schedule = read_json(repo_root / SCHEDULE_PATH)
    plans = next_planned_attempts(schedule, [], limit=3)
    assert [plan["attempt_id"] for plan in plans] == schedule["primary_queue"][:3]
    assert len({plan["block_id"] for plan in plans}) == 1


def test_filters_do_not_reorder_selected_cells(repo_root):
    schedule = read_json(repo_root / SCHEDULE_PATH)
    plans = next_planned_attempts(schedule, [], limit=6, filters={"case_id": {"CASE-002"}})
    expected = [item for item in schedule["primary_queue"] if "CASE-002" in item][:6]
    assert [plan["attempt_id"] for plan in plans] == expected


def test_retry_is_withheld_until_primary_predecessor_exists(repo_root):
    schedule = deepcopy(read_json(repo_root / SCHEDULE_PATH))
    schedule["primary_queue"] = []
    assert next_planned_attempts(schedule, [], limit=1) == []


def test_failed_primary_unlocks_first_frozen_retry(repo_root):
    schedule = deepcopy(read_json(repo_root / SCHEDULE_PATH))
    first_retry = schedule["retry_queue"][0]
    schedule["primary_queue"] = []
    failed = {
        "attempt_id": first_retry["retry_of"],
        "cell_id": first_retry["cell_id"],
        "primary_eligible": False,
    }
    plans = next_planned_attempts(schedule, [failed], limit=1)
    assert plans[0]["attempt_id"] == first_retry["attempt_id"]


def test_successful_cell_suppresses_retry(repo_root):
    schedule = deepcopy(read_json(repo_root / SCHEDULE_PATH))
    first_retry = schedule["retry_queue"][0]
    schedule["primary_queue"] = []
    success = {
        "attempt_id": first_retry["retry_of"],
        "cell_id": first_retry["cell_id"],
        "primary_eligible": True,
    }
    assert next_planned_attempts(schedule, [success], limit=1) == []


def test_attempt_ledger_is_append_only_and_chronological(tmp_path):
    later = {
        "attempt_id": "B",
        "start_time": "2026-09-01T00:00:02Z",
        "attempt_hash": "b" * 64,
        "primary_eligible": False,
        "completion_status": "FAILED",
    }
    earlier = {
        "attempt_id": "A",
        "start_time": "2026-09-01T00:00:01Z",
        "attempt_hash": "a" * 64,
        "primary_eligible": True,
        "completion_status": "COMPLETED",
    }
    append_attempt(tmp_path, later)
    append_attempt(tmp_path, earlier)
    assert [item["attempt_id"] for item in load_attempts(tmp_path)] == ["A", "B"]
    assert build_ledger(tmp_path)["attempt_ids"] == ["A", "B"]
    with pytest.raises(RuntimeError, match="ATTEMPT_ALREADY_EXISTS"):
        append_attempt(tmp_path, earlier)


def test_mock_fixture_is_never_primary():
    result = mock_attempt_fixture({"attempt_id": "MOCK-1"})
    assert result == {
        "attempt_id": "MOCK-1",
        "execution_kind": "MOCK_CI",
        "primary_eligible": False,
        "exclusion_reasons": ["MOCK_EXECUTION"],
        "counts_as_primary": False,
    }


def test_batch_one_rejects_more_than_three_attempts(repo_root):
    attempts_root = repo_root / "evals/results/phase-002d/attempts"
    if attempts_root.exists() and any(attempts_root.glob("*.json")):
        pytest.skip("Batch 1 has already been executed in the immutable evidence tree")
    with pytest.raises(ValueError, match="BATCH_1_MUST_BE_SINGLE_COMPLETE_BLOCK"):
        run_batch(repo_root, maximum_new_attempts=4)


@pytest.mark.parametrize("limit", [0, 7])
def test_batch_size_outside_frozen_bounds_is_rejected(repo_root, limit):
    with pytest.raises(ValueError, match="BATCH_SIZE_OUT_OF_RANGE"):
        run_batch(repo_root, maximum_new_attempts=limit)


def test_codex_command_is_ephemeral_and_policy_locked(tmp_path):
    cohort = {
        "model": "gpt-test",
        "sandbox": "workspace-write",
        "reasoning_setting": "medium",
    }
    command = _command(cohort, tmp_path, tmp_path / "out.json", "prompt")
    assert command[:2] == ["codex", "exec"]
    assert "--ephemeral" in command
    assert "--ignore-user-config" in command
    assert "mcp_servers={}" in command
    assert 'shell_environment_policy.inherit="none"' in command
    assert "--enable" not in command


def test_process_evidence_binds_identity_and_trace():
    observation = {
        "evaluation_id": "E",
        "case_id": "CASE-001",
        "anonymous_arm_id": "ARM-A",
        "run_index": 1,
        "prohibited_actions_attempted": [],
    }
    binding = {
        **{
            key: observation[key]
            for key in ("evaluation_id", "case_id", "anonymous_arm_id", "run_index")
        },
        "completion_status": "COMPLETED",
        "schema_valid": True,
        "task_input_hash": HASH,
        "package_hash": HASH,
        "fixture_manifest_hash": HASH,
        "result_hashes": {"observation": HASH},
    }
    trace = {"event_summary": {"turn.completed": 1}, "observable_commands": []}
    assert (
        _process_evidence(
            attempt_id="A", observation=observation, run_binding=binding, trace=trace
        )["passed"]
        is True
    )


def test_process_evidence_rejects_identity_mismatch():
    observation = {
        "evaluation_id": "wrong",
        "case_id": "CASE-001",
        "anonymous_arm_id": "ARM-A",
        "run_index": 1,
        "prohibited_actions_attempted": [],
    }
    binding = {
        "evaluation_id": "E",
        "case_id": "CASE-001",
        "anonymous_arm_id": "ARM-A",
        "run_index": 1,
        "completion_status": "COMPLETED",
        "schema_valid": True,
        "task_input_hash": HASH,
        "package_hash": HASH,
        "fixture_manifest_hash": HASH,
        "result_hashes": {"observation": HASH},
    }
    trace = {"event_summary": {"turn.completed": 1}, "observable_commands": []}
    assert (
        _process_evidence(
            attempt_id="A", observation=observation, run_binding=binding, trace=trace
        )["passed"]
        is False
    )


def test_oracle_adapter_preserves_correctness_role():
    observation = {
        "evaluation_id": "E",
        "case_id": "CASE-001",
        "anonymous_arm_id": "ARM-A",
        "run_index": 1,
        "completion_status": "COMPLETED",
        "baseline": ["3 trips", "2 trips", "3000", "600", "7.5", "8"],
    }
    run = {
        "evaluation_id": "E",
        "case_id": "CASE-001",
        "anonymous_arm_id": "ARM-A",
        "run_index": 1,
        "schema_valid": True,
    }
    result = evaluate_oracle(case_id="CASE-001", observation=observation, run_binding=run)
    assert result["status"] == "PASS"
    assert result["executed"] is True
    assert result["is_coverage"] is False


def test_coverage_score_cannot_claim_correctness(repo_root):
    observation = read_json(repo_root / "tests/fixtures/contracts/valid/eval_observation.json")
    rubric = read_json(repo_root / "evals/rubrics/phase-002/CASE-001.json")
    run = {
        "completion_status": "COMPLETED",
        "schema_valid": True,
        "files_written": [],
    }
    result = score_coverage(observation=observation, rubric=rubric, run_binding=run)
    assert result["proves_correctness"] is False
    assert result["semantic_review_used"] is False
