"""Codex App Server fallback with independent persistent threads."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from jsonschema import ValidationError

from ..judge_runner import assert_blind
from ..models import read_json, sha256_bytes, sha256_json, write_json
from .app_server_client import (
    AppServerClient,
    AppServerDisconnected,
    AppServerError,
    AppServerPolicyRequest,
)
from .base import RoleRunRequest, TransportAdapter, TransportResult, TransportStatus
from .event_sanitization import summarize_events
from .failure_classification import FailureInfo, classify_failure

ClientFactory = Callable[..., AppServerClient]


class AppServerAdapter(TransportAdapter):
    name = "APP_SERVER_RESUMABLE"

    def __init__(self, client_factory: ClientFactory = AppServerClient) -> None:
        self.client_factory = client_factory
        self._client: AppServerClient | None = None
        self._thread_id: str | None = None
        self._turn_id: str | None = None
        self._last_result: TransportResult | None = None

    def start_role(self, request: RoleRunRequest) -> TransportResult:
        return self._run(request, resume=False)

    def resume_role(self, request: RoleRunRequest) -> TransportResult:
        return self._run(request, resume=True)

    def poll_role(self) -> TransportResult | None:
        return self._last_result

    def cancel_role(self) -> None:
        if self._client is not None and self._thread_id and self._turn_id:
            try:
                self._client.interrupt(thread_id=self._thread_id, turn_id=self._turn_id)
            finally:
                self._client.close()

    def _run(self, request: RoleRunRequest, *, resume: bool) -> TransportResult:
        started_at = datetime.now(UTC).isoformat()
        started = time.monotonic()
        stderr_path = request.raw_event_path.with_suffix(".stderr")
        self._client = self.client_factory(
            raw_event_path=request.raw_event_path,
            stderr_path=stderr_path,
            timeout_seconds=request.timeout_seconds,
        )
        output: dict[str, Any] | None = None
        failure: FailureInfo | None = None
        return_code: int | None = None
        try:
            self._client.start()
            if resume:
                exact = request.checkpoint_store.load_exact_session(request.role_id)
                thread_id = exact.get("session_id") if exact else None
                if not isinstance(thread_id, str) or not thread_id:
                    raise AppServerError("SESSION_ID_MISSING")
                response = self._client.resume_thread(
                    thread_id=thread_id,
                    cwd=request.workspace,
                    model=request.model,
                    reasoning_setting=request.reasoning_setting,
                )
            else:
                response = self._client.start_thread(
                    cwd=request.workspace,
                    model=request.model,
                    reasoning_setting=request.reasoning_setting,
                )
                thread = response.get("thread", {}) if isinstance(response, dict) else {}
                thread_id = thread.get("id")
                if not isinstance(thread_id, str) or not thread_id:
                    raise AppServerError("SESSION_ID_MISSING")
            observed_model = response.get("model") if isinstance(response, dict) else None
            if observed_model != request.model:
                raise AppServerError("MODEL_COMPARABILITY_BROKEN")
            self._thread_id = thread_id
            prompt = request.prompt
            if resume:
                prompt = (
                    "Continue only the same formal role using the unchanged local bundle and "
                    "output_schema.json. Add no new assumptions. Return the required JSON only."
                )
            turn_id, text, _ = self._client.start_turn(
                thread_id=thread_id,
                prompt=prompt,
                output_schema=read_json(request.output_schema_path),
                model=request.model,
                reasoning_setting=request.reasoning_setting,
            )
            self._turn_id = turn_id
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("SCHEMA_INVALID:OUTPUT_NOT_OBJECT")
            write_json(request.output_path, parsed)
            output = self.validate_output(request.output_path, request.output_schema_path)
            assert_blind(output)
            return_code = 0
        except (AppServerDisconnected, TimeoutError) as exc:
            failure = classify_failure(
                str(exc),
                session_id=self._thread_id,
                adapter=self.name,
                resume=resume,
            )
        except AppServerPolicyRequest as exc:
            failure = classify_failure(
                "MCP_POLICY_VIOLATION:" + str(exc),
                session_id=self._thread_id,
                adapter=self.name,
                resume=resume,
            )
        except (AppServerError, ValueError, ValidationError, json.JSONDecodeError) as exc:
            failure = classify_failure(
                str(exc),
                session_id=self._thread_id,
                adapter=self.name,
                resume=resume,
            )
        finally:
            if self._client is not None:
                self._client.close()
        duration = round(time.monotonic() - started, 6)
        summary = summarize_events(request.raw_event_path)
        if failure is None:
            status = TransportStatus.COMPLETED
        elif failure.failure_class == "AUTH_BLOCKED":
            status = TransportStatus.AUTH_BLOCKED
        elif failure.failure_class == "QUOTA_BLOCKED":
            status = TransportStatus.QUOTA_BLOCKED
        elif failure.failure_class == "SCHEMA_INVALID":
            status = TransportStatus.SCHEMA_FAILED
        elif failure.failure_class in {
            "MODEL_COMPARABILITY_BROKEN",
            "MCP_POLICY_VIOLATION",
            "IDENTITY_LEAK",
            "EVIDENCE_HASH_MISMATCH",
            "POLICY_HASH_MISMATCH",
        }:
            status = TransportStatus.POLICY_FAILED
        elif failure.resumable:
            status = TransportStatus.TRANSPORT_FAILED_RESUMABLE
        else:
            status = TransportStatus.TRANSPORT_FAILED_NONRESUMABLE
        raw_stderr = stderr_path.read_bytes() if stderr_path.is_file() else b""
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
            session_id=self._thread_id,
            turn_id=self._turn_id,
            failure=failure,
            raw_event_hash=summary.get("raw_event_hash"),
            stderr_hash=sha256_bytes(raw_stderr),
            event_summary={
                key: value
                for key, value in summary.items()
                if key not in {"session_id", "turn_id", "raw_event_hash", "token_usage"}
            },
            token_usage=summary.get("token_usage", {}),
        )
        self._write_checkpoint(request, result, started_at)
        self._last_result = result
        return result

    def _write_checkpoint(
        self, request: RoleRunRequest, result: TransportResult, started_at: str
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
            "completion_status": result.status.value,
            "failure_class": result.failure.failure_class if result.failure else None,
            "observable_code": result.failure.observable_code if result.failure else None,
            "raw_event_hash": result.raw_event_hash,
            "stderr_hash": result.stderr_hash,
            "output_hash": sha256_json(result.output) if result.output is not None else None,
            "resume_allowed": bool(
                result.failure and result.failure.resumable and request.attempt < 2
            ),
            "supersedes": request.supersedes,
            "notes": [
                "App Server JSON-RPC content is retained only in ignored raw events",
                "identifier fields are irreversible hashes",
                "hidden reasoning is not retained in tracked output",
            ],
            "event_summary": result.event_summary,
            "token_usage": result.token_usage,
        }
        request.checkpoint_store.write(
            checkpoint, session_id=result.session_id, turn_id=result.turn_id
        )
