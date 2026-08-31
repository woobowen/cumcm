import io
import json
from pathlib import Path

import pytest

from cumcm_skill_lab.adjudication.transport.adapter_selection import (
    select_initial,
    select_recovery,
)
from cumcm_skill_lab.adjudication.transport.app_server_adapter import AppServerAdapter
from cumcm_skill_lab.adjudication.transport.app_server_client import AppServerDisconnected
from cumcm_skill_lab.adjudication.transport.base import (
    RoleRunRequest,
    TransportStatus,
)
from cumcm_skill_lab.adjudication.transport.checkpoints import CheckpointStore
from cumcm_skill_lab.adjudication.transport.event_sanitization import (
    hash_identifier,
    parse_jsonl_bytes,
    summarize_event_records,
    summarize_events,
)
from cumcm_skill_lab.adjudication.transport.exec_adapter import (
    ExecAdapter,
    safe_codex_environment,
)
from cumcm_skill_lab.adjudication.transport.failure_classification import classify_failure
from cumcm_skill_lab.adjudication.transport.runtime_budget import RunBudget


def _schema(role="CORRECTNESS_JUDGE"):
    return {
        "type": "object",
        "properties": {"role": {"const": role}, "result": {"type": "string"}},
        "required": ["role", "result"],
        "additionalProperties": False,
    }


def _request(tmp_path, *, role="CORRECTNESS_JUDGE", attempt=1):
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    schema_path = workspace / "output_schema.json"
    schema_path.write_text(json.dumps(_schema(role)), encoding="utf-8")
    return RoleRunRequest(
        role_id=role,
        workspace=workspace,
        prompt="Read local evidence and return JSON only.",
        output_schema_path=schema_path,
        output_path=workspace / "last_message.json",
        raw_event_path=tmp_path / f"raw-{attempt}.jsonl",
        checkpoint_store=CheckpointStore(tmp_path),
        model="gpt-5.4",
        reasoning_setting="medium",
        input_bundle_hash="a" * 64,
        policy_hash="b" * 64,
        evidence_hash="c" * 64,
        attempt=attempt,
        timeout_seconds=5,
    )


class FakePopen:
    commands = []
    events = [{"type": "thread.started", "thread_id": "session-1"}, {"type": "turn.completed"}]
    stderr_bytes = b""
    exit_code = 0
    output = {"role": "CORRECTNESS_JUDGE", "result": "ok"}

    def __init__(self, command, **kwargs):
        type(self).commands.append(command)
        self.command = command
        assert kwargs["stdout"] == -1
        assert kwargs["stderr"] == -1
        self.stdout = io.BytesIO()
        self.stderr = io.BytesIO()
        for event in type(self).events:
            self.stdout.write(json.dumps(event).encode() + b"\n")
        self.stdout.seek(0)
        self.stderr.write(type(self).stderr_bytes)
        self.stderr.seek(0)
        if type(self).output is not None:
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text(json.dumps(type(self).output), encoding="utf-8")

    def wait(self, timeout=None):
        return type(self).exit_code

    def poll(self):
        return type(self).exit_code

    def terminate(self):
        pass

    def kill(self):
        pass


@pytest.fixture(autouse=True)
def reset_fake_popen():
    FakePopen.commands = []
    FakePopen.events = [
        {"type": "thread.started", "thread_id": "session-1"},
        {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 2}},
    ]
    FakePopen.stderr_bytes = b""
    FakePopen.exit_code = 0
    FakePopen.output = {"role": "CORRECTNESS_JUDGE", "result": "ok"}


def test_exec_completed_writes_hashed_checkpoint(monkeypatch, tmp_path):
    monkeypatch.setattr("subprocess.Popen", FakePopen)
    request = _request(tmp_path)
    result = ExecAdapter().start_role(request)
    assert result.status == TransportStatus.COMPLETED
    checkpoint = request.checkpoint_store.load_checkpoint(request.role_id)
    assert checkpoint["thread_id"] == hash_identifier("session-1")
    assert "session-1" not in json.dumps(checkpoint)
    assert request.checkpoint_store.load_exact_session(request.role_id)["session_id"] == "session-1"


def test_exec_transport_failure_with_session_is_resumable(monkeypatch, tmp_path):
    FakePopen.exit_code = 1
    FakePopen.output = None
    FakePopen.stderr_bytes = b"websocket connection reset"
    monkeypatch.setattr("subprocess.Popen", FakePopen)
    result = ExecAdapter().start_role(_request(tmp_path))
    assert result.status == TransportStatus.TRANSPORT_FAILED_RESUMABLE
    assert result.failure.failure_class == "RESPONSES_CONNECT_RESET"


