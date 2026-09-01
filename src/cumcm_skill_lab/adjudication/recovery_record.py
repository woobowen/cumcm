"""Sanitized terminal records for an incomplete Phase 002B recovery chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .bundles.role_views import ROLE_ORDER, ROLE_SLUGS
from .models import file_sha256, read_json, sha256_json, write_json
from .transport.event_sanitization import summarize_events
from .transport.runtime_budget import PHASE002B_MAXIMUM_STARTS, PREVIOUS_MODEL_STARTS

RESULT_ROOT = Path("evals/results/phase-002b")


def write_incomplete_recovery(root: Path) -> dict[str, Any]:
    budget = read_json(root / RESULT_ROOT / "transport_diagnostics/run_budget.json")
    diagnostics: list[dict[str, Any]] = []
    for start in budget["starts"]:
        role = start["role_id"]
        slug = ROLE_SLUGS[role]
        attempt = start["attempt"]
        raw_path = root / ".cache/adjudication-002b/raw-events" / f"{slug}-attempt-{attempt}.jsonl"
        stderr_path = raw_path.with_suffix(".stderr")
        summary = summarize_events(raw_path)
        if summary["raw_event_hash"] is None:
            raise ValueError(f"RAW_EVENT_MISSING:{role}:{attempt}")
        record = {
            "schema_version": "1.0.0",
            "diagnostic_id": f"PHASE-002B-{slug.upper()}-ATTEMPT-{attempt:03d}",
            "role_id": role,
            "adapter": start["adapter"],
            "start_kind": start["start_kind"],
            "attempt": attempt,
            "model": "gpt-5.6-sol",
            "reasoning_setting": "medium",
            "started_at": start["started_at"],
            "completed_at": start["completed_at"],
            "duration_seconds": start["duration_seconds"],
            "completion_status": start["completion_status"],
            "failure_class": start["failure_class"],
            "observable_code": "RESPONSES_CONNECTION_RESET",
            "raw_event_hash": summary["raw_event_hash"],
            "stderr_hash": file_sha256(stderr_path) if stderr_path.is_file() else None,
            "session_id_hash": summary["session_id_hash"],
            "turn_id_hash": summary["turn_id_hash"],
            "event_summary": {
                key: value
                for key, value in summary.items()
                if key
                not in {
                    "session_id",
                    "turn_id",
                    "raw_event_hash",
                    "token_usage",
                }
            },
            "token_usage": summary["token_usage"],
            "resume_allowed": attempt < 2 and bool(summary["session_id_hash"]),
            "next_adapter": "EXEC_RESUMABLE" if attempt == 1 else "NONE",
            "terminal": attempt >= 2,
            "user_action_required": attempt >= 2,
            "raw_content_tracked": False,
            "hidden_reasoning_tracked": False,
            "credentials_tracked": False,
        }
        record["content_hash"] = sha256_json(record)
        path = root / RESULT_ROOT / "transport_diagnostics" / f"{slug}_attempt_{attempt:03d}.json"
        write_json(path, record)
        diagnostics.append(record)
    ledger = read_json(root / RESULT_ROOT / "role_ledger.json")
    freeze = read_json(root / RESULT_ROOT / "input_freeze_manifest.json")
    diagnostic_paths = sorted(
        (root / RESULT_ROOT / "transport_diagnostics").glob("correctness_attempt_*.json")
    )
    manifest = {
        "schema_version": "1.0.0",
        "recovery_id": "PHASE-AUTOMATED-ADJUDICATION-RECOVERY-002B",
        "status": "AUTOMATED_ADJUDICATION_INCOMPLETE",
        "input_freeze_hash": freeze["freeze_hash"],
        "evidence_hash": freeze["evidence_hash"],
        "policy_hash": freeze["policy_hash"],
        "model": "gpt-5.6-sol",
        "reasoning_setting": "medium",
        "previous_model_starts": PREVIOUS_MODEL_STARTS,
        "phase002b_maximum_starts": PHASE002B_MAXIMUM_STARTS,
        "phase002b_model_starts": len(budget["starts"]),
        "phase002b_remaining_budget": PHASE002B_MAXIMUM_STARTS - len(budget["starts"]),
        "completed_roles": [],
        "failed_roles": ["CORRECTNESS_JUDGE"],
        "pending_roles": list(ROLE_ORDER[1:]),
        "terminal_failure_class": diagnostics[-1]["failure_class"],
        "terminal_reason": "PER_ROLE_TWO_ATTEMPT_LIMIT_REACHED",
        "meta_adjudication": "NOT_RUN",
        "decision_audit": "NOT_RUN",
        "deterministic_replay": "NOT_RUN",
        "automated_decision_ids": [],
        "next_phase_allowed": None,
        "role_statuses": {item["role_id"]: item["status"] for item in ledger["roles"]},
        "diagnostics": {
            str(path.relative_to(root)): file_sha256(path) for path in diagnostic_paths
        },
        "previous_failure_hashes": freeze["previous_failed_attempt_hashes"],
        "api_key_used": False,
        "api_billing_used": False,
        "authentication": "CHATGPT_MANAGED_CODEX_LOGIN",
        "phase002_rerun": False,
        "third_party_integrated": False,
        "base_selected": False,
        "skill_capability_status": "SCAFFOLD_ONLY",
    }
    manifest["content_hash"] = sha256_json(manifest)
    write_json(root / RESULT_ROOT / "recovery_manifest.json", manifest)
    return manifest


def check_incomplete_recovery(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / RESULT_ROOT / "recovery_manifest.json"
    if not manifest_path.is_file():
        return ["RECOVERY_MANIFEST_MISSING"]
    manifest = read_json(manifest_path)
    body = dict(manifest)
    recorded_hash = body.pop("content_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("RECOVERY_MANIFEST_HASH_MISMATCH")
    budget = read_json(root / RESULT_ROOT / "transport_diagnostics/run_budget.json")
    if manifest.get("phase002b_model_starts") != len(budget["starts"]):
        errors.append("RECOVERY_BUDGET_MISMATCH")
    if manifest.get("phase002b_remaining_budget") != 8 - len(budget["starts"]):
        errors.append("RECOVERY_REMAINING_BUDGET_MISMATCH")
    for relative, expected_hash in manifest.get("diagnostics", {}).items():
        path = root / relative
        if not path.is_file():
            errors.append(f"RECOVERY_DIAGNOSTIC_MISSING:{relative}")
            continue
        if file_sha256(path) != expected_hash:
            errors.append(f"RECOVERY_DIAGNOSTIC_HASH_MISMATCH:{relative}")
        record = read_json(path)
        record_body = dict(record)
        record_hash = record_body.pop("content_hash", None)
        if sha256_json(record_body) != record_hash:
            errors.append(f"RECOVERY_DIAGNOSTIC_CONTENT_HASH_MISMATCH:{relative}")
        if record.get("raw_content_tracked") is not False:
            errors.append(f"RAW_CONTENT_TRACKING_INVALID:{relative}")
    if manifest.get("status") != "AUTOMATED_ADJUDICATION_INCOMPLETE":
        errors.append("RECOVERY_STATUS_INVALID")
    if manifest.get("next_phase_allowed") is not None:
        errors.append("RECOVERY_PHASE003_INVALID")
    return errors
