"""Controlled real-Codex Phase 002D expansion runner."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.judge_runner import DISABLED_FEATURES
from cumcm_skill_lab.adjudication.models import canonical_json
from cumcm_skill_lab.eval.anonymization import assert_identity_free
from cumcm_skill_lab.eval.case_generation import fixture_manifest_hash
from cumcm_skill_lab.eval.models import sha256_text, validate_json
from cumcm_skill_lab.eval.runner import (
    PRIVATE_PATH,
    SECRET_TEXT,
    _artifact_reference_errors,
    _meaningful_entries,
    _parse_json_message,
    _snapshot,
    _source_reference_errors,
    _test_claim_errors,
    _trace_policy_errors,
    _write_workspace,
)
from cumcm_skill_lab.eval.scoring import detect_hard_failures
from cumcm_skill_lab.eval.trace_summary import summarize_jsonl

from .attempt_ledger import (
    CHECKPOINT_PATH,
    append_attempt,
    atomic_write_json,
    attempt_path,
    load_attempts,
    write_ledger,
)
from .budget import BUDGET_PATH, validate_budget
from .cohort import COHORT_PATH, validate_cohort
from .eligibility import evaluate_primary_eligibility
from .input_freeze import verify_input_freeze
from .models import (
    CONFIG_PATH,
    RESULT_ROOT,
    file_sha256,
    git_output,
    hashed_body,
    read_json,
    read_yaml,
    write_json,
)
from .oracle import evaluate_oracle
from .pilot import _classify_failure, _safe_environment
from .schedule import SCHEDULE_PATH, validate_schedule
from .scoring import score_coverage

ATTEMPT_SCHEMA_PATH = Path("contracts/expansion_attempt.schema.json")
RUN_SCHEMA_PATH = Path("contracts/expansion_run.schema.json")
ELIGIBILITY_SCHEMA_PATH = Path("contracts/primary_eligibility.schema.json")
INFRASTRUCTURE_FAILURES = {
    "TLS_HANDSHAKE_TIMEOUT",
    "RESPONSES_CONNECT_RESET",
    "WEBSOCKET_RESET",
    "HTTPS_FALLBACK_DISCONNECT",
    "PROCESS_TIMEOUT",
    "UNKNOWN_TRANSPORT_FAILURE",
}
IDENTITY_MARKERS = ("yushui", "handsomezr", "no_project_modeling_skill")


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _arm_mapping(root: Path) -> dict[str, str]:
    mapping = read_json(root / ".cache/upstream-eval/arm-map.json")["actual_to_anonymous"]
    inverse = {anonymous: actual for actual, anonymous in mapping.items()}
    if sorted(inverse) != ["ARM-A", "ARM-B", "ARM-C"]:
        raise RuntimeError("ANONYMOUS_ARM_MAP_INVALID")
    return inverse


def _plans(schedule: dict[str, Any]) -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for block in schedule["blocks"]:
        for cell in block["planned_attempts"]:
            attempt_id = cell["primary_attempt_id"]
            values[attempt_id] = {
                "attempt_id": attempt_id,
                "cell_id": cell["cell_id"],
                "block_id": block["block_id"],
                "block_number": block["block_number"],
                "case_id": block["case_id"],
                "repeat_id": block["repeat_id"],
                "anonymous_arm_id": cell["anonymous_arm_id"],
                "schedule_order": cell["schedule_order"],
                "attempt_number": 1,
                "retry_of": None,
            }
            for number, retry_id in enumerate(cell["retry_attempt_ids"], start=2):
                values[retry_id] = {
                    **values[attempt_id],
                    "attempt_id": retry_id,
                    "attempt_number": number,
                    "retry_of": attempt_id if number == 2 else cell["retry_attempt_ids"][0],
                }
    return values


def _matching(plan: dict[str, Any], filters: dict[str, set[Any]] | None) -> bool:
    if not filters:
        return True
    return all(not allowed or plan[field] in allowed for field, allowed in filters.items())


def next_planned_attempts(
    schedule: dict[str, Any],
    attempts: list[dict[str, Any]],
    *,
    limit: int,
    filters: dict[str, set[Any]] | None = None,
) -> list[dict[str, Any]]:
    plans = _plans(schedule)
    by_id = {attempt["attempt_id"]: attempt for attempt in attempts}
    successful_cells = {attempt["cell_id"] for attempt in attempts if attempt["primary_eligible"]}
    selected: list[dict[str, Any]] = []
    for attempt_id in schedule["primary_queue"]:
        plan = plans[attempt_id]
        if attempt_id not in by_id and _matching(plan, filters):
            selected.append(plan)
            if len(selected) == limit:
                return selected
    for slot in schedule["retry_queue"]:
        attempt_id = slot["attempt_id"]
        plan = plans[attempt_id]
        if (
            attempt_id in by_id
            or plan["cell_id"] in successful_cells
            or not _matching(plan, filters)
        ):
            continue
        predecessor = plan["retry_of"]
        if predecessor not in by_id or by_id[predecessor]["primary_eligible"]:
            continue
        selected.append(plan)
        if len(selected) == limit:
            return selected
    return selected


def _command(cohort: dict[str, Any], workspace: Path, output_path: Path, prompt: str) -> list[str]:
    command = [
        "codex",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--strict-config",
        "--model",
        cohort["model"],
        "--sandbox",
        cohort["sandbox"],
        "--config",
        f'model_reasoning_effort="{cohort["reasoning_setting"]}"',
        "--config",
        "mcp_servers={}",
        "--config",
        'shell_environment_policy.inherit="none"',
    ]
    for feature in DISABLED_FEATURES:
        command.extend(["--disable", feature])
    command.extend(
        [
            "--json",
            "--output-schema",
            str(workspace / "observation.schema.json"),
            "--output-last-message",
            str(output_path),
            "--cd",
            str(workspace),
            prompt,
        ]
    )
    return command


def _run_process(
    *, command: list[str], workspace: Path, profile: str, timeout: int
) -> tuple[int | None, str, str, bool, float]:
    environment, _ = _safe_environment(profile)
    start = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr, False, time.monotonic() - start
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout.decode(errors="replace")
            if isinstance(exc.stdout, bytes)
            else exc.stdout or ""
        )
        stderr = (
            exc.stderr.decode(errors="replace")
            if isinstance(exc.stderr, bytes)
            else exc.stderr or ""
        )
        return None, stdout, stderr, True, time.monotonic() - start


def _usage(trace: dict[str, Any]) -> dict[str, int | None]:
    usage = trace.get("token_usage") or {}
    return {
        key: usage.get(key)
        for key in (
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "reasoning_tokens",
        )
    }


def _validate_instance(root: Path, relative: Path, value: dict[str, Any]) -> list[str]:
    return [
        error.message
        for error in Draft202012Validator(read_json(root / relative)).iter_errors(value)
    ]


def pre_run_errors(root: Path) -> list[str]:
    errors = verify_input_freeze(root)
    cohort = read_json(root / COHORT_PATH)
    budget = read_json(root / BUDGET_PATH)
    schedule = read_json(root / SCHEDULE_PATH)
    errors.extend(validate_cohort(root, cohort))
    errors.extend(validate_budget(root, budget))
    errors.extend(validate_schedule(root, schedule))
    if schedule["cohort_hash"] != cohort["cohort_hash"]:
        errors.append("SCHEDULE_COHORT_HASH_MISMATCH")
    if budget["cohort_hash"] != cohort["cohort_hash"]:
        errors.append("BUDGET_COHORT_HASH_MISMATCH")
    if cohort["pilot_status"] != "PASS":
        errors.append("PILOT_NOT_PASS")
    return sorted(set(errors))


def _process_evidence(
    *,
    attempt_id: str,
    observation: dict[str, Any],
    run_binding: dict[str, Any],
    trace: dict[str, Any],
) -> dict[str, Any]:
    checks = {
        "identity_tuple_bound": all(
            observation.get(key) == run_binding.get(key)
            for key in ("evaluation_id", "case_id", "anonymous_arm_id", "run_index")
        ),
        "run_completed": run_binding["completion_status"] == "COMPLETED",
        "schema_valid": run_binding["schema_valid"] is True,
        "command_events_observed": bool(trace["event_summary"]),
        "input_hashes_bound": all(
            run_binding.get(key)
            for key in ("task_input_hash", "package_hash", "fixture_manifest_hash")
        ),
        "output_hash_recorded": bool(run_binding["result_hashes"].get("observation")),
        "prohibited_action_clear": not _meaningful_entries(
            observation.get("prohibited_actions_attempted", [])
        ),
    }
    body = {
        "schema_version": "1.0.0",
        "attempt_id": attempt_id,
        "role": "PROCESS_EVIDENCE",
        "checks": checks,
        "passed": all(checks.values()),
        "evidence_level": "E2" if all(checks.values()) else "E1",
        "observable_commands": trace["observable_commands"],
        "event_summary": trace["event_summary"],
    }
    return hashed_body(body, "process_hash")


def execute_attempt(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    errors = pre_run_errors(root)
    if errors:
        raise RuntimeError("PRE_RUN_GATE_FAILED:" + ",".join(errors))
    if attempt_path(root, plan["attempt_id"]).exists():
        raise RuntimeError(f"ATTEMPT_ALREADY_EXISTS:{plan['attempt_id']}")
    cohort = read_json(root / COHORT_PATH)
    budget = read_json(root / BUDGET_PATH)
    config = read_yaml(root / CONFIG_PATH)
    schedule = read_json(root / SCHEDULE_PATH)
    actual_arm = _arm_mapping(root)[plan["anonymous_arm_id"]]
    package_dir = root / ".cache/upstream-eval/packages" / actual_arm
    package_manifest = read_json(package_dir / "package_manifest.json")
    if package_manifest["status"] != "PACKAGE_SAFE":
        raise RuntimeError("FROZEN_PACKAGE_NOT_SAFE")
    case = read_json(root / f"evals/cases/phase-002/{plan['case_id']}.json")
    workspace = root / ".cache/phase002d/workspaces" / plan["attempt_id"]
    task_input_hash, prompt = _write_workspace(
        root,
        workspace,
        package_dir,
        case,
        plan["anonymous_arm_id"],
        "PHASE-002D-EVIDENCE-EXPANSION",
        plan["repeat_id"],
    )
    subject_commit = git_output(root, "rev-parse", "HEAD")
    workspace_commit = git_output(workspace, "rev-parse", "HEAD")
    harness = workspace / ".harness"
    harness.mkdir(exist_ok=True)
    output_path = harness / "last-message.json"
    before = _snapshot(workspace)
    command = _command(cohort, workspace, output_path, prompt)
    started_at = _now()
    exit_code, stdout, stderr, timed_out, duration = _run_process(
        command=command,
        workspace=workspace,
        profile=cohort["transport_profile"],
        timeout=int(config["timeout_seconds"]),
    )
    ended_at = _now()
    raw_dir = root / ".cache/phase002d/raw-runs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_trace = raw_dir / f"{plan['attempt_id']}.jsonl"
    raw_stderr = raw_dir / f"{plan['attempt_id']}.stderr"
    raw_trace.write_text(stdout, encoding="utf-8")
    raw_stderr.write_text(stderr, encoding="utf-8")
    trace = summarize_jsonl(stdout)
    after = _snapshot(workspace)
    protected = {path for path in before if not path.startswith(".harness/")}
    input_mutated = any(before[path] != after.get(path) for path in protected)
    files_written = sorted(
        path
        for path, digest in after.items()
        if not path.startswith(".harness/") and before.get(path) != digest
    )
    observation: dict[str, Any] | None = None
    schema_errors: list[str] = []
    publication_errors: list[str] = []
    if output_path.is_file() and output_path.read_text(encoding="utf-8").strip():
        try:
            observation = _parse_json_message(output_path.read_text(encoding="utf-8"))
            schema_errors = validate_json(
                observation, root / "contracts/eval_observation.schema.json"
            )
            candidate_ids = [
                item["candidate_id"]
                for item in read_json(
                    root / "research/upstream_candidates/dynamic_reviews/package_safety_review.json"
                )["arms"]
                if item["candidate_id"]
            ]
            assert_identity_free(observation, candidate_ids)
            serialized = canonical_json(observation).lower()
            if any(marker in serialized for marker in IDENTITY_MARKERS):
                publication_errors.append("IDENTITY_LEAK")
            if PRIVATE_PATH.search(serialized):
                publication_errors.append("PRIVATE_PATH_IN_OBSERVATION")
            if SECRET_TEXT.search(serialized):
                publication_errors.append("SECRET_IN_OBSERVATION")
        except (json.JSONDecodeError, RuntimeError, ValueError) as exc:
            schema_errors.append(type(exc).__name__)
    else:
        schema_errors.append("OUTPUT_LAST_MESSAGE_MISSING")
    publication_errors.extend(_trace_policy_errors(trace))
    if observation is not None:
        publication_errors.extend(_artifact_reference_errors(observation, workspace))
        publication_errors.extend(_source_reference_errors(observation))
        publication_errors.extend(_test_claim_errors(observation))
        if _meaningful_entries(observation.get("prohibited_actions_attempted", [])):
            publication_errors.append("PROHIBITED_ACTION_REPORTED")
    schema_valid = not schema_errors and not publication_errors
    completion = (
        "COMPLETED"
        if exit_code == 0
        and schema_valid
        and observation is not None
        and observation["completion_status"] == "COMPLETED"
        else "FAILED"
    )
    failure_class = None
    if completion != "COMPLETED":
        failure_class = (
            "SCHEMA_INVALID"
            if schema_errors
            else "POLICY_VIOLATION"
            if publication_errors
            else _classify_failure(
                exit_code=exit_code, stderr=stderr, stdout=stdout, timed_out=timed_out
            )
        )
    run_dir = root / RESULT_ROOT / "runs" / plan["attempt_id"]
    observation_path = run_dir / "observation.json"
    result_hashes: dict[str, str | None] = {"observation": None}
    if observation is not None and schema_valid:
        write_json(observation_path, observation)
        result_hashes["observation"] = file_sha256(observation_path)
    hard_failures: set[str] = set()
    if observation is not None:
        hard_failures.update(
            detect_hard_failures(
                observation,
                {
                    "completion_status": completion,
                    "schema_valid": schema_valid,
                    "files_written": files_written,
                },
            )
        )
    for error in publication_errors:
        if "NETWORK" in error:
            hard_failures.add("NETWORK_POLICY_VIOLATION")
        elif "MCP" in error:
            hard_failures.add("MCP_POLICY_VIOLATION")
        elif "IDENTITY" in error:
            hard_failures.add("IDENTITY_LEAK")
        elif "PROHIBITED" in error:
            hard_failures.add("ANSWER_CONTAMINATION")
    if input_mutated:
        hard_failures.add("INPUT_MUTATION")
    fixture_hash = fixture_manifest_hash(root)
    policy_hash = file_sha256(root / "adjudication/policies/phase-002d.yaml")
    oracle_hash = file_sha256(root / "src/cumcm_skill_lab/expansion/oracle.py")
    scorer_hash = file_sha256(root / "src/cumcm_skill_lab/expansion/scoring.py")
    runner_hash = file_sha256(root / "src/cumcm_skill_lab/expansion/runner.py")
    schema_hash = file_sha256(root / "contracts/eval_observation.schema.json")
    usage = _usage(trace)
    attempt_body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "attempt_id": plan["attempt_id"],
        "execution_kind": "REAL_CODEX",
        "cohort_id": cohort["cohort_id"],
        "cohort_hash": cohort["cohort_hash"],
        "case_id": plan["case_id"],
        "anonymous_arm_id": plan["anonymous_arm_id"],
        "repeat_id": plan["repeat_id"],
        "cell_id": plan["cell_id"],
        "schedule_block": plan["block_id"],
        "schedule_order": plan["schedule_order"],
        "schedule_hash": schedule["schedule_hash"],
        "fresh_session": True,
        "resume_used": False,
        "parser_recovery_used": False,
        "transport_profile": cohort["transport_profile"],
        "model": cohort["model"],
        "reasoning_setting": cohort["reasoning_setting"],
        "codex_version": cohort["codex_cli_version"],
        "auth_mode": cohort["auth_mode"],
        "sandbox": cohort["sandbox"],
        "network_policy": cohort["network_policy"],
        "mcp_policy": cohort["mcp_policy"],
        "prompt_hash": sha256_text(prompt),
        "task_input_hash": task_input_hash,
        "fixture_hash": fixture_hash,
        "package_hash": package_manifest["package_hash"],
        "schema_hash": schema_hash,
        "policy_hash": policy_hash,
        "oracle_hash": oracle_hash,
        "scorer_hash": scorer_hash,
        "runner_hash": runner_hash,
        "budget_hash": budget["budget_hash"],
        "subject_commit": subject_commit,
        "workspace_commit": workspace_commit,
        "start_time": started_at,
        "end_time": ended_at,
        "duration_seconds": round(duration, 6),
        "exit_code": exit_code,
        "completion_status": completion,
        "failure_class": failure_class,
        "retry_of": plan["retry_of"],
        **usage,
        "event_summary": trace["event_summary"],
        "observable_commands": trace["observable_commands"],
        "files_written": files_written,
        "input_mutated": input_mutated,
        "schema_valid": schema_valid,
        "oracle_status": "NOT_RUN",
        "process_evidence_status": "NOT_RUN",
        "robustness_status": "PENDING_CROSS_REPEAT",
        "hard_failures": sorted(hard_failures),
        "primary_eligible": False,
        "exclusion_reasons": [],
        "result_hashes": result_hashes,
        "raw_trace_hash": file_sha256(raw_trace),
        "stderr_hash": file_sha256(raw_stderr),
        "manual_intervention": False,
        "api_key_used": False,
        "api_billing_used": False,
    }
    run_binding = {
        "evaluation_id": "PHASE-002D-EVIDENCE-EXPANSION",
        "case_id": plan["case_id"],
        "anonymous_arm_id": plan["anonymous_arm_id"],
        "run_index": plan["repeat_id"],
        "completion_status": completion,
        "schema_valid": schema_valid,
        "command": ["codex", "exec"],
        "task_input_hash": task_input_hash,
        "fixture_manifest_hash": fixture_hash,
        "package_hash": package_manifest["package_hash"],
        "result_hashes": result_hashes,
    }
    if observation is not None and schema_valid:
        oracle = evaluate_oracle(
            case_id=plan["case_id"], observation=observation, run_binding=run_binding
        )
        process = _process_evidence(
            attempt_id=plan["attempt_id"],
            observation=observation,
            run_binding=run_binding,
            trace=trace,
        )
        coverage = score_coverage(
            observation=observation,
            rubric=read_json(root / f"evals/rubrics/phase-002/{plan['case_id']}.json"),
            run_binding=run_binding,
        )
    else:
        oracle = hashed_body(
            {
                "schema_version": "1.0.0",
                "case_id": plan["case_id"],
                "anonymous_arm_id": plan["anonymous_arm_id"],
                "repeat_id": plan["repeat_id"],
                "role": "DETERMINISTIC_ORACLE_CORRECTNESS",
                "checks": {},
                "status": "NOT_RUN",
                "executed": False,
                "is_coverage": False,
            },
            "oracle_result_hash",
        )
        process = hashed_body(
            {
                "schema_version": "1.0.0",
                "attempt_id": plan["attempt_id"],
                "role": "PROCESS_EVIDENCE",
                "checks": {},
                "passed": False,
                "evidence_level": "E0",
                "observable_commands": trace["observable_commands"],
                "event_summary": trace["event_summary"],
            },
            "process_hash",
        )
        coverage = hashed_body(
            {
                "schema_version": "1.0.0",
                "case_id": plan["case_id"],
                "anonymous_arm_id": plan["anonymous_arm_id"],
                "repeat_id": plan["repeat_id"],
                "status": "NOT_SCORED",
                "structured_coverage_score": None,
                "dimensions": {},
                "evidence": [],
                "missing": ["schema-valid observation missing"],
                "hard_failures": sorted(hard_failures),
                "proves_correctness": False,
                "semantic_review_used": False,
            },
            "coverage_hash",
        )
    write_json(root / RESULT_ROOT / "oracle" / f"{plan['attempt_id']}.json", oracle)
    write_json(root / RESULT_ROOT / "process_evidence" / f"{plan['attempt_id']}.json", process)
    write_json(root / RESULT_ROOT / "scores" / f"{plan['attempt_id']}.json", coverage)
    attempt_body["oracle_status"] = oracle["status"]
    attempt_body["process_evidence_status"] = "PASS" if process["passed"] else "FAIL"
    attempt_body["result_hashes"].update(
        {
            "oracle": oracle["oracle_result_hash"],
            "process_evidence": process["process_hash"],
            "coverage": coverage["coverage_hash"],
        }
    )
    expected = {
        key: attempt_body[key]
        for key in (
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
    }
    eligibility = evaluate_primary_eligibility(
        attempt=attempt_body, oracle=oracle, process=process, expected=expected
    )
    write_json(root / RESULT_ROOT / "eligibility" / f"{plan['attempt_id']}.json", eligibility)
    attempt_body["primary_eligible"] = eligibility["primary_eligible"]
    attempt_body["exclusion_reasons"] = eligibility["exclusion_reasons"]
    attempt_body["result_hashes"]["eligibility"] = eligibility["eligibility_hash"]
    attempt = hashed_body(attempt_body, "attempt_hash")
    attempt_errors = _validate_instance(root, ATTEMPT_SCHEMA_PATH, attempt)
    eligibility_errors = _validate_instance(root, ELIGIBILITY_SCHEMA_PATH, eligibility)
    if attempt_errors or eligibility_errors:
        raise RuntimeError(
            "ATTEMPT_CONTRACT_INVALID:" + ",".join(attempt_errors + eligibility_errors)
        )
    serialized = canonical_json(attempt).lower()
    if any(marker in serialized for marker in IDENTITY_MARKERS):
        raise RuntimeError("TRACKED_ATTEMPT_IDENTITY_LEAK")
    append_attempt(root, attempt)
    run_record = hashed_body(
        {
            "schema_version": "1.0.0",
            "run_id": f"RUN-{plan['attempt_id']}",
            "attempt_id": plan["attempt_id"],
            "execution_kind": "REAL_CODEX",
            "case_id": plan["case_id"],
            "anonymous_arm_id": plan["anonymous_arm_id"],
            "repeat_id": plan["repeat_id"],
            "attempt_hash": attempt["attempt_hash"],
            "subject_commit": subject_commit,
            "workspace_commit": workspace_commit,
            "observation_hash": result_hashes["observation"],
            "oracle_result_hash": oracle["oracle_result_hash"],
            "process_hash": process["process_hash"],
            "coverage_hash": coverage["coverage_hash"],
            "eligibility_hash": eligibility["eligibility_hash"],
            "primary_eligible": eligibility["primary_eligible"],
            "oracle_status": oracle["status"],
            "process_evidence_status": "PASS" if process["passed"] else "FAIL",
            "robustness_status": "PENDING_CROSS_REPEAT",
        },
        "run_hash",
    )
    run_errors = _validate_instance(root, RUN_SCHEMA_PATH, run_record)
    if run_errors:
        raise RuntimeError("RUN_CONTRACT_INVALID:" + ",".join(run_errors))
    write_json(run_dir / "run.json", run_record)
    write_ledger(root)
    write_checkpoint(root)
    return attempt


def runner_status(root: Path) -> dict[str, Any]:
    schedule = read_json(root / SCHEDULE_PATH)
    budget = read_json(root / BUDGET_PATH)
    attempts = load_attempts(root)
    eligible = [attempt for attempt in attempts if attempt["primary_eligible"]]
    successes = {(a["case_id"], a["anonymous_arm_id"], a["repeat_id"]) for a in eligible}
    common_repeats = {
        case_id: [
            repeat
            for repeat in range(1, schedule["repeats"] + 1)
            if all((case_id, arm, repeat) in successes for arm in schedule["anonymous_arms"])
        ]
        for case_id in schedule["cases"]
    }
    balanced = [case_id for case_id, repeats in common_repeats.items() if repeats]
    repeat_depth = min((len(repeats) for repeats in common_repeats.values()), default=0)
    tokens = {
        key: sum(a[key] for a in attempts if isinstance(a.get(key), int))
        for key in ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_tokens")
    }
    elapsed = round(sum(a["duration_seconds"] for a in attempts), 6)
    consecutive_infra = 0
    for attempt in reversed(attempts):
        if attempt["failure_class"] in INFRASTRUCTURE_FAILURES:
            consecutive_infra += 1
        else:
            break
    next_items = next_planned_attempts(schedule, attempts, limit=1)
    hard_stop_reasons: list[str] = []
    if len(eligible) >= budget["target_successes"]:
        hard_stop_reasons.append("MINIMA_SATISFIED")
    if len(attempts) >= budget["maximum_total_attempts"]:
        hard_stop_reasons.append("MAXIMUM_TOTAL_ATTEMPTS_REACHED")
    if tokens["input_tokens"] >= budget["maximum_total_input_tokens"]:
        hard_stop_reasons.append("INPUT_TOKEN_BUDGET_REACHED")
    if tokens["output_tokens"] >= budget["maximum_total_output_tokens"]:
        hard_stop_reasons.append("OUTPUT_TOKEN_BUDGET_REACHED")
    if elapsed >= budget["maximum_total_elapsed_seconds"]:
        hard_stop_reasons.append("ELAPSED_BUDGET_REACHED")
    if consecutive_infra >= budget["maximum_consecutive_infrastructure_failures"]:
        hard_stop_reasons.append("CONSECUTIVE_INFRASTRUCTURE_FAILURES")
    return {
        "status": "STOPPED" if hard_stop_reasons else "READY",
        "attempts": len(attempts),
        "primary_eligible": len(eligible),
        "failures": sum(a["completion_status"] != "COMPLETED" for a in attempts),
        "balanced_cases": balanced,
        "balanced_case_count": len(balanced),
        "repeat_depth": repeat_depth,
        "tokens": tokens,
        "elapsed_seconds": elapsed,
        "remaining_attempts": budget["maximum_total_attempts"] - len(attempts),
        "next_attempt_id": next_items[0]["attempt_id"] if next_items else None,
        "consecutive_infrastructure_failures": consecutive_infra,
        "hard_stop_reasons": hard_stop_reasons,
        "scored_runs_started": bool(attempts),
    }


def write_checkpoint(root: Path) -> dict[str, Any]:
    status = runner_status(root)
    checkpoint = hashed_body(
        {
            "schema_version": "1.0.0",
            "checkpoint_id": "PHASE-002D-CHECKPOINT",
            **status,
        },
        "checkpoint_hash",
    )
    atomic_write_json(root / CHECKPOINT_PATH, checkpoint)
    return checkpoint


def check_runner(root: Path) -> dict[str, Any]:
    errors = pre_run_errors(root)
    attempt_schema = read_json(root / ATTEMPT_SCHEMA_PATH)
    run_schema = read_json(root / RUN_SCHEMA_PATH)
    eligibility_schema = read_json(root / ELIGIBILITY_SCHEMA_PATH)
    for attempt in load_attempts(root):
        errors.extend(
            f"ATTEMPT:{attempt['attempt_id']}:{error.message}"
            for error in Draft202012Validator(attempt_schema).iter_errors(attempt)
        )
        eligibility_path = root / RESULT_ROOT / "eligibility" / f"{attempt['attempt_id']}.json"
        if not eligibility_path.is_file():
            errors.append(f"ELIGIBILITY_MISSING:{attempt['attempt_id']}")
        else:
            errors.extend(
                f"ELIGIBILITY:{attempt['attempt_id']}:{error.message}"
                for error in Draft202012Validator(eligibility_schema).iter_errors(
                    read_json(eligibility_path)
                )
            )
        run_path = root / RESULT_ROOT / "runs" / attempt["attempt_id"] / "run.json"
        if not run_path.is_file():
            errors.append(f"RUN_MISSING:{attempt['attempt_id']}")
        else:
            errors.extend(
                f"RUN:{attempt['attempt_id']}:{error.message}"
                for error in Draft202012Validator(run_schema).iter_errors(read_json(run_path))
            )
    status = runner_status(root)
    return {"check_status": "PASS" if not errors else "FAIL", "errors": sorted(errors), **status}


def run_batch(
    root: Path,
    *,
    maximum_new_attempts: int,
    filters: dict[str, set[Any]] | None = None,
) -> list[dict[str, Any]]:
    if not 1 <= maximum_new_attempts <= 6:
        raise ValueError("BATCH_SIZE_OUT_OF_RANGE")
    if not load_attempts(root) and maximum_new_attempts > 3:
        raise ValueError("BATCH_1_MUST_BE_SINGLE_COMPLETE_BLOCK")
    status = runner_status(root)
    if status["status"] == "STOPPED":
        return []
    schedule = read_json(root / SCHEDULE_PATH)
    attempts = load_attempts(root)
    planned = next_planned_attempts(schedule, attempts, limit=maximum_new_attempts, filters=filters)
    results = []
    for plan in planned:
        current = runner_status(root)
        if current["status"] == "STOPPED":
            break
        results.append(execute_attempt(root, plan))
    return results


def mock_attempt_fixture(plan: dict[str, Any]) -> dict[str, Any]:
    """Return explicit non-primary mock evidence for unit tests only."""
    return {
        "attempt_id": plan["attempt_id"],
        "execution_kind": "MOCK_CI",
        "primary_eligible": False,
        "exclusion_reasons": ["MOCK_EXECUTION"],
        "counts_as_primary": False,
    }