def test_exec_failure_without_session_is_nonresumable(monkeypatch, tmp_path):
    FakePopen.events = [{"type": "turn.failed", "error": {"message": "timeout"}}]
    FakePopen.exit_code = 1
    FakePopen.output = None
    monkeypatch.setattr("subprocess.Popen", FakePopen)
    result = ExecAdapter().start_role(_request(tmp_path))
    assert result.status == TransportStatus.TRANSPORT_FAILED_NONRESUMABLE
    assert result.failure.failure_class == "SESSION_ID_MISSING"
    assert result.failure.next_adapter == "APP_SERVER_RESUMABLE"


def test_exec_resume_uses_exact_session_and_never_last(monkeypatch, tmp_path):
    monkeypatch.setattr("subprocess.Popen", FakePopen)
    request = _request(tmp_path, attempt=1)
    ExecAdapter().start_role(request)
    resumed = _request(tmp_path, attempt=2)
    result = ExecAdapter().resume_role(resumed)
    command = FakePopen.commands[-1]
    assert result.status == TransportStatus.COMPLETED
    assert "session-1" in command
    assert "--last" not in command
    assert "--ephemeral" not in command


def test_exec_resume_without_secret_session_fails_closed(tmp_path):
    result = ExecAdapter().resume_role(_request(tmp_path, attempt=2))
    assert result.status == TransportStatus.TRANSPORT_FAILED_NONRESUMABLE
    assert result.failure.failure_class == "SESSION_ID_MISSING"


class FakeAppClient:
    next_thread = 0
    calls = []
    observed_model = "gpt-5.4"
    disconnect = False

    def __init__(self, *, raw_event_path, stderr_path, timeout_seconds):
        self.raw_event_path = raw_event_path
        self.stderr_path = stderr_path
        self.timeout_seconds = timeout_seconds

    def start(self):
        self.raw_event_path.parent.mkdir(parents=True, exist_ok=True)
        self.raw_event_path.write_text("", encoding="utf-8")

    def start_thread(self, *, cwd, model, reasoning_setting):
        type(self).next_thread += 1
        thread_id = f"app-thread-{type(self).next_thread}"
        type(self).calls.append(("start", thread_id, cwd, model, reasoning_setting))
        return {"thread": {"id": thread_id}, "model": type(self).observed_model}

    def resume_thread(self, *, thread_id, cwd, model, reasoning_setting):
        type(self).calls.append(("resume", thread_id, cwd, model, reasoning_setting))
        return {"thread": {"id": thread_id}, "model": type(self).observed_model}

    def start_turn(
        self,
        *,
        thread_id,
        prompt,
        output_schema,
        model,
        reasoning_setting,
        on_turn_started=None,
    ):
        type(self).calls.append(("turn", thread_id, prompt, model, reasoning_setting))
        if on_turn_started is not None:
            on_turn_started("turn-1")
        if type(self).disconnect:
            raise AppServerDisconnected("APP_SERVER_PROCESS_EXITED")
        role = output_schema["properties"]["role"]["const"]
        return "turn-1", json.dumps({"role": role, "result": "ok"}), {}

    def interrupt(self, *, thread_id, turn_id):
        type(self).calls.append(("interrupt", thread_id, turn_id))

    def close(self):
        pass


@pytest.fixture(autouse=True)
def reset_fake_app_client():
    FakeAppClient.next_thread = 0
    FakeAppClient.calls = []
    FakeAppClient.observed_model = "gpt-5.4"
    FakeAppClient.disconnect = False


def test_app_server_thread_and_turn_complete(tmp_path):
    request = _request(tmp_path)
    result = AppServerAdapter(FakeAppClient).start_role(request)
    assert result.status == TransportStatus.COMPLETED
    assert result.session_id == "app-thread-1"
    assert result.turn_id == "turn-1"
    assert [call[0] for call in FakeAppClient.calls] == ["start", "turn"]


def test_app_server_resume_uses_same_thread(tmp_path):
    request = _request(tmp_path)
    AppServerAdapter(FakeAppClient).start_role(request)
    resumed = _request(tmp_path, attempt=2)
    result = AppServerAdapter(FakeAppClient).resume_role(resumed)
    assert result.status == TransportStatus.COMPLETED
    assert any(call[:2] == ("resume", "app-thread-1") for call in FakeAppClient.calls)


