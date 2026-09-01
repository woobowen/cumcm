import io
import json
import subprocess

import pytest

from cumcm_skill_lab.adjudication.formal_outputs import _validate_meta_policy
from cumcm_skill_lab.adjudication.role_orchestrator import validate_role_ledger
from cumcm_skill_lab.adjudication.transport.base import TransportStatus
from cumcm_skill_lab.adjudication.transport.checkpoints import CheckpointStore
from cumcm_skill_lab.adjudication.transport.event_sanitization import hash_identifier
from cumcm_skill_lab.adjudication.transport.exec_adapter import ExecAdapter


class TimeoutPopen:
    def __init__(self, command, **kwargs):
        assert kwargs["stdout"] == subprocess.PIPE
        assert kwargs["stderr"] == subprocess.PIPE
        self.stdout = io.BytesIO(
            json.dumps({"type": "thread.started", "thread_id": "timeout-session"}).encode() + b"\n"
        )
        self.stderr = io.BytesIO(b"stream timeout")
        self.waits = 0

    def wait(self, timeout=None):
        self.waits += 1
        if self.waits == 1:
            raise subprocess.TimeoutExpired("codex", timeout)
        return 1

    def terminate(self):
        return None

    def kill(self):
        return None

    def poll(self):
        return None


def test_exec_timeout_preserves_exact_session_for_resume(monkeypatch, tmp_path):
    monkeypatch.setattr("subprocess.Popen", TimeoutPopen)
    request = _request(tmp_path)
    result = ExecAdapter().start_role(request)
    assert result.status == TransportStatus.TRANSPORT_FAILED_RESUMABLE
    assert result.failure.failure_class == "RESPONSES_STREAM_TIMEOUT"
    assert request.checkpoint_store.load_exact_session(request.role_id)["session_id"] == (
        "timeout-session"
    )
    checkpoint = request.checkpoint_store.load_checkpoint(request.role_id)
    assert checkpoint["thread_id"] == hash_identifier("timeout-session")
    assert checkpoint["resume_allowed"] is True


def test_atomic_checkpoint_replace_never_leaves_partial_file(tmp_path):
    store = CheckpointStore(tmp_path)
    first = _checkpoint()
    store.write(first, session_id="session-1", turn_id="turn-1")
    second = {**first, "attempt": 2, "completion_status": "COMPLETED"}
    store.write(second, session_id="session-1", turn_id="turn-2")
    assert store.load_checkpoint("CORRECTNESS_JUDGE")["attempt"] == 2
    assert store.load_exact_session("CORRECTNESS_JUDGE")["turn_id"] == "turn-2"
    assert not list(store.tracked_root.glob(".*.json.*"))


def test_shared_thread_hash_is_rejected(tmp_path):
    ledger = {
        "schema_version": "1.0.0",
        "roles": [
            {
                "role_id": role,
                "status": "COMPLETED" if index < 2 else "PENDING",
                "schema_valid": index < 2,
                "thread_id_hash": "same-thread-hash" if index < 2 else None,
            }
            for index, role in enumerate(
                (
                    "CORRECTNESS_JUDGE",
                    "SCIENTIFIC_VALIDITY_JUDGE",
                    "ENGINEERING_REPRODUCIBILITY_JUDGE",
                    "BLIND_DISSENT_JUDGE",
                    "EVIDENCE_META_ADJUDICATOR",
                    "DECISION_AUDITOR",
                )
            )
        ],
    }
    path = tmp_path / "evals/results/phase-002b/role_ledger.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(ledger), encoding="utf-8")
    assert "ROLE_INDEPENDENCE_BROKEN:SHARED_THREAD" in validate_role_ledger(
        tmp_path, require_complete=False
    )


def test_insufficient_frozen_evidence_rejects_forced_architecture_accept(repo_root):
    output = {
        "decisions": [
            {
                "decision_id": "DECISION-ARCHITECTURE-002A",
                "decision": "AUTOMATED_ACCEPTED",
                "accepted_scope": "SPECIFICATION_ONLY",
                "next_phase_allowed": None,
            },
            {
                "decision_id": "DECISION-RECOVERY-POLICY-002A",
                "decision": "EVIDENCE_INSUFFICIENT",
                "accepted_scope": "NONE",
                "next_phase_allowed": None,
            },
            {
                "decision_id": "DECISION-COMPONENTS-002A",
                "decision": "RETEST_REQUIRED",
                "accepted_scope": "NONE",
                "next_phase_allowed": None,
                "component_results": [],
            },
        ]
    }
    with pytest.raises(
        ValueError,
        match="META_POLICY_VIOLATION:ARCHITECTURE_MUST_BE_EVIDENCE_INSUFFICIENT",
    ):
        _validate_meta_policy(repo_root, output)


def _request(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    schema = {
        "type": "object",
        "properties": {"role": {"const": "CORRECTNESS_JUDGE"}},
        "required": ["role"],
        "additionalProperties": False,
    }
    schema_path = workspace / "output_schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    from cumcm_skill_lab.adjudication.transport.base import RoleRunRequest

    return RoleRunRequest(
        role_id="CORRECTNESS_JUDGE",
        workspace=workspace,
        prompt="offline timeout fixture",
        output_schema_path=schema_path,
        output_path=workspace / "output.json",
        raw_event_path=tmp_path / "raw.jsonl",
        checkpoint_store=CheckpointStore(tmp_path),
        model="gpt-5.6-sol",
        reasoning_setting="medium",
        input_bundle_hash="a" * 64,
        policy_hash="b" * 64,
        evidence_hash="c" * 64,
        attempt=1,
        timeout_seconds=1,
    )


def _checkpoint():
    return {
        "role_id": "CORRECTNESS_JUDGE",
        "adapter": "EXEC_RESUMABLE",
        "attempt": 1,
        "model": "gpt-5.6-sol",
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
