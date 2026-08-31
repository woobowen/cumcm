import shutil
from datetime import UTC, datetime

import pytest

from cumcm_skill_lab.adjudication.bundles.builder import build_all
from cumcm_skill_lab.adjudication.bundles.role_views import ROLE_ORDER
from cumcm_skill_lab.adjudication.formal_outputs import (
    DECISION_FILENAMES,
    create_pre_audit_decisions,
    formal_output_path,
)
from cumcm_skill_lab.adjudication.models import read_json, sha256_json, write_json
from cumcm_skill_lab.adjudication.phase002b_replay import build_replay
from cumcm_skill_lab.adjudication.phase002b_reporting import load_inputs, render_all
from cumcm_skill_lab.adjudication.phase002b_status import (
    COMPLETE,
    classify_completion,
    phase003_allowed,
)
from cumcm_skill_lab.adjudication.role_orchestrator import RoleOrchestrator
from cumcm_skill_lab.adjudication.transport.base import TransportResult, TransportStatus
from cumcm_skill_lab.adjudication.transport.checkpoints import CheckpointStore
from cumcm_skill_lab.adjudication.transport.failure_classification import classify_failure
from cumcm_skill_lab.adjudication.transport.runtime_budget import RunBudget


@pytest.fixture
def isolated_repo(repo_root, tmp_path):
    target = tmp_path / "repo"
    shutil.copytree(
        repo_root,
        target,
        ignore=shutil.ignore_patterns(".git", ".venv", ".cache", "__pycache__"),
    )
    result = build_all(target, check=False)
    assert result["status"] == "PASS"
    return target


class SuccessfulRoleAdapter:
    name = "EXEC_RESUMABLE"

    def start_role(self, request):
        return self._complete(request)

    def resume_role(self, request):
        return self._complete(request)

    def poll_role(self):
        return None

    def cancel_role(self):
        return None

    def _complete(self, request):
        output = _valid_runtime_output(request)
        now = datetime.now(UTC).isoformat()
        session_id = f"mock-session-{request.role_id}"
        turn_id = f"mock-turn-{request.role_id}"
        request.checkpoint_store.write(
            {
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
                "started_at": now,
                "last_event_at": now,
                "completion_status": "COMPLETED",
                "failure_class": None,
                "observable_code": None,
                "raw_event_hash": "a" * 64,
                "stderr_hash": "b" * 64,
                "output_hash": sha256_json(output),
                "resume_allowed": False,
                "supersedes": request.supersedes,
                "notes": ["offline mock adapter"],
                "event_summary": {"event_counts": {"turn.completed": 1}},
                "token_usage": {},
            },
            session_id=session_id,
            turn_id=turn_id,
        )
        return TransportResult(
            role_id=request.role_id,
            adapter=self.name,
            status=TransportStatus.COMPLETED,
            attempt=request.attempt,
            model=request.model,
            reasoning_setting=request.reasoning_setting,
            duration_seconds=0.01,
            return_code=0,
            output=output,
            session_id=session_id,
            turn_id=turn_id,
            raw_event_hash="a" * 64,
            stderr_hash="b" * 64,
        )


class SuccessfulAppAdapter(SuccessfulRoleAdapter):
    name = "APP_SERVER_RESUMABLE"


class ResumeAfterResetAdapter(SuccessfulRoleAdapter):
    start_calls = 0
    resume_calls = 0

    def start_role(self, request):
        type(self).start_calls += 1
        return _transport_failure(
            request,
            adapter=self.name,
            observable="websocket connection reset",
            session_id="resume-session",
        )

    def resume_role(self, request):
        type(self).resume_calls += 1
        return self._complete(request)


class NonresumableExecAdapter(SuccessfulRoleAdapter):
    def start_role(self, request):
        return _transport_failure(
            request,
            adapter=self.name,
            observable="websocket connection reset",
            session_id=None,
        )