def test_app_server_disconnect_is_classified(tmp_path):
    FakeAppClient.disconnect = True
    result = AppServerAdapter(FakeAppClient).start_role(_request(tmp_path))
    assert result.status == TransportStatus.TRANSPORT_FAILED_RESUMABLE
    assert result.failure.failure_class == "APP_SERVER_DISCONNECTED"
    exact = _request(tmp_path).checkpoint_store.load_exact_session("CORRECTNESS_JUDGE")
    assert exact == {"session_id": "app-thread-1", "turn_id": "turn-1"}


def test_app_server_model_mismatch_fails_policy(tmp_path):
    FakeAppClient.observed_model = "different-model"
    result = AppServerAdapter(FakeAppClient).start_role(_request(tmp_path))
    assert result.status == TransportStatus.POLICY_FAILED
    assert result.failure.failure_class == "MODEL_COMPARABILITY_BROKEN"


def test_two_app_roles_get_distinct_threads(tmp_path):
    first = AppServerAdapter(FakeAppClient).start_role(_request(tmp_path / "first"))
    second = AppServerAdapter(FakeAppClient).start_role(
        _request(tmp_path / "second", role="SCIENTIFIC_VALIDITY_JUDGE")
    )
    assert first.session_id != second.session_id


@pytest.mark.parametrize(
    ("observable", "expected"),
    [
        ("not logged in", "AUTH_BLOCKED"),
        ("usage limit reached", "QUOTA_BLOCKED"),
        ("websocket connection reset", "RESPONSES_CONNECT_RESET"),
        ("stream timeout", "RESPONSES_STREAM_TIMEOUT"),
        ("model unavailable", "MODEL_UNAVAILABLE"),
        ("model mismatch", "MODEL_COMPARABILITY_BROKEN"),
        ("schema invalid", "SCHEMA_INVALID"),
        ("OUTPUT_MISSING", "OUTPUT_MISSING"),
        ("EVIDENCE_HASH_MISMATCH", "EVIDENCE_HASH_MISMATCH"),
        ("POLICY_HASH_MISMATCH", "POLICY_HASH_MISMATCH"),
        ("IDENTITY_LEAK", "IDENTITY_LEAK"),
        ("SANDBOX_POLICY_VIOLATION", "SANDBOX_POLICY_VIOLATION"),
        ("NETWORK_POLICY_VIOLATION", "NETWORK_POLICY_VIOLATION"),
        ("MCP_POLICY_VIOLATION", "MCP_POLICY_VIOLATION"),
    ],
)
def test_failure_classes_are_specific(observable, expected):
    assert classify_failure(observable, session_id="session").failure_class == expected


def test_failure_without_session_uses_specific_missing_class():
    failure = classify_failure("websocket reset", session_id=None)
    assert failure.failure_class == "SESSION_ID_MISSING"
    assert failure.next_adapter == "APP_SERVER_RESUMABLE"


def test_app_server_eof_classification():
    failure = classify_failure(
        "APP_SERVER_EOF", session_id="thread", adapter="APP_SERVER_RESUMABLE"
    )
    assert failure.failure_class == "APP_SERVER_DISCONNECTED"


def test_event_summary_drops_message_and_reasoning_content():
    events = [
        {"type": "thread.started", "thread_id": "secret-session"},
        {"type": "item.completed", "item": {"type": "reasoning", "text": "hidden"}},
        {"type": "turn.completed", "usage": {"input_tokens": 7, "output_tokens": 3}},
    ]
    summary = summarize_event_records(events)
    assert "hidden" not in json.dumps(summary)
    assert summary["reasoning_content_retained"] is False
    assert summary["token_usage"] == {"input_tokens": 7, "output_tokens": 3}


def test_malformed_raw_event_is_counted_not_copied(tmp_path):
    path = tmp_path / "raw.jsonl"
    path.write_bytes(b"not-json\n")
    summary = summarize_events(path)
    assert summary["event_counts"] == {"MALFORMED_JSON_EVENT": 1}
    assert "not-json" not in json.dumps(summary)


def test_identifier_hash_is_stable_and_irreversible_representation():
    assert hash_identifier("thread-1") == hash_identifier("thread-1")
    assert hash_identifier("thread-1") != "thread-1"
    assert hash_identifier(None) is None


def test_parse_jsonl_ignores_blank_lines():
    assert parse_jsonl_bytes(b'\n{"type":"x"}\n\n') == [{"type": "x"}]


