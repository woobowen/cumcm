"""Minimal newline-delimited JSON-RPC client for the bundled Codex App Server."""

from __future__ import annotations

import json
import os
import selectors
import subprocess
import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from .exec_adapter import isolation_args, safe_codex_environment


class AppServerError(RuntimeError):
    pass


class AppServerDisconnected(AppServerError):
    pass


class AppServerPolicyRequest(AppServerError):
    pass


class AppServerClient:
    def __init__(
        self,
        *,
        raw_event_path: Path,
        stderr_path: Path,
        timeout_seconds: int,
        command: list[str] | None = None,
    ) -> None:
        self.raw_event_path = raw_event_path
        self.stderr_path = stderr_path
        self.timeout_seconds = timeout_seconds
        self.command = command or ["codex", "app-server", *isolation_args()]
        self.process: subprocess.Popen[bytes] | None = None
        self._stderr_handle: Any = None
        self._raw_handle: Any = None
        self._selector = selectors.DefaultSelector()
        self._buffer = b""
        self._next_id = 1
        self.events: list[dict[str, Any]] = []

    def start(self) -> None:
        self.raw_event_path.parent.mkdir(parents=True, exist_ok=True)
        self.stderr_path.parent.mkdir(parents=True, exist_ok=True)
        self._stderr_handle = self.stderr_path.open("ab")
        self._raw_handle = self.raw_event_path.open("ab")
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._stderr_handle,
            env=safe_codex_environment(),
        )
        if self.process.stdout is None:
            raise AppServerDisconnected("APP_SERVER_STDOUT_MISSING")
        self._selector.register(self.process.stdout, selectors.EVENT_READ)
        self.request(
            "initialize",
            {"clientInfo": {"name": "cumcm-adjudication", "version": "0.2.2"}},
        )
        self.notify("initialized", {})

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._send({"method": method, "params": params})

    def request(
        self, method: str, params: dict[str, Any], *, timeout_seconds: int | None = None
    ) -> Any:
        request_id = self._next_id
        self._next_id += 1
        self._send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + (timeout_seconds or self.timeout_seconds)
        while True:
            message = self._receive(deadline)
            if message.get("id") == request_id and "method" not in message:
                if "error" in message:
                    raise AppServerError(f"JSON_RPC_ERROR:{_error_code(message['error'])}")
                return message.get("result")
            self._handle_async(message)

    def start_thread(
        self,
        *,
        cwd: Path,
        model: str,
        reasoning_setting: str,
    ) -> dict[str, Any]:
        return self.request(
            "thread/start",
            {
                "cwd": str(cwd),
                "model": model,
                "sandbox": "workspace-write",
                "approvalPolicy": "never",
                "ephemeral": False,
                "dynamicTools": [],
                "environments": [],
                "config": {
                    "mcp_servers": {},
                    "model_reasoning_effort": reasoning_setting,
                    "approval_policy": "never",
                    "shell_environment_policy": {"inherit": "none"},
                },
            },
        )

    def resume_thread(
        self,
        *,
        thread_id: str,
        cwd: Path,
        model: str,
        reasoning_setting: str,
    ) -> dict[str, Any]:
        return self.request(
            "thread/resume",
            {
                "threadId": thread_id,
                "cwd": str(cwd),
                "model": model,
                "sandbox": "workspace-write",
                "approvalPolicy": "never",
                "config": {
                    "mcp_servers": {},
                    "model_reasoning_effort": reasoning_setting,
                    "approval_policy": "never",
                    "shell_environment_policy": {"inherit": "none"},
                },
            },
        )

    def start_turn(
        self,
        *,
        thread_id: str,
        prompt: str,
        output_schema: dict[str, Any],
        model: str,
        reasoning_setting: str,
        on_turn_started: Callable[[str], None] | None = None,
    ) -> tuple[str, str, dict[str, Any]]:
        response = self.request(
            "turn/start",
            {
                "threadId": thread_id,
                "input": [{"type": "text", "text": prompt}],
                "model": model,
                "effort": reasoning_setting,
                "approvalPolicy": "never",
                "environments": [],
                "outputSchema": output_schema,
            },
        )
        turn = response.get("turn", {}) if isinstance(response, dict) else {}
        turn_id = turn.get("id")
        if not isinstance(turn_id, str) or not turn_id:
            raise AppServerError("TURN_ID_MISSING")
        if on_turn_started is not None:
            on_turn_started(turn_id)
        text, completed = self.wait_for_turn(thread_id=thread_id, turn_id=turn_id)
        return turn_id, text, completed

    def wait_for_turn(self, *, thread_id: str, turn_id: str) -> tuple[str, dict[str, Any]]:
        deadline = time.monotonic() + self.timeout_seconds
        deltas: list[str] = []
        completed_message: dict[str, Any] | None = None
        while completed_message is None:
            message = self._receive(deadline)
            method = message.get("method")
            params = message.get("params", {})
            self._handle_async(message)
            if method == "item/agentMessage/delta" and params.get("turnId") == turn_id:
                delta = params.get("delta")
                if isinstance(delta, str):
                    deltas.append(delta)
            elif method == "item/completed" and params.get("turnId") == turn_id:
                item = params.get("item", {})
                text = _agent_message_text(item)
                if text and not deltas:
                    deltas.append(text)
            elif method == "turn/completed" and params.get("threadId") == thread_id:
                completed_message = message
        turn = completed_message.get("params", {}).get("turn", {})
        status = turn.get("status")
        if status != "completed":
            raise AppServerError(f"TURN_NOT_COMPLETED:{status}")
        return "".join(deltas), completed_message

    def interrupt(self, *, thread_id: str, turn_id: str) -> None:
        self.request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})

    def close(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        if self.process is not None and self.process.stdout is not None:
            with suppress(KeyError, ValueError):
                self._selector.unregister(self.process.stdout)
        self._selector.close()
        if self._stderr_handle is not None:
            self._stderr_handle.close()
        if self._raw_handle is not None:
            self._raw_handle.close()

    def _send(self, message: dict[str, Any]) -> None:
        if self.process is None or self.process.stdin is None or self.process.poll() is not None:
            raise AppServerDisconnected("APP_SERVER_DISCONNECTED")
        raw = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
        self._record({"direction": "client", **message})
        try:
            self.process.stdin.write(raw)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise AppServerDisconnected("APP_SERVER_BROKEN_PIPE") from exc

    def _receive(self, deadline: float) -> dict[str, Any]:
        while b"\n" not in self._buffer:
            if self.process is None or self.process.stdout is None:
                raise AppServerDisconnected("APP_SERVER_NOT_STARTED")
            if self.process.poll() is not None:
                raise AppServerDisconnected("APP_SERVER_PROCESS_EXITED")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("APP_SERVER_STREAM_TIMEOUT")
            ready = self._selector.select(timeout=remaining)
            if not ready:
                raise TimeoutError("APP_SERVER_STREAM_TIMEOUT")
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise AppServerDisconnected("APP_SERVER_EOF")
            self._buffer += chunk
        line, self._buffer = self._buffer.split(b"\n", 1)
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AppServerError("APP_SERVER_INVALID_JSON") from exc
        if not isinstance(message, dict):
            raise AppServerError("APP_SERVER_MESSAGE_NOT_OBJECT")
        self._record({"direction": "server", **message})
        return message

    def _handle_async(self, message: dict[str, Any]) -> None:
        if "method" in message and "id" in message:
            raise AppServerPolicyRequest(f"UNEXPECTED_SERVER_REQUEST:{message['method']}")
        if "method" in message:
            self.events.append(message)

    def _record(self, message: dict[str, Any]) -> None:
        if self._raw_handle is None:
            return
        self._raw_handle.write(
            json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
        )
        self._raw_handle.flush()


def _agent_message_text(item: Any) -> str | None:
    if not isinstance(item, dict) or item.get("type") != "agentMessage":
        return None
    for key in ("text", "message", "content"):
        value = item.get(key)
        if isinstance(value, str):
            return value
    return None


def _error_code(error: Any) -> str:
    if isinstance(error, dict):
        code = error.get("code")
        if isinstance(code, int | str):
            return str(code)
    return "UNKNOWN"