def test_mock_six_role_chain_meta_audit_and_replay(monkeypatch, isolated_repo):
    decisions, replay = _complete_six_role_chain(monkeypatch, isolated_repo)
    assert RunBudget(isolated_repo).remaining() == 2
    assert replay["stable"] is True
    assert len(set(replay["variants"].values())) == 1
    architecture = next(item for item in decisions if item["decision_type"] == "ARCHITECTURE")
    assert architecture["decision"] == "EVIDENCE_INSUFFICIENT"
    assert architecture["next_phase_allowed"] is None


def test_exec_to_exact_resume_chain(monkeypatch, isolated_repo):
    _disable_freeze_git(monkeypatch)
    ResumeAfterResetAdapter.start_calls = 0
    ResumeAfterResetAdapter.resume_calls = 0
    orchestrator = RoleOrchestrator(
        isolated_repo,
        adapter_factories={
            "EXEC_RESUMABLE": ResumeAfterResetAdapter,
            "APP_SERVER_RESUMABLE": SuccessfulAppAdapter,
        },
    )
    outcome = orchestrator.execute("CORRECTNESS_JUDGE", allow_recovery=True)
    assert outcome.completion_status == "COMPLETED"
    assert outcome.attempts == 2
    assert ResumeAfterResetAdapter.start_calls == 1
    assert ResumeAfterResetAdapter.resume_calls == 1


def test_exec_to_app_server_fallback(monkeypatch, isolated_repo):
    _disable_freeze_git(monkeypatch)
    orchestrator = RoleOrchestrator(
        isolated_repo,
        adapter_factories={
            "EXEC_RESUMABLE": NonresumableExecAdapter,
            "APP_SERVER_RESUMABLE": SuccessfulAppAdapter,
        },
    )
    outcome = orchestrator.execute("CORRECTNESS_JUDGE", allow_recovery=True)
    assert outcome.completion_status == "COMPLETED"
    assert outcome.adapter == "APP_SERVER_RESUMABLE"
    starts = RunBudget(isolated_repo).load()["starts"]
    assert [item["start_kind"] for item in starts] == ["INITIAL", "FALLBACK"]


def test_interrupted_running_checkpoint_resumes_exact_app_thread(monkeypatch, isolated_repo):
    _disable_freeze_git(monkeypatch)
    role = "CORRECTNESS_JUDGE"
    manifest = read_json(
        isolated_repo / "evals/results/phase-002b/bundle_manifests/correctness.json"
    )
    budget = RunBudget(isolated_repo)
    budget.record_start(role, "APP_SERVER_RESUMABLE", "INITIAL")
    store = CheckpointStore(isolated_repo)
    store.write(
        _checkpoint(role, manifest, status="RUNNING", adapter="APP_SERVER_RESUMABLE"),
        session_id="interrupted-thread",
        turn_id="interrupted-turn",
    )
    orchestrator = RoleOrchestrator(
        isolated_repo,
        adapter_factories={
            "EXEC_RESUMABLE": SuccessfulRoleAdapter,
            "APP_SERVER_RESUMABLE": SuccessfulAppAdapter,
        },
        budget=budget,
    )
    outcome = orchestrator.execute(role, allow_recovery=True)
    assert outcome.completion_status == "COMPLETED"
    assert outcome.attempts == 2
    assert budget.load()["starts"][-1]["start_kind"] == "RESUME"


def test_partial_checkpoint_restart_does_not_rerun_completed_role(monkeypatch, isolated_repo):
    _disable_freeze_git(monkeypatch)
    factories = {
        "EXEC_RESUMABLE": SuccessfulRoleAdapter,
        "APP_SERVER_RESUMABLE": SuccessfulAppAdapter,
    }
    first = RoleOrchestrator(isolated_repo, adapter_factories=factories)
    assert first.execute(ROLE_ORDER[0], allow_recovery=True).completion_status == "COMPLETED"
    restarted = RoleOrchestrator(isolated_repo, adapter_factories=factories)
    skipped = restarted.execute(ROLE_ORDER[0], allow_recovery=True)
    assert skipped.skipped_completed is True
    assert restarted.execute(ROLE_ORDER[1], allow_recovery=True).completion_status == "COMPLETED"
    assert len(RunBudget(isolated_repo).load()["starts"]) == 2


