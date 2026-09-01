"""Strict serial orchestration for the six external Phase 002B roles."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .bundles.role_views import ROLE_ORDER, ROLE_SLUGS
from .formal_outputs import formal_output_path, is_formal_output_valid, promote_output
from .models import file_sha256, read_json, read_yaml, sha256_json
from .recovery_freeze import verify_manifest as verify_input_freeze
from .transport import AppServerAdapter, ExecAdapter, RoleRunRequest, TransportResult
from .transport.adapter_selection import select_initial, select_recovery
from .transport.base import TransportAdapter, TransportStatus
from .transport.checkpoints import CheckpointStore, _atomic_json_write
from .transport.exec_adapter import safe_codex_environment
from .transport.runtime_budget import RunBudget

AdapterFactory = Callable[[], TransportAdapter]


@dataclass(frozen=True)
class RoleExecutionOutcome:
    role_id: str
    completion_status: str
    attempts: int
    adapter: str | None
    output_path: str | None
    output_hash: str | None
    skipped_completed: bool
    failure_class: str | None


class RoleOrchestrator:
    def __init__(
        self,
        root: Path,
        *,
        config_path: str = "adjudication/configs/phase-002b-v2.yaml",
        adapter_factories: dict[str, AdapterFactory] | None = None,
        budget: RunBudget | None = None,
    ) -> None:
        self.root = root
        self.config_path = config_path
        self.config = read_yaml(root / config_path)
        self.checkpoints = CheckpointStore(root)
        self.budget = budget or RunBudget(root)
        self.adapter_factories = adapter_factories or {
            "EXEC_RESUMABLE": ExecAdapter,
            "APP_SERVER_RESUMABLE": AppServerAdapter,
        }

    def execute(self, role: str, *, allow_recovery: bool) -> RoleExecutionOutcome:
        self._assert_preconditions(role)
        if self._completed_role_valid(role):
            output_path = formal_output_path(self.root, role)
            checkpoint = self.checkpoints.load_checkpoint(role) or {}
            return RoleExecutionOutcome(
                role_id=role,
                completion_status="COMPLETED",
                attempts=checkpoint.get("attempt", 1),
                adapter=checkpoint.get("adapter"),
                output_path=str(output_path.relative_to(self.root)),
                output_hash=file_sha256(output_path),
                skipped_completed=True,
                failure_class=None,
            )
        manifest = self._manifest(role)
        workspace = prepare_role_workspace(self.root, role, manifest)
        previous_checkpoint = self.checkpoints.load_checkpoint(role)
        previous_adapter = previous_checkpoint.get("adapter") if previous_checkpoint else None
        attempts_used = sum(
            item["role_id"] == role for item in self.budget.load().get("starts", [])
        )
        if previous_checkpoint and previous_checkpoint.get("completion_status") != "COMPLETED":
            exact = self.checkpoints.load_exact_session(role)
            action = select_recovery(
                status=TransportStatus(previous_checkpoint["completion_status"]),
                exact_session_available=bool(exact and exact.get("session_id")),
                attempts_used=attempts_used,
                previous_adapter=previous_adapter,
            )
        elif attempts_used:
            action = select_recovery(
                status=TransportStatus.TRANSPORT_FAILED_NONRESUMABLE,
                exact_session_available=False,
                attempts_used=attempts_used,
                previous_adapter=previous_adapter,
            )
        else:
            action = select_initial()
        if action.action in {"STOP", "EXHAUSTED"}:
            self._write_role_ledger()
            return RoleExecutionOutcome(
                role_id=role,
                completion_status=(
                    TransportStatus.EXHAUSTED.value
                    if action.action == "EXHAUSTED"
                    else (previous_checkpoint or {}).get(
                        "completion_status", TransportStatus.POLICY_FAILED.value
                    )
                ),
                attempts=attempts_used,
                adapter=previous_adapter,
                output_path=None,
                output_hash=None,
                skipped_completed=False,
                failure_class=(previous_checkpoint or {}).get("failure_class"),
            )
        result = self._execute_action(role, action.adapter, action.action, manifest, workspace)
        if result.status == TransportStatus.COMPLETED:
            formal = promote_output(
                self.root,
                role=role,
                raw_output=result.output or {},
                manifest=manifest,
                checkpoint_path=self.checkpoints.tracked_path(role),
            )
            self._write_role_ledger()
            self._assert_unique_sessions()
            return RoleExecutionOutcome(
                role_id=role,
                completion_status="COMPLETED",
                attempts=result.attempt,
                adapter=result.adapter,
                output_path=_formal_relative(role),
                output_hash=sha256_json(formal),
                skipped_completed=False,
                failure_class=None,
            )
        if allow_recovery and result.attempt < 2:
            exact = self.checkpoints.load_exact_session(role)
            recovery = select_recovery(
                status=result.status,
                exact_session_available=bool(exact and exact.get("session_id")),
                attempts_used=result.attempt,
                previous_adapter=result.adapter,
            )
            if recovery.action not in {"STOP", "EXHAUSTED"}:
                recovered = self._execute_action(
                    role, recovery.adapter, recovery.action, manifest, workspace
                )
                if recovered.status == TransportStatus.COMPLETED:
                    formal = promote_output(
                        self.root,
                        role=role,
                        raw_output=recovered.output or {},
                        manifest=manifest,
                        checkpoint_path=self.checkpoints.tracked_path(role),
                    )
                    self._write_role_ledger()
                    self._assert_unique_sessions()
                    return RoleExecutionOutcome(
                        role_id=role,
                        completion_status="COMPLETED",
                        attempts=recovered.attempt,
                        adapter=recovered.adapter,
                        output_path=_formal_relative(role),
                        output_hash=sha256_json(formal),
                        skipped_completed=False,
                        failure_class=None,
                    )
                result = recovered
        self._write_role_ledger()
        return RoleExecutionOutcome(
            role_id=role,
            completion_status=result.status.value,
            attempts=result.attempt,
            adapter=result.adapter,
            output_path=None,
            output_hash=None,
            skipped_completed=False,
            failure_class=result.failure.failure_class if result.failure else None,
        )

    def _execute_action(
        self,
        role: str,
        adapter_name: str,
        action: str,
        manifest: dict,
        workspace: Path,
    ) -> TransportResult:
        if adapter_name not in self.adapter_factories:
            raise RuntimeError(f"ADAPTER_UNAVAILABLE:{adapter_name}")
        role_starts = sum(item["role_id"] == role for item in self.budget.load().get("starts", []))
        start_kind = (
            "RESUME" if action == "RESUME" else ("INITIAL" if role_starts == 0 else "FALLBACK")
        )
        budget_record = self.budget.record_start(role, adapter_name, start_kind)
        attempt = budget_record["attempt"]
        slug = ROLE_SLUGS[role]
        request = RoleRunRequest(
            role_id=role,
            workspace=workspace,
            prompt=role_prompt(role),
            output_schema_path=workspace / "output_schema.json",
            output_path=workspace / ".harness" / f"last-message-{attempt}.json",
            raw_event_path=(
                self.root
                / ".cache/adjudication-002b/raw-events"
                / f"{slug}-attempt-{attempt}.jsonl"
            ),
            checkpoint_store=self.checkpoints,
            model=self.config["model"],
            reasoning_setting=self.config["reasoning_setting"],
            input_bundle_hash=manifest["bundle_hash"],
            policy_hash=manifest["policy_hash"],
            evidence_hash=manifest["evidence_hash"],
            attempt=attempt,
            timeout_seconds=self.config["timeout_seconds"],
            supersedes=(self.checkpoints.load_checkpoint(role) or {}).get("output_hash"),
        )
        adapter = self.adapter_factories[adapter_name]()
        result = adapter.resume_role(request) if action == "RESUME" else adapter.start_role(request)
        self.budget.record_result(
            role,
            attempt,
            result.status.value,
            duration_seconds=result.duration_seconds,
            token_usage=result.token_usage,
            failure_class=result.failure.failure_class if result.failure else None,
        )
        return result

    def _assert_preconditions(self, role: str) -> None:
        if role not in ROLE_ORDER:
            raise ValueError(f"UNSUPPORTED_ROLE:{role}")
        errors = verify_input_freeze(self.root)
        if errors:
            raise RuntimeError("INPUT_FREEZE_BROKEN:" + ",".join(errors))
        index = ROLE_ORDER.index(role)
        required = ROLE_ORDER[:index]
        if role in ROLE_ORDER[:4]:
            required = ROLE_ORDER[:index]
        for prior in required:
            if not self._completed_role_valid(prior):
                raise RuntimeError(f"ROLE_PRECONDITION_MISSING:{prior}")
        manifest = self._manifest(role)
        if role in ROLE_ORDER[4:] and not manifest["dependencies_ready"]:
            raise RuntimeError(f"ROLE_DEPENDENCIES_PENDING:{role}")
        if manifest["model"] != self.config["model"]:
            raise RuntimeError("MODEL_COMPARABILITY_BROKEN")
        if manifest["reasoning_setting"] != self.config["reasoning_setting"]:
            raise RuntimeError("MODEL_COMPARABILITY_BROKEN")

    def _completed_role_valid(self, role: str) -> bool:
        checkpoint = self.checkpoints.load_checkpoint(role)
        if not checkpoint or checkpoint.get("completion_status") != "COMPLETED":
            return False
        manifest = self._manifest(role)
        expected = {
            "model": manifest["model"],
            "reasoning_setting": manifest["reasoning_setting"],
            "input_bundle_hash": manifest["bundle_hash"],
            "policy_hash": manifest["policy_hash"],
            "evidence_hash": manifest["evidence_hash"],
            "output_schema_hash": manifest["output_schema_hash"],
        }
        if any(checkpoint.get(key) != value for key, value in expected.items()):
            return False
        return is_formal_output_valid(self.root, role)

    def _manifest(self, role: str) -> dict:
        return read_json(
            self.root / "evals/results/phase-002b/bundle_manifests" / f"{ROLE_SLUGS[role]}.json"
        )

    def _assert_unique_sessions(self) -> None:
        seen: set[str] = set()
        for role in ROLE_ORDER:
            checkpoint = self.checkpoints.load_checkpoint(role)
            if not checkpoint or checkpoint.get("completion_status") != "COMPLETED":
                continue
            session_hash = checkpoint.get("thread_id")
            if not session_hash:
                raise RuntimeError(f"SESSION_ID_MISSING:{role}")
            if session_hash in seen:
                raise RuntimeError("ROLE_INDEPENDENCE_BROKEN:SHARED_THREAD")
            seen.add(session_hash)

    def _write_role_ledger(self) -> None:
        records: list[dict] = []
        for role in ROLE_ORDER:
            checkpoint = self.checkpoints.load_checkpoint(role)
            output_path = formal_output_path(self.root, role)
            records.append(
                {
                    "role_id": role,
                    "status": (checkpoint.get("completion_status") if checkpoint else "PENDING"),
                    "adapter": checkpoint.get("adapter") if checkpoint else None,
                    "attempt": checkpoint.get("attempt") if checkpoint else 0,
                    "thread_id_hash": checkpoint.get("thread_id") if checkpoint else None,
                    "turn_id_hash": checkpoint.get("turn_id") if checkpoint else None,
                    "model": checkpoint.get("model") if checkpoint else self.config["model"],
                    "reasoning_setting": (
                        checkpoint.get("reasoning_setting")
                        if checkpoint
                        else self.config["reasoning_setting"]
                    ),
                    "output_path": (
                        str(output_path.relative_to(self.root)) if output_path.is_file() else None
                    ),
                    "output_hash": file_sha256(output_path) if output_path.is_file() else None,
                    "schema_valid": is_formal_output_valid(self.root, role),
                }
            )
        _atomic_json_write(
            self.root / "evals/results/phase-002b/role_ledger.json",
            {"schema_version": "1.0.0", "roles": records},
        )


def prepare_role_workspace(root: Path, role: str, manifest: dict) -> Path:
    slug = ROLE_SLUGS[role]
    source = root / ".cache/adjudication-002b/bundles" / slug
    if not source.is_dir():
        raise RuntimeError(f"BUNDLE_CACHE_MISSING:{role}")
    workspace = (
        root / ".cache/adjudication-002b/workspaces" / f"{slug}-{manifest['bundle_hash'][:12]}"
    )
    workspace.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob("*.json")):
        target = workspace / path.name
        if target.is_file() and file_sha256(target) != file_sha256(path):
            raise RuntimeError(f"STALE_WORKSPACE_FILE:{role}:{path.name}")
        if not target.is_file():
            shutil.copy2(path, target)
    (workspace / ".harness").mkdir(exist_ok=True)
    if not (workspace / ".git").is_dir():
        subprocess.run(
            ["git", "init", "-q"],
            cwd=workspace,
            env=safe_codex_environment(),
            check=True,
        )
        subprocess.run(
            ["git", "add", *sorted(path.name for path in source.glob("*.json"))],
            cwd=workspace,
            env=safe_codex_environment(),
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=adjudication-harness",
                "-c",
                "user.email=none@invalid",
                "commit",
                "-qm",
                "frozen role evidence bundle",
            ],
            cwd=workspace,
            env=safe_codex_environment(),
            check=True,
        )
    remotes = subprocess.run(
        ["git", "remote"],
        cwd=workspace,
        env=safe_codex_environment(),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if remotes:
        raise RuntimeError(f"ROLE_WORKSPACE_REMOTE_PRESENT:{role}")
    return workspace


def role_prompt(role: str) -> str:
    return (
        f"You are the independent formal {role}. Work only in this isolated local repository. "
        "Read role_task.json, bundle_index.json, evidence_catalog.json and every mandatory file. "
        "Use no network, MCP, peer context, majority vote or human technical Gate. Candidate "
        "identity is unavailable and must not be guessed. Recovery evidence is gap-only and "
        "structured coverage is not correctness. The frozen hierarchy defines E3 through E0; "
        "do not invent undefined E4/E5 evidence. Cite only exact catalog identifiers. Do not "
        "expose hidden reasoning. Return JSON only and satisfy output_schema.json exactly."
    )


def validate_role_ledger(root: Path, *, require_complete: bool) -> list[str]:
    path = root / "evals/results/phase-002b/role_ledger.json"
    if not path.is_file():
        return ["ROLE_LEDGER_MISSING"]
    ledger = read_json(path)
    errors: list[str] = []
    roles = ledger.get("roles", [])
    if [item.get("role_id") for item in roles] != list(ROLE_ORDER):
        errors.append("ROLE_LEDGER_ORDER_INVALID")
    completed_threads: list[str] = []
    for record in roles:
        if require_complete and record.get("status") != "COMPLETED":
            errors.append(f"ROLE_INCOMPLETE:{record.get('role_id')}")
        if record.get("status") == "COMPLETED":
            if not record.get("schema_valid"):
                errors.append(f"ROLE_SCHEMA_INVALID:{record.get('role_id')}")
            if not record.get("thread_id_hash"):
                errors.append(f"ROLE_THREAD_MISSING:{record.get('role_id')}")
            else:
                completed_threads.append(record["thread_id_hash"])
    if len(completed_threads) != len(set(completed_threads)):
        errors.append("ROLE_INDEPENDENCE_BROKEN:SHARED_THREAD")
    return errors


def _formal_relative(role: str) -> str:
    return str(Path(formal_output_path(Path("."), role)))
