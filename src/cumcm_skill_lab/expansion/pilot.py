"""Compact real-Codex calibration pilot with a single profile fallback."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.judge_runner import DISABLED_FEATURES
from cumcm_skill_lab.eval.trace_summary import sanitize_error, summarize_jsonl

from .cohort import COHORT_PATH
from .models import (
    RESULT_ROOT,
    file_sha256,
    hashed_body,
    read_json,
    sha256_json,
    write_json,
)

PILOT_PATH = RESULT_ROOT / "pilot/pilot.json"
PILOT_SCHEMA_PATH = Path("contracts/expansion_pilot.schema.json")
PILOT_ID = "CALIBRATION-PILOT-002D-001"
PROXY_VARIABLES = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)
OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "pilot_id",
        "completion_status",
        "sum",
        "difference",
        "input_sha256",
        "network_used",
        "mcp_used",
    ],
    "properties": {
        "pilot_id": {"type": "string", "const": PILOT_ID},
        "completion_status": {"type": "string", "const": "COMPLETED"},
        "sum": {"type": "integer", "const": 42},
        "difference": {"type": "integer", "const": 8},
        "input_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "network_used": {"type": "boolean", "const": False},
        "mcp_used": {"type": "boolean", "const": False},
    },
    "additionalProperties": False,
}


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_environment(profile: str) -> tuple[dict[str, str], bool]:
    environment: dict[str, str] = {}
    for key in ("PATH", "LANG", "LC_ALL", "TERM", "HOME", "CODEX_HOME"):
        value = os.environ.get(key)
        if value is not None:
            environment[key] = value
    proxy_present = False
    if profile == "PROXY_INHERITED":
        for key in PROXY_VARIABLES:
            value = os.environ.get(key)
            if value is not None:
                environment[key] = value
                proxy_present = True
    elif profile != "NO_PROXY_PROCESS_ONLY":
        raise ValueError(f"UNKNOWN_TRANSPORT_PROFILE:{profile}")
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    return environment, proxy_present


def _snapshot(workspace: Path) -> dict[str, str]:
    return {
        path.relative_to(workspace).as_posix(): file_sha256(path)
        for path in workspace.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }


def _classify_failure(*, exit_code: int | None, stderr: str, stdout: str, timed_out: bool) -> str:
    text = f"{stderr}\n{stdout}".lower()
    if "tls" in text and any(value in text for value in ("handshake", "timeout", "timed out")):
        return "TLS_HANDSHAKE_TIMEOUT"
    if any(value in text for value in ("connection reset", "responses_connect_reset")):
        return "RESPONSES_CONNECT_RESET"
    if "websocket" in text and any(value in text for value in ("reset", "closed", "disconnect")):
        return "WEBSOCKET_RESET"
    if "https" in text and any(value in text for value in ("fallback", "disconnect", "closed")):
        return "HTTPS_FALLBACK_DISCONNECT"
    if "invalid_json_schema" in text or "invalid schema for response_format" in text:
        return "RUNNER_SCHEMA_REJECTED"
    if any(value in text for value in ("not logged in", "authentication", "unauthorized")):
        return "AUTH_BLOCKED"
    if any(value in text for value in ("quota", "usage limit", "rate limit")):
        return "QUOTA_BLOCKED"
    if "model" in text and any(
        value in text for value in ("unavailable", "not found", "unsupported")
    ):
        return "MODEL_UNAVAILABLE"
    if timed_out:
        return "PROCESS_TIMEOUT"
    if exit_code not in {0, None}:
        return "UNKNOWN_TRANSPORT_FAILURE"
    return "UNKNOWN_FAILURE"


def transport_fallback_allowed(failure_class: str | None) -> bool:
    return failure_class in {
        "TLS_HANDSHAKE_TIMEOUT",
        "RESPONSES_CONNECT_RESET",
        "WEBSOCKET_RESET",
        "HTTPS_FALLBACK_DISCONNECT",
    }


def _usage(trace: dict[str, Any]) -> dict[str, int | None]:
    observed = trace.get("token_usage") or {}
    return {
        "input_tokens": observed.get("input_tokens"),
        "cached_input_tokens": observed.get("cached_input_tokens"),
        "output_tokens": observed.get("output_tokens"),
        "reasoning_tokens": observed.get("reasoning_tokens"),
        "total_tokens": observed.get("total_tokens"),
    }


def _command(cohort: dict[str, Any], workspace: Path, output_path: Path) -> list[str]:
    arguments = [
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
        arguments.extend(["--disable", feature])
    arguments.extend(
        [
            "--json",
            "--output-schema",
            str(workspace / "output.schema.json"),
            "--output-last-message",
            str(output_path),
            "--cd",
            str(workspace),
            (
                "Read INPUT.json and output.schema.json in this isolated repository. "
                "Compute the requested integer sum and absolute difference. Do not use network, "
                "web, MCP, credentials, parent directories, or external files. Do not modify "
                "inputs. Return only the JSON required by output.schema.json."
            ),
        ]
    )
    return arguments


def _prepare_workspace(root: Path, attempt_id: str) -> tuple[Path, str]:
    workspace = root / ".cache/phase002d/pilot-workspaces" / attempt_id
    if workspace.exists():
        raise RuntimeError(f"PILOT_WORKSPACE_EXISTS:{attempt_id}")
    workspace.mkdir(parents=True)
    input_value = {"left": 17, "right": 25, "operation": "sum_and_absolute_difference"}
    write_json(workspace / "INPUT.json", input_value)
    write_json(workspace / "output.schema.json", OUTPUT_SCHEMA)
    input_hash = file_sha256(workspace / "INPUT.json")
    subprocess.run(["git", "init", "-q", "-b", "pilot"], cwd=workspace, check=True)
    subprocess.run(
        ["git", "config", "user.email", "pilot@example.invalid"], cwd=workspace, check=True
    )
    subprocess.run(["git", "config", "user.name", "CUMCM Pilot Harness"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "INPUT.json", "output.schema.json"], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "-qm", "freeze pilot inputs"], cwd=workspace, check=True)
    remotes = subprocess.run(
        ["git", "remote"], cwd=workspace, check=True, capture_output=True, text=True
    ).stdout.strip()
    if remotes:
        raise RuntimeError("PILOT_WORKSPACE_REMOTE_PRESENT")
    return workspace, input_hash


def run_attempt(root: Path, cohort: dict[str, Any], *, number: int, profile: str) -> dict[str, Any]:
    attempt_id = f"{PILOT_ID}-ATTEMPT-{number:03d}"
    workspace, input_hash = _prepare_workspace(root, attempt_id)
    harness = workspace / ".harness"
    harness.mkdir()
    output_path = harness / "last-message.json"
    command = _command(cohort, workspace, output_path)
    environment, proxy_present = _safe_environment(profile)
    before = _snapshot(workspace)
    started_at = _now()
    start = time.monotonic()
    timed_out = False
    try:
        process = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
        exit_code = process.returncode
        stdout = process.stdout
        stderr = process.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
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
    ended_at = _now()
    duration = round(time.monotonic() - start, 6)
    raw_dir = root / ".cache/phase002d/pilot"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_trace = raw_dir / f"attempt-{number:03d}.jsonl"
    raw_stderr = raw_dir / f"attempt-{number:03d}.stderr"
    raw_trace.write_text(stdout, encoding="utf-8")
    raw_stderr.write_text(stderr, encoding="utf-8")
    trace = summarize_jsonl(stdout)
    after = _snapshot(workspace)
    protected = {"INPUT.json", "output.schema.json"}
    input_mutated = any(before.get(path) != after.get(path) for path in protected)
    files_written = sorted(
        path
        for path, digest in after.items()
        if not path.startswith(".harness/") and before.get(path) != digest
    )
    output: dict[str, Any] | None = None
    schema_valid = False
    oracle_status = "NOT_RUN"
    failure_class: str | None = None
    if exit_code == 0 and output_path.is_file():
        try:
            output = json.loads(output_path.read_text(encoding="utf-8"))
            schema_valid = not list(Draft202012Validator(OUTPUT_SCHEMA).iter_errors(output))
        except json.JSONDecodeError:
            schema_valid = False
        if schema_valid:
            oracle_status = (
                "PASS"
                if output["sum"] == 42
                and output["difference"] == 8
                and output["input_sha256"] == input_hash
                and output["network_used"] is False
                and output["mcp_used"] is False
                else "FAIL"
            )
    if exit_code != 0 or timed_out:
        failure_class = _classify_failure(
            exit_code=exit_code, stderr=stderr, stdout=stdout, timed_out=timed_out
        )
    elif not schema_valid:
        failure_class = "SCHEMA_INVALID"
    elif oracle_status != "PASS":
        failure_class = "ORACLE_FAILED"
    elif input_mutated:
        failure_class = "INPUT_MUTATED"
    completion = "PASS" if failure_class is None else "FAIL"
    output_hash = file_sha256(output_path) if output_path.is_file() else None
    body = {
        "schema_version": "1.0.0",
        "attempt_id": attempt_id,
        "fresh_session": True,
        "resume_used": False,
        "retry_of": None if number == 1 else f"{PILOT_ID}-ATTEMPT-001",
        "model": cohort["model"],
        "reasoning_setting": cohort["reasoning_setting"],
        "transport_profile": profile,
        "proxy_variables_present": proxy_present,
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": duration,
        "exit_code": exit_code,
        "completion_status": completion,
        "failure_class": failure_class,
        "schema_valid": schema_valid,
        "oracle_status": oracle_status,
        "input_mutated": input_mutated,
        "token_usage": _usage(trace),
        "files_written": files_written,
        "event_summary": trace["event_summary"],
        "observable_commands": trace["observable_commands"],
        "output": output,
        "result_hashes": {"structured_output": output_hash},
        "raw_trace_hash": file_sha256(raw_trace),
        "stderr_hash": file_sha256(raw_stderr),
        "stderr_summary": sanitize_error(stderr, root) if failure_class else None,
        "counts_as_primary": False,
        "counts_as_repeat": False,
        "api_key_used": False,
        "api_billing_used": False,
    }
    attempt = hashed_body(body, "attempt_hash")
    write_json(root / RESULT_ROOT / f"pilot/attempt-{number:03d}.json", attempt)
    return attempt


def _validate_record(root: Path, record: dict[str, Any]) -> list[str]:
    schema = read_json(root / PILOT_SCHEMA_PATH)
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(record)]
    body = dict(record)
    recorded = body.pop("result_hash", None)
    if sha256_json(body) != recorded:
        errors.append("PILOT_RESULT_HASH_MISMATCH")
    if record["status"] == "PASS" and record["selected_transport_profile"] is None:
        errors.append("PILOT_PASS_WITHOUT_PROFILE")
    return sorted(errors)


def run_pilot(root: Path) -> dict[str, Any]:
    cohort = read_json(root / COHORT_PATH)
    previous = read_json(root / PILOT_PATH) if (root / PILOT_PATH).is_file() else None
    attempts = list(previous["attempts"]) if previous else []
    corrections: list[dict[str, Any]] = (
        list(previous.get("classification_corrections", [])) if previous else []
    )
    supersedes = previous["result_hash"] if previous else None
    if not attempts:
        attempts.append(run_attempt(root, cohort, number=1, profile="PROXY_INHERITED"))
    first_failure = attempts[0]["failure_class"]
    first_raw_trace = root / ".cache/phase002d/pilot/attempt-001.jsonl"
    raw_schema_rejection = (
        first_raw_trace.is_file()
        and "invalid_json_schema" in first_raw_trace.read_text(encoding="utf-8").lower()
    )
    if first_failure == "UNKNOWN_TRANSPORT_FAILURE" and (
        "invalid schema for response_format" in (attempts[0].get("stderr_summary") or "").lower()
        or raw_schema_rejection
    ):
        corrections = [
            {
                "attempt_id": attempts[0]["attempt_id"],
                "original_failure_class": first_failure,
                "corrected_failure_class": "RUNNER_SCHEMA_REJECTED",
                "correction_reason": "IGNORED_RAW_TRACE_HASH_PROVES_OUTPUT_SCHEMA_REJECTED",
                "attempt_hash_unchanged": attempts[0]["attempt_hash"],
                "evidence_hash": attempts[0]["raw_trace_hash"],
            }
        ]
        first_failure = "RUNNER_SCHEMA_REJECTED"
    if len(attempts) == 1 and first_failure == "RUNNER_SCHEMA_REJECTED":
        attempts.append(run_attempt(root, cohort, number=2, profile="PROXY_INHERITED"))
    elif len(attempts) == 1 and transport_fallback_allowed(first_failure):
        attempts.append(run_attempt(root, cohort, number=2, profile="NO_PROXY_PROCESS_ONLY"))
    successful = next((item for item in attempts if item["completion_status"] == "PASS"), None)
    status = "PASS" if successful else "INFRASTRUCTURE_BLOCKED"
    body = {
        "schema_version": "1.0.0",
        "pilot_id": PILOT_ID,
        "cohort_id": cohort["cohort_id"],
        "cohort_hash": cohort["cohort_hash"],
        "model": cohort["model"],
        "reasoning_setting": cohort["reasoning_setting"],
        "status": status,
        "selected_transport_profile": (successful["transport_profile"] if successful else None),
        "attempts": attempts,
        "model_start_count": len(attempts),
        "maximum_model_starts": 2,
        "fresh_sessions_only": True,
        "resume_used": False,
        "counts_as_primary": False,
        "counts_as_repeat": False,
        "scored_runs_started": False,
        "api_key_used": False,
        "api_billing_used": False,
        "monetary_cost": "UNKNOWN",
        "classification_corrections": corrections,
        "supersedes_result_hash": supersedes,
    }
    record = hashed_body(body, "result_hash")
    errors = _validate_record(root, record)
    if errors:
        raise RuntimeError("PILOT_RECORD_INVALID:" + ",".join(errors))
    if previous is not None and previous != record:
        write_json(
            root / RESULT_ROOT / f"pilot/superseded/pilot-{previous['result_hash']}.json",
            previous,
        )
    write_json(root / PILOT_PATH, record)
    return record


def check_pilot(root: Path) -> dict[str, Any]:
    if not (root / PILOT_PATH).is_file():
        return {"status": "FAIL", "errors": ["PILOT_RECORD_MISSING"]}
    record = read_json(root / PILOT_PATH)
    errors = _validate_record(root, record)
    for index, expected in enumerate(record["attempts"], start=1):
        path = root / RESULT_ROOT / f"pilot/attempt-{index:03d}.json"
        if not path.is_file() or read_json(path) != expected:
            errors.append(f"PILOT_ATTEMPT_MISMATCH:{index}")
    return {
        "status": "PASS" if not errors and record["status"] == "PASS" else record["status"],
        "errors": sorted(errors),
        "pilot_status": record["status"],
        "selected_transport_profile": record["selected_transport_profile"],
        "model_start_count": record["model_start_count"],
        "result_hash": record["result_hash"],
    }