def test_meta_is_blocked_until_four_blind_roles(monkeypatch, isolated_repo):
    _disable_freeze_git(monkeypatch)
    orchestrator = RoleOrchestrator(
        isolated_repo,
        adapter_factories={
            "EXEC_RESUMABLE": SuccessfulRoleAdapter,
            "APP_SERVER_RESUMABLE": SuccessfulAppAdapter,
        },
    )
    with pytest.raises(RuntimeError, match="ROLE_PRECONDITION_MISSING:CORRECTNESS_JUDGE"):
        orchestrator.execute("EVIDENCE_META_ADJUDICATOR", allow_recovery=True)


def test_audit_is_blocked_until_meta_and_proposals(monkeypatch, isolated_repo):
    _disable_freeze_git(monkeypatch)
    factories = {
        "EXEC_RESUMABLE": SuccessfulRoleAdapter,
        "APP_SERVER_RESUMABLE": SuccessfulAppAdapter,
    }
    orchestrator = RoleOrchestrator(isolated_repo, adapter_factories=factories)
    for role in ROLE_ORDER[:4]:
        orchestrator.execute(role, allow_recovery=True)
    with pytest.raises(RuntimeError, match="ROLE_PRECONDITION_MISSING:EVIDENCE_META_ADJUDICATOR"):
        orchestrator.execute("DECISION_AUDITOR", allow_recovery=True)


@pytest.mark.parametrize("decision", ["EVIDENCE_INSUFFICIENT", "AUTOMATED_ABSTAINED"])
def test_non_accepting_decision_still_counts_as_complete(decision):
    roles = [{"role_id": role, "status": "COMPLETED", "schema_valid": True} for role in ROLE_ORDER]
    decisions = [{"decision_id": f"D-{index}", "decision": decision} for index in range(3)]
    assert classify_completion(roles, decisions, {"result": "PASS"}, {"stable": True}) == COMPLETE


def test_phase003_remains_blocked_without_accepted_architecture():
    decisions = [
        {"decision_type": "ARCHITECTURE", "decision": "EVIDENCE_INSUFFICIENT"},
        {
            "decision_type": "COMPONENTS",
            "decision": "AUTOMATED_ACCEPTED",
            "accepted_scope": "SPECIFICATION_ONLY",
        },
    ]
    assert not phase003_allowed(decisions, {"result": "PASS"}, {"stable": True})


def test_completed_adjudication_does_not_force_acceptance():
    roles = [{"role_id": role, "status": "COMPLETED", "schema_valid": True} for role in ROLE_ORDER]
    decisions = [
        {"decision_id": f"D-{index}", "decision": "EVIDENCE_INSUFFICIENT"} for index in range(3)
    ]
    assert classify_completion(roles, decisions, {"result": "PASS"}, {"stable": True}) == COMPLETE
    assert all(item["decision"] != "AUTOMATED_ACCEPTED" for item in decisions)


def test_reports_render_actual_decision_records(monkeypatch, isolated_repo):
    decisions, replay = _complete_six_role_chain(monkeypatch, isolated_repo)
    by_type = {item["decision_type"]: item for item in decisions}
    decision_dir = isolated_repo / "evals/results/phase-002b/automated_decisions"
    for filename, decision_type in zip(
        DECISION_FILENAMES, ("ARCHITECTURE", "RECOVERY_POLICY", "COMPONENTS"), strict=True
    ):
        write_json(decision_dir / filename, by_type[decision_type])
    write_json(isolated_repo / "evals/results/phase-002b/replay/replay.json", replay)
    reports = render_all(load_inputs(isolated_repo))
    acceptance = reports["phase-002b-acceptance.md"]
    assert "EVIDENCE_INSUFFICIENT" in acceptance
    assert "DECISION-ARCHITECTURE-002A" in acceptance
    assert "Phase 003 allowed: `False`" in acceptance