def test_checkpoint_write_is_atomic_and_separates_exact_id(tmp_path):
    store = CheckpointStore(tmp_path)
    checkpoint = _checkpoint_fields()
    store.write(checkpoint, session_id="exact-session", turn_id="exact-turn")
    tracked = store.load_checkpoint("CORRECTNESS_JUDGE")
    assert tracked["thread_id"] == hash_identifier("exact-session")
    assert store.load_exact_session("CORRECTNESS_JUDGE") == {
        "session_id": "exact-session",
        "turn_id": "exact-turn",
    }
    assert not list(store.tracked_root.glob(".*.json.*"))


def test_checkpoint_missing_required_field_fails(tmp_path):
    store = CheckpointStore(tmp_path)
    checkpoint = _checkpoint_fields()
    del checkpoint["model"]
    with pytest.raises(ValueError, match="CHECKPOINT_FIELDS_MISSING:model"):
        store.write(checkpoint, session_id=None, turn_id=None)


def test_safe_environment_never_copies_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-value")
    monkeypatch.setenv("PATH", "/bin")
    environment = safe_codex_environment()
    assert "OPENAI_API_KEY" not in environment
    assert environment["PATH"] == "/bin"


def test_initial_adapter_is_exec():
    assert (select_initial().adapter, select_initial().action) == ("EXEC_RESUMABLE", "START")


def test_resumable_failure_selects_exact_exec_resume():
    action = select_recovery(
        status=TransportStatus.TRANSPORT_FAILED_RESUMABLE,
        exact_session_available=True,
        attempts_used=1,
    )
    assert (action.adapter, action.action) == ("EXEC_RESUMABLE", "RESUME")


def test_interrupted_running_checkpoint_selects_exact_resume():
    action = select_recovery(
        status=TransportStatus.RUNNING,
        exact_session_available=True,
        attempts_used=1,
        previous_adapter="APP_SERVER_RESUMABLE",
    )
    assert (action.adapter, action.action) == ("APP_SERVER_RESUMABLE", "RESUME")


def test_nonresumable_failure_selects_app_server():
    action = select_recovery(
        status=TransportStatus.TRANSPORT_FAILED_NONRESUMABLE,
        exact_session_available=False,
        attempts_used=1,
    )
    assert (action.adapter, action.action) == ("APP_SERVER_RESUMABLE", "START")


def test_two_attempts_exhaust_role():
    action = select_recovery(
        status=TransportStatus.TRANSPORT_FAILED_RESUMABLE,
        exact_session_available=True,
        attempts_used=2,
    )
    assert (action.adapter, action.action) == ("NONE", "EXHAUSTED")


def test_per_role_budget_limit(tmp_path):
    budget = RunBudget(tmp_path)
    budget.record_start("CORRECTNESS_JUDGE", "EXEC_RESUMABLE", "INITIAL")
    budget.record_start("CORRECTNESS_JUDGE", "EXEC_RESUMABLE", "RESUME")
    with pytest.raises(RuntimeError, match="ROLE_REAL_RUN_BUDGET_EXHAUSTED"):
        budget.record_start("CORRECTNESS_JUDGE", "APP_SERVER_RESUMABLE", "FALLBACK")


def test_total_phase_budget_limit(tmp_path):
    budget = RunBudget(tmp_path)
    for index in range(8):
        budget.record_start(f"ROLE-{index}", "EXEC_RESUMABLE", "INITIAL")
    assert budget.remaining() == 0
    with pytest.raises(RuntimeError, match="TOTAL_REAL_RUN_BUDGET_EXHAUSTED"):
        budget.record_start("ROLE-9", "EXEC_RESUMABLE", "INITIAL")


def test_budget_result_updates_exact_start(tmp_path):
    budget = RunBudget(tmp_path)
    budget.record_start("CORRECTNESS_JUDGE", "EXEC_RESUMABLE", "INITIAL")
    budget.record_result("CORRECTNESS_JUDGE", 1, "COMPLETED")
    assert budget.load()["starts"][0]["completion_status"] == "COMPLETED"


def _checkpoint_fields():
    return {
        "role_id": "CORRECTNESS_JUDGE",
        "adapter": "EXEC_RESUMABLE",
        "attempt": 1,
        "model": "gpt-5.4",
        "reasoning_setting": "medium",
        "input_bundle_hash": "a" * 64,
        "policy_hash": "b" * 64,
        "output_schema_hash": "c" * 64,
        "started_at": "2026-09-01T00:00:00Z",
        "last_event_at": "2026-09-01T00:00:01Z",
        "completion_status": "RUNNING",
        "failure_class": None,
        "raw_event_hash": None,
        "output_hash": None,
        "resume_allowed": True,
        "supersedes": None,
        "notes": [],
    }
