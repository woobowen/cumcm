"""Run and record the complete offline Phase 002D-R2 validation matrix."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import read_json, sha256_bytes, sha256_json, write_json

from .models import CREATED_AT, RESULT_ROOT

VALIDATION_PATH = RESULT_ROOT / "validation_commands.json"
VALIDATION_COMMANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("RUFF_CHECK", (".venv/bin/python", "-m", "ruff", "check", ".")),
    ("RUFF_FORMAT", (".venv/bin/python", "-m", "ruff", "format", "--check", ".")),
    ("PYTEST", (".venv/bin/python", "-m", "pytest", "-q")),
    ("INSTRUCTION_BUDGET", (".venv/bin/python", "scripts/check_instruction_budget.py")),
    (
        "SKILL_DISCOVERY",
        (
            ".venv/bin/python",
            "scripts/check_skill_discovery.py",
            "--expected-name",
            "cumcm-modeling-evidence",
            "--expected-count",
            "1",
        ),
    ),
    ("CONTRACTS", (".venv/bin/python", "scripts/check_contracts.py")),
    ("UPSTREAM_MANIFEST", (".venv/bin/python", "scripts/check_upstream_manifest.py")),
    ("ANSWER_LEAKAGE", (".venv/bin/python", "scripts/check_answer_leakage.py")),
    ("SECRETS", (".venv/bin/python", "scripts/check_secrets.py")),
    (
        "PHASE002_FREEZE",
        (".venv/bin/python", "scripts/freeze_phase002d_inputs.py", "--check"),
    ),
    (
        "PHASE002D_R1_FREEZE",
        (".venv/bin/python", "scripts/freeze_phase002d_r1_inputs.py", "--check"),
    ),
    (
        "PHASE002D_R2_FREEZE",
        (".venv/bin/python", "scripts/freeze_phase002d_r2_inputs.py", "--check"),
    ),
    (
        "COMPONENT_SPECS",
        (".venv/bin/python", "scripts/validate_component_specifications.py", "--check"),
    ),
    (
        "INTERACTION_CONTRACT",
        (".venv/bin/python", "scripts/validate_component_interactions.py", "--check"),
    ),
    (
        "ARCHITECTURE_CANDIDATES",
        (".venv/bin/python", "scripts/validate_architecture_candidates.py", "--check"),
    ),
    (
        "BENCHMARK_GENERATOR",
        (".venv/bin/python", "scripts/generate_prospective_benchmark.py", "--check"),
    ),
    (
        "BENCHMARK_VAULT",
        (".venv/bin/python", "scripts/check_benchmark_vault.py", "--check"),
    ),
    (
        "BENCHMARK_FREEZE",
        (".venv/bin/python", "scripts/freeze_prospective_benchmark.py", "--check"),
    ),
    (
        "THRESHOLD_FREEZE",
        (".venv/bin/python", "scripts/freeze_prospective_thresholds.py", "--check"),
    ),
    (
        "PROSPECTIVE_PROTOCOL",
        (".venv/bin/python", "scripts/validate_prospective_protocol.py", "--check"),
    ),
    (
        "CLEAN_ROOM_PROVENANCE",
        (".venv/bin/python", "scripts/validate_clean_room_provenance.py", "--check"),
    ),
    (
        "FINDING_CLOSURE",
        (".venv/bin/python", "scripts/synthesize_phase002d_r2_findings.py", "--check"),
    ),
    (
        "IMPLEMENTATION_EMBARGO",
        (".venv/bin/python", "scripts/check_implementation_embargo.py", "--check"),
    ),
    (
        "R2_ADJUDICATION",
        (".venv/bin/python", "scripts/adjudicate_phase002d_r2.py", "--check"),
    ),
    (
        "R2_DECISION_AUDIT",
        (".venv/bin/python", "scripts/audit_phase002d_r2_decision.py", "--check"),
    ),
    (
        "R2_REPLAY",
        (".venv/bin/python", "scripts/replay_phase002d_r2_decision.py", "--check"),
    ),
    (
        "R2_STATE",
        (".venv/bin/python", "scripts/transition_phase002d_r2_state.py", "--check"),
    ),
    (
        "R2_REPORTS",
        (".venv/bin/python", "scripts/summarize_phase002d_r2.py", "--check"),
    ),
    ("STATUS_RENDER", (".venv/bin/python", "scripts/render_status.py")),
    ("STATUS_CHECK", (".venv/bin/python", "scripts/render_status.py", "--check")),
    ("STRICT_REPOSITORY", (".venv/bin/python", "scripts/validate_repo.py", "--strict")),
    ("OFFLINE_CI", ("bash", "scripts/ci.sh")),
    ("GIT_DIFF_CHECK", ("git", "diff", "--check")),
    ("GIT_STATUS", ("git", "status", "--short", "--branch")),
)


def _command_text(argv: tuple[str, ...]) -> str:
    return shlex.join(argv)


def run_validation(root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    environment = dict(os.environ)
    environment["PYTHONHASHSEED"] = "0"
    for command_id, argv in VALIDATION_COMMANDS:
        started = time.monotonic()
        result = subprocess.run(
            argv,
            cwd=root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        duration = round(time.monotonic() - started, 6)
        combined = (result.stdout + result.stderr).encode("utf-8")
        records.append(
            {
                "id": command_id,
                "command": _command_text(argv),
                "exit_code": result.returncode,
                "duration_seconds": duration,
                "execution_type": "DETERMINISTIC_OFFLINE",
                "result": "PASS" if result.returncode == 0 else "FAIL",
                "evidence_hash": sha256_bytes(combined),
                "blocker": None if result.returncode == 0 else f"EXIT_{result.returncode}",
                "model_or_reasoning_visibility": "NONE",
                "stdout_tail": result.stdout[-2000:],
                "stderr_tail": result.stderr[-2000:],
            }
        )
        print(f"[{records[-1]['result']}] {command_id}: {records[-1]['command']}")
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "ledger_id": "PHASE-002D-R2-FINAL-VALIDATION-001",
        "created_at": CREATED_AT,
        "commands": records,
        "command_count": len(records),
        "passed_count": sum(item["result"] == "PASS" for item in records),
        "failed_count": sum(item["result"] == "FAIL" for item in records),
        "real_batch_codex_runs": 0,
        "api_calls": 0,
        "prototype_executions": 0,
        "third_party_executions": 0,
        "status": "PASS" if all(item["result"] == "PASS" for item in records) else "FAIL",
    }
    value = {**body, "ledger_hash": sha256_json(body)}
    write_json(root / VALIDATION_PATH, value)
    return value


def validate_validation_ledger(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    body = dict(value)
    ledger_hash = body.pop("ledger_hash", None)
    if sha256_json(body) != ledger_hash:
        errors.append("PHASE002D_R2_VALIDATION_LEDGER_HASH_MISMATCH")
    expected_commands = [_command_text(argv) for _, argv in VALIDATION_COMMANDS]
    recorded_commands = [item.get("command") for item in value.get("commands", [])]
    if recorded_commands != expected_commands:
        errors.append("PHASE002D_R2_VALIDATION_COMMAND_SET_MISMATCH")
    if value.get("status") != "PASS" or value.get("failed_count") != 0:
        errors.append("PHASE002D_R2_VALIDATION_FAILURE_RECORDED")
    if any(
        value.get(field) != 0
        for field in (
            "real_batch_codex_runs",
            "api_calls",
            "prototype_executions",
            "third_party_executions",
        )
    ):
        errors.append("PHASE002D_R2_VALIDATION_EXECUTION_BOUNDARY_VIOLATION")
    return errors


def check_validation(root: Path) -> dict[str, Any]:
    if not (root / VALIDATION_PATH).is_file():
        return {"status": "FAIL", "errors": ["PHASE002D_R2_VALIDATION_LEDGER_MISSING"]}
    value = read_json(root / VALIDATION_PATH)
    errors = validate_validation_ledger(value)
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "command_count": value.get("command_count"),
        "passed_count": value.get("passed_count"),
        "ledger_hash": value.get("ledger_hash"),
    }


__all__ = [
    "VALIDATION_COMMANDS",
    "VALIDATION_PATH",
    "check_validation",
    "run_validation",
    "validate_validation_ledger",
]