def _valid_runtime_output(request):
    schema = read_json(request.output_schema_path)
    catalog = read_json(request.workspace / "evidence_catalog.json")["identifiers"]
    evidence_ref = "eligibility:summary"
    test_ref = next(item for item in catalog if item.startswith("TEST-"))
    common = {
        "role": request.role_id,
        "bundle_hash": schema["properties"]["bundle_hash"]["const"],
        "policy_hash": request.policy_hash,
        "evidence_hash": request.evidence_hash,
        "majority_vote_used": False,
        "human_technical_gate_used": False,
        "recovery_ranked": False,
        "confidence": 0.8,
    }
    finding = {
        "finding_id": f"FORMAL-{request.role_id}-001",
        "severity": "WARNING",
        "target": "frozen evidence",
        "statement": "The frozen comparison is insufficient for architecture selection.",
        "evidence_refs": [evidence_ref],
        "testability": "TESTABLE",
        "status": "UNRESOLVED",
    }
    if request.role_id in ROLE_ORDER[:3]:
        return {
            **common,
            "recommendation": "INSUFFICIENT",
            "recommendation_evidence_refs": [evidence_ref],
            "evidence_sufficiency": "INSUFFICIENT",
            "findings": [finding],
            "unresolved_blockers": [],
            "uncertainties": ["Insufficient balanced cases and repeats."],
        }
    if request.role_id == "BLIND_DISSENT_JUDGE":
        return {
            **common,
            "recommendation": "INSUFFICIENT",
            "evidence_sufficiency": "INSUFFICIENT",
            "findings": [finding],
            "unresolved_blockers": [],
            "strongest_dissent": "Architecture benefit is not established.",
            "strongest_dissent_evidence_refs": [evidence_ref],
            "test_evidence_refs": [test_ref],
            "uncertainties": ["No repeat-level superiority evidence."],
        }
    if request.role_id == "EVIDENCE_META_ADJUDICATOR":
        return {
            **common,
            "thresholds_unchanged": True,
            "hard_gate_status": "UNKNOWN",
            "evidence_sufficiency": "INSUFFICIENT",
            "unresolved_blockers": [],
            "decisions": _meta_decisions(evidence_ref, test_ref),
        }
    checks = {key: True for key in schema["properties"]["checks"]["properties"]}
    audit_ref = "META-ADJUDICATION-002B"
    assert audit_ref in catalog
    return {
        **common,
        "result": "PASS",
        "checks": checks,
        "failures": [],
        "blockers": [],
        "replayable": True,
        "audit_evidence_refs": [audit_ref],
    }


def _meta_decisions(evidence_ref, test_ref):
    component_ids = (
        "accepted-versus-done-workflow-state",
        "claim-evidence-support-gate",
        "hash-bound-reproducibility-manifest",
        "leakage-safe-model-comparison-gate",
    )
    common = {
        "target_ids": ["FROZEN-SCOPE"],
        "accepted_scope": "NONE",
        "hard_gate_status": "UNKNOWN",
        "evidence_sufficiency": "INSUFFICIENT",
        "reason_codes": ["FROZEN_EVIDENCE_INSUFFICIENT"],
        "evidence_refs": [evidence_ref],
        "dissent_refs": [],
        "retest_requirements": [test_ref],
        "confidence": 0.8,
        "next_phase_allowed": None,
    }
    return [
        {
            **common,
            "decision_id": "DECISION-ARCHITECTURE-002A",
            "decision_type": "ARCHITECTURE",
            "decision": "EVIDENCE_INSUFFICIENT",
        },
        {
            **common,
            "decision_id": "DECISION-RECOVERY-POLICY-002A",
            "decision_type": "RECOVERY_POLICY",
            "decision": "EVIDENCE_INSUFFICIENT",
        },
        {
            **common,
            "decision_id": "DECISION-COMPONENTS-002A",
            "decision_type": "COMPONENTS",
            "decision": "RETEST_REQUIRED",
            "component_results": [
                {
                    "mechanism_id": mechanism_id,
                    "decision": "RETEST_REQUIRED",
                    "accepted_scope": "NONE",
                    "reason_codes": ["EXECUTABLE_TEST_REQUIRED"],
                    "evidence_refs": [evidence_ref],
                    "required_tests": [test_ref],
                    "maintenance_cost": "MEDIUM",
                }
                for mechanism_id in component_ids
            ],
        },
    ]


