"""Persistent `codex exec` transport with one exact-session continuation."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from datetime import UTC, datetime
from typing import Any

from jsonschema import ValidationError

from ..judge_runner import DISABLED_FEATURES, assert_blind
from ..models import read_json, sha256_bytes, sha256_json
from .base import RoleRunRequest, TransportAdapter, TransportResult, TransportStatus
from .event_sanitization import parse_jsonl_bytes, sanitized_observable, summarize_events
from .failure_classification import FailureInfo, classify_failure


def safe_codex_environment() -> dict[str, str]:
    """Copy only named non-secret variables; never enumerate or read API-key variables."""
    environment: dict[str, str] = {}
    for key in ("PATH", "LANG", "LC_ALL", "TERM", "HOME", "CODEX_HOME"):
        value = os.environ.get(key)
        if value is not None:
            environment[key] = value
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    return environment


def isolation_args() -> list[str]:
    arguments = [
        "--config",
        "mcp_servers={}",
        "--config",
        'shell_environment_policy.inherit="none"',
        "--config",
        'approval_policy="never"',
    ]
    for feature in DISABLED_FEATURES:
        arguments.extend(["--disable", feature])
    return arguments


class ExecAdapter(TransportAdapter):
    name = "EXEC_RESUMABLE"

    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self._last_result: TransportResult | None = None

    def start_role(self, request: RoleRunRequest) -> TransportResult:
        command = [
            "codex",
            "exec",
            "--ignore-user-config",
            "--strict-config",
            "--model",
            request.model,
            "--sandbox",
            "workspace-write",
            "--config",
            f'model_reasoning_effort="{request.reasoning_setting}"',
            *isolation_args(),
            "--json",
            "--output-schema",
            str(request.output_schema_path),
            "--output-last-message",
            str(request.output_path),
            "--cd",
            str(request.workspace),
            request.prompt,
        ]
        return self._run(request, command, resume=False)

    def resume_role(self, request: RoleRunRequest) -> TransportResult:
        exact = request.checkpoint_store.load_exact_session(request.role_id)
        session_id = exact.get("session_id") if exact else None
        if not isinstance(session_id, str) or not session_id:
            return self._missing_session_result(request)
        command = [
            "codex",
            "exec",
            "resume",
            "--ignore-user-config",
            "--strict-config",
            "--model",
            request.model,
            "--config",
            f'model_reasoning_effort="{request.reasoning_setting}"',
            *isolation_args(),
            "--json",
            "--output-schema",
            str(request.output_schema_path),
            "--output-last-message",
            str(request.output_path),
            session_id,
            (
                "Continue only the same formal role. Re-read the unchanged local bundle and "
                "output_schema.json, add no new assumptions, and return the required JSON only."
            ),
        ]
        return self._run(request, command, resume=True, expected_session_id=session_id)

    def poll_role(self) -> TransportResult | None:
        return self._last_result

    def cancel_role(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()

    def _run(
        self,
        request: RoleRunRequest,
        command: list[str],
        *,
        resume: bool,
        expected_session_id: str | None = None,
    ) -> TransportResult:
        started_at = datetime.now(UTC).isoformat()
        started = time.monotonic()
        request.raw_event_path.parent.mkdir(parents=True, exist_ok=True)
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path = request.raw_event_path.with_suffix(".stderr")
        timed_out = False
        reader_errors: list[BaseException] = []
        session_state: dict[str, str | None] = {
            "session_id": expected_session_id,
            "turn_id": None,
        }
        with request.raw_event_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            self._process = subprocess.Popen(
                command,
                cwd=request.workspace,
                env=safe_codex_environment(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if expected_session_id is not None:
                self._write_running_checkpoint(
                    request,
                    started_at,
                    session_id=expected_session_id,
                    turn_id=None,
                )
            stdout_thread = threading.Thread(
                target=self._copy_stdout,
                args=(
                    request,
                    self._process,
                    stdout,
                    started_at,
                    session_state,
                    reader_errors,
                ),
                daemon=True,
            )
            stderr_thread = threading.Thread(
                target=self._copy_stream,
                args=(self._process.stderr, stderr, reader_errors),
                daemon=True,
            )
            stdout_thread.start()
            stderr_thread.start()
            try:
                return_code = self._process.wait(timeout=request.timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                self._process.terminate()
                try:
                    return_code = self._process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    return_code = self._process.wait(timeout=10)
            stdout_thread.join(timeout=10)
            stderr_thread.join(timeout=10)
            if stdout_thread.is_alive() or stderr_thread.is_alive():
                reader_errors.append(RuntimeError("TRANSPORT_READER_DID_NOT_STOP"))
        if reader_errors:
            raise RuntimeError("TRANSPORT_STREAM_CAPTURE_FAILED") from reader_errors[0]
        duration = round(time.monotonic() - started, 6)
        raw_stderr = stderr_path.read_bytes()
        raw_events = request.raw_event_path.read_bytes()
        event_records = parse_jsonl_bytes(raw_events)
        summary = summarize_events(request.raw_event_path)
        session_id = summary.get("session_id") or expected_session_id
        turn_id = summary.get("turn_id")
        observable = (
            raw_stderr.decode(errors="replace") + "\n" + sanitized_observable(event_records)
        )
        if timed_out:
            observable += "\nRESPONSES_STREAM_TIMEOUT"
        output: dict[str, Any] | None = None
        failure: FailureInfo | None = None
        if return_code == 0:
            try:
                output = self.validate_output(request.output_path, request.output_schema_path)
                assert_blind(output)
            except (ValueError, ValidationError, OSError) as exc:
                failure = classify_failure(str(exc), session_id=session_id, resume=resume)
        else:
            failure = classify_failure(observable, session_id=session_id, resume=resume)
        if failure is None and output is None:
            failure = classify_failure("OUTPUT_MISSING", session_id=session_id, resume=resume)
        if failure is None:
            status = TransportStatus.COMPLETED
        elif failure.failure_class == "AUTH_BLOCKED":
            status = TransportStatus.AUTH_BLOCKED
        elif failure.failure_class == "QUOTA_BLOCKED":
            status = TransportStatus.QUOTA_BLOCKED
        elif failure.failure_class == "SCHEMA_INVALID":
            status = TransportStatus.SCHEMA_FAILED
        elif failure.failure_class in {
            "EVIDENCE_HASH_MISMATCH",
            "POLICY_HASH_MISMATCH",
            "IDENTITY_LEAK",
            "SANDBOX_POLICY_VIOLATION",
            "NETWORK_POLICY_VIOLATION",
            "MCP_POLICY_VIOLATION",
            "MODEL_COMPARABILITY_BROKEN",
        }:
            status = TransportStatus.POLICY_FAILED
        elif failure.resumable:
            status = TransportStatus.TRANSPORT_FAILED_RESUMABLE
        else:
            status = TransportStatus.TRANSPORT_FAILED_NONRESUMABLE
        result = TransportResult(
            role_id=request.role_id,
            adapter=self.name,
            status=status,
            attempt=request.attempt,
            model=request.model,
            reasoning_setting=request.reasoning_setting,
            duration_seconds=duration,
            return_code=return_code,
            output=output,
            session_id=session_id,
            turn_id=turn_id,
            failure=failure,
            raw_event_hash=summary.get("raw_event_hash"),
            stderr_hash=sha256_bytes(raw_stderr),
            event_summary=_trackable_summary(summary),
            token_usage=summary.get("token_usage", {}),
        )
        self._write_checkpoint(request, result, started_at)
        self._last_result = result
        self._process = None
        return result

    def _copy_stdout(
        self,
        request: RoleRunRequest,
        process: subprocess.Popen[bytes],
        destination: Any,
        started_at: str,
        session_state: dict[str, str | None],
        errors: list[BaseException],
    ) -> None:
        try:
            if process.stdout is None:
                raise RuntimeError("TRANSPORT_STDOUT_MISSING")
            for line in iter(process.stdout.readline, b""):
                destination.write(line)
                destination.flush()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                event_type = event.get("type") or event.get("method")
                if event_type == "thread.started":
                    session_id = event.get("thread_id")
                    if isinstance(session_id, str) and session_id:
                        session_state["session_id"] = session_id
                        self._write_running_checkpoint(
                            request,
                            started_at,
                            session_id=session_id,
                            turn_id=session_state["turn_id"],
                        )
                elif event_type in {"turn.started", "turn.completed"}:
                    turn_id = event.get("turn_id")
                    if isinstance(turn_id, str) and turn_id:
                        session_state["turn_id"] = turn_id
                        if session_state["session_id"] is not None:
                            self._write_running_checkpoint(
                                request,
                                started_at,
                                session_id=session_state["session_id"],
                                turn_id=turn_id,
                            )
        except BaseException as exc:  # pragma: no cover - defensive thread boundary
            errors.append(exc)

    @staticmethod
    def _copy_stream(source: Any, destination: Any, errors: list[BaseException]) -> None:
        try:
            if source is None:
                raise RuntimeError("TRANSPORT_STDERR_MISSING")
            while chunk := source.read(65536):
                destination.write(chunk)
                destination.flush()
        except BaseException as exc:  # pragma: no cover - defensive thread boundary
            errors.append(exc)

    def _write_running_checkpoint(
        self,
        request: RoleRunRequest,
        started_at: str,
        *,
        session_id: str,
        turn_id: str | None,
    ) -> None:
        checkpoint = {
            "schema_version": "1.0.0",
            "role_id": request.role_id,
            "adapter": self.name,
            "attempt": request.attempt,
            "model": request.model,
            "reasoning_setting": request.reasoning_setting,
            "input_bundle_hash": request.input_bundle_hash,
            "policy_hash": request.policy_hash,
            "evidence_hash": request.evidence_hash,
            "output_schema_hash": sha256_json(read_json(request.output_schema_path)),
            "started_at": started_at,
            "last_event_at": datetime.now(UTC).isoformat(),
            "completion_status": TransportStatus.RUNNING.value,
            "failure_class": None,
            "observable_code": None,
            "raw_event_hash": None,
            "stderr_hash": None,
            "output_hash": None,
            "resume_allowed": request.attempt < 2,
            "supersedes": request.supersedes,
            "notes": [
                "exact session persisted before terminal transport state",
                "raw events and stderr are ignored",
                "identifier fields are irreversible hashes",
                "hidden reasoning is not retained in tracked output",
            ],
            "event_summary": {},
            "token_usage": {},
        }
        request.checkpoint_store.write(checkpoint, session_id=session_id, turn_id=turn_id)

    def _missing_session_result(self, request: RoleRunRequest) -> TransportResult:
        failure = classify_failure("SESSION_ID_MISSING", session_id=None, resume=True)
        result = TransportResult(
            role_id=request.role_id,
            adapter=self.name,
            status=TransportStatus.TRANSPORT_FAILED_NONRESUMABLE,
            attempt=request.attempt,
            model=request.model,
            reasoning_setting=request.reasoning_setting,
            duration_seconds=0.0,
            return_code=None,
            failure=failure,
        )
        self._last_result = result
        return result

    def _write_checkpoint(
        self, request: RoleRunRequest, result: TransportResult, started_at: str
    ) -> None:
        output_hash = sha256_json(result.output) if result.output is not None else None
        checkpoint = {
            "schema_version": "1.0.0",
            "role_id": request.role_id,
            "adapter": self.name,
            "attempt": request.attempt,
            "model": request.model,
            "reasoning_setting": request.reasoning_setting,
            "input_bundle_hash": request.input_bundle_hash,
            "policy_hash": request.policy_hash,
            "evidence_hash": request.evidence_hash,
            "output_schema_hash": sha256_json(read_json(request.output_schema_path)),
            "started_at": started_at,
            "last_event_at": datetime.now(UTC).isoformat(),
            "completion_status": result.status.value,
            "failure_class": result.failure.failure_class if result.failure else None,
            "observable_code": result.failure.observable_code if result.failure else None,
            "raw_event_hash": result.raw_event_hash,
            "stderr_hash": result.stderr_hash,
            "output_hash": output_hash,
            "resume_allowed": bool(
                result.failure and result.failure.resumable and request.attempt < 2
            ),
            "supersedes": request.supersedes,
            "notes": [
                "raw events and stderr are ignored",
                "identifier fields are irreversible hashes",
                "hidden reasoning is not retained in tracked output",
            ],
            "event_summary": result.event_summary,
            "token_usage": result.token_usage,
            "duration_seconds": result.duration_seconds,
        }
        request.checkpoint_store.write(
            checkpoint, session_id=result.session_id, turn_id=result.turn_id
        )


def _trackable_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in summary.items()
        if key not in {"session_id", "turn_id", "raw_event_hash", "token_usage"}
    }