def _disable_freeze_git(monkeypatch):
    monkeypatch.setattr(
        "cumcm_skill_lab.adjudication.role_orchestrator.verify_input_freeze", lambda root: []
    )
    monkeypatch.setattr(
        "cumcm_skill_lab.adjudication.phase002b_replay.verify_input_freeze", lambda root: []
    )


def _transport_failure(request, *, adapter, observable, session_id):
    failure = classify_failure(
        observable,
        session_id=session_id,
        adapter=adapter,
    )
    status = (
        TransportStatus.TRANSPORT_FAILED_RESUMABLE
        if failure.resumable
        else TransportStatus.TRANSPORT_FAILED_NONRESUMABLE
    )
    manifest = {
        "bundle_hash": request.input_bundle_hash,
        "policy_hash": request.policy_hash,
        "evidence_hash": request.evidence_hash,
        "output_schema_hash": sha256_json(read_json(request.output_schema_path)),
    }
    checkpoint = _checkpoint(
        request.role_id,
        manifest,
        status=status.value,
        adapter=adapter,
        attempt=request.attempt,
        failure_class=failure.failure_class,
    )
    request.checkpoint_store.write(
        checkpoint,
        session_id=session_id,
        turn_id=None,
    )
    return TransportResult(
        role_id=request.role_id,
        adapter=adapter,
        status=status,
        attempt=request.attempt,
        model=request.model,
        reasoning_setting=request.reasoning_setting,
        duration_seconds=0.01,
        return_code=1,
        session_id=session_id,
        failure=failure,
    )


def _checkpoint(
    role,
    manifest,
    *,
    status,
    adapter,
    attempt=1,
    failure_class=None,
):
    now = datetime.now(UTC).isoformat()
    return {
        "schema_version": "1.0.0",
        "role_id": role,
        "adapter": adapter,
        "attempt": attempt,
        "model": "gpt-5.6-sol",
        "reasoning_setting": "medium",
        "input_bundle_hash": manifest["bundle_hash"],
        "policy_hash": manifest["policy_hash"],
        "evidence_hash": manifest["evidence_hash"],
        "output_schema_hash": manifest["output_schema_hash"],
        "started_at": now,
        "last_event_at": now,
        "completion_status": status,
        "failure_class": failure_class,
        "observable_code": failure_class,
        "raw_event_hash": None,
        "stderr_hash": None,
        "output_hash": None,
        "resume_allowed": status in {"RUNNING", "TRANSPORT_FAILED_RESUMABLE"},
        "supersedes": None,
        "notes": ["offline interruption fixture"],
        "event_summary": {},
        "token_usage": {},
    }


def _complete_six_role_chain(monkeypatch, root):
    _disable_freeze_git(monkeypatch)
    factories = {
        "EXEC_RESUMABLE": SuccessfulRoleAdapter,
        "APP_SERVER_RESUMABLE": SuccessfulAppAdapter,
    }
    orchestrator = RoleOrchestrator(root, adapter_factories=factories)
    for role in ROLE_ORDER[:4]:
        assert orchestrator.execute(role, allow_recovery=True).completion_status == "COMPLETED"
    assert build_all(root, check=False)["status"] == "PASS"
    assert orchestrator.execute(ROLE_ORDER[4], allow_recovery=True).completion_status == "COMPLETED"
    meta = read_json(formal_output_path(root, ROLE_ORDER[4]))
    create_pre_audit_decisions(root, meta)
    assert build_all(root, check=False)["status"] == "PASS"
    assert orchestrator.execute(ROLE_ORDER[5], allow_recovery=True).completion_status == "COMPLETED"
    return build_replay(root)
