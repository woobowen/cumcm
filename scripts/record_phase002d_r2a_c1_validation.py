#!/usr/bin/env python3
"""Run and record the final offline C1/C2 acceptance validation matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from typing import Any

from _bootstrap import ROOT

from cumcm_skill_lab.authorization_c1.models import check_or_write_json, sha256_json
from cumcm_skill_lab.authorization_c2.reporting import VALIDATION_PATH

REMOTE_CI = {
    "status": "PASS",
    "subject_commit": "6916ebfaa37021d6b54854bff28d0a6966c3daeb",
    "run_id": 33738775293,
    "url": "https://github.com/woobowen/cumcm/actions/runs/33738775293",
}
COMMANDS = (
    (".venv/bin/python", "-m", "ruff", "check", "."),
    (".venv/bin/python", "-m", "ruff", "format", "--check", "."),
    (".venv/bin/python", "-m", "pytest", "-q"),
    (".venv/bin/python", "scripts/check_instruction_budget.py"),
    (
        ".venv/bin/python",
        "scripts/check_skill_discovery.py",
        "--expected-name",
        "cumcm-modeling-evidence",
        "--expected-count",
        "1",
    ),
    (".venv/bin/python", "scripts/check_contracts.py"),
    (".venv/bin/python", "scripts/check_upstream_manifest.py"),
    (".venv/bin/python", "scripts/check_answer_leakage.py"),
    (".venv/bin/python", "scripts/check_secrets.py"),
    (".venv/bin/python", "scripts/freeze_phase002d_r2_inputs.py", "--check"),
    (".venv/bin/python", "scripts/freeze_phase002d_r2a_inputs.py", "--check"),
    (".venv/bin/python", "scripts/freeze_phase002d_r2a_c1_inputs.py", "--check"),
    (
        ".venv/bin/python",
        "scripts/check_historical_freeze_compatibility.py",
        "--check",
    ),
    (
        ".venv/bin/python",
        "scripts/check_project_state_schema_compatibility.py",
        "--check",
    ),
    (".venv/bin/python", "scripts/build_shadow_authorization_dependencies.py", "--check"),
    (".venv/bin/python", "scripts/resolve_c1_final_audit_dependency.py", "--check"),
    (".venv/bin/python", "scripts/check_shadow_authorization_preconditions.py", "--check"),
    (".venv/bin/python", "scripts/validate_shadow_prototype_scope.py", "--check"),
    (".venv/bin/python", "scripts/freeze_shadow_authorization_candidate.py", "--check"),
    (
        ".venv/bin/python",
        "scripts/build_candidate_bound_authorization_evidence.py",
        "--check",
    ),
    (".venv/bin/python", "scripts/audit_shadow_authorization.py", "--check"),
    (".venv/bin/python", "scripts/freeze_shadow_authorization_candidate_c2.py", "--check"),
    (
        ".venv/bin/python",
        "scripts/build_candidate_bound_authorization_evidence_c2.py",
        "--check",
    ),
    (
        ".venv/bin/python",
        "scripts/prepare_final_shadow_authorization_audit_c2.py",
        "--check",
    ),
    (".venv/bin/python", "scripts/audit_shadow_authorization_c2.py", "--check"),
    (".venv/bin/python", "scripts/seal_shadow_authorization.py", "--check"),
    (".venv/bin/python", "scripts/replay_shadow_authorization.py", "--check"),
    (".venv/bin/python", "scripts/transition_phase002d_r2a_state.py", "--check"),
    (".venv/bin/python", "scripts/summarize_phase002d_r2a_c1.py", "--check"),
    (".venv/bin/python", "scripts/check_implementation_embargo.py", "--check"),
    (".venv/bin/python", "scripts/check_benchmark_vault.py", "--check"),
    (".venv/bin/python", "scripts/render_status.py"),
    (".venv/bin/python", "scripts/render_status.py", "--check"),
    (".venv/bin/python", "scripts/validate_repo.py", "--strict"),
    ("bash", "scripts/ci.sh"),
    ("git", "diff", "--check"),
)


def _display(argv: tuple[str, ...]) -> str:
    return " ".join(argv)


def _run(argv: tuple[str, ...]) -> tuple[dict[str, Any], str]:
    started = time.monotonic()
    completed = subprocess.run(argv, cwd=ROOT, check=False, capture_output=True, text=True)
    duration = time.monotonic() - started
    output = completed.stdout + completed.stderr
    result = {
        "command": _display(argv),
        "exit_code": completed.returncode,
        "duration_seconds": round(duration, 3),
        "execution_type": "OFFLINE_LOCAL_DETERMINISTIC",
        "result": "PASS" if completed.returncode == 0 else "FAIL",
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "blocker": None if completed.returncode == 0 else output[-2000:],
    }
    return result, output


def _pytest_counts(output: str) -> dict[str, int | None]:
    match = re.search(r"(?P<passed>\d+) passed(?:, (?P<skipped>\d+) skipped)?", output)
    if match is None:
        return {"collected": None, "passed": None, "failed": None, "skipped": None}
    passed = int(match.group("passed"))
    skipped = int(match.group("skipped") or 0)
    return {"collected": passed + skipped, "passed": passed, "failed": 0, "skipped": skipped}


def _contract_counts(output: str) -> dict[str, int | None]:
    for line in reversed(output.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        contracts = value.get("sections", {}).get("contracts", {})
        if contracts:
            return {
                "schemas": contracts.get("schema_count"),
                "valid": contracts.get("valid_fixtures"),
                "invalid_rejected": contracts.get("invalid_rejected"),
            }
    return {"schemas": None, "valid": None, "invalid_rejected": None}


def build_validation_record() -> dict[str, Any]:
    commands: list[dict[str, Any]] = []
    outputs: dict[str, str] = {}
    for argv in COMMANDS:
        result, output = _run(argv)
        commands.append(result)
        outputs[result["command"]] = output
        print(
            json.dumps(
                {
                    "command": result["command"],
                    "exit_code": result["exit_code"],
                    "duration_seconds": result["duration_seconds"],
                    "result": result["result"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
    pytest_command = ".venv/bin/python -m pytest -q"
    strict_command = ".venv/bin/python scripts/validate_repo.py --strict"
    overall = all(item["result"] == "PASS" for item in commands)
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "validation_id": "PHASE-002D-R2A-C1-C2-FINAL-ACCEPTANCE-VALIDATION-001",
        "subject_commit": "6916ebfaa37021d6b54854bff28d0a6966c3daeb",
        "execution_mode": "OFFLINE_LOCAL_DETERMINISTIC_PLUS_REMOTE_CI_RECEIPT",
        "commands": commands,
        "pytest": _pytest_counts(outputs[pytest_command]),
        "contract_fixtures": _contract_counts(outputs[strict_command]),
        "remote_ci": REMOTE_CI,
        "overall_status": "PASS" if overall and REMOTE_CI["status"] == "PASS" else "FAIL",
    }
    body["record_hash"] = sha256_json(body)
    return body


def validate_record(value: dict[str, Any]) -> list[str]:
    body = dict(value)
    recorded = body.pop("record_hash", None)
    errors = []
    expected_commands = [_display(argv) for argv in COMMANDS]
    actual_commands = [item.get("command") for item in value.get("commands", [])]
    if sha256_json(body) != recorded:
        errors.append("C2_VALIDATION_RECORD_HASH_MISMATCH")
    if actual_commands != expected_commands:
        errors.append("C2_VALIDATION_COMMAND_MATRIX_MISMATCH")
    if value.get("overall_status") != "PASS":
        errors.append("C2_VALIDATION_NOT_PASS")
    if any(item.get("result") != "PASS" for item in value.get("commands", [])):
        errors.append("C2_VALIDATION_COMMAND_FAILED")
    if value.get("remote_ci", {}).get("status") != "PASS":
        errors.append("C2_VALIDATION_REMOTE_CI_NOT_PASS")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the frozen record only")
    args = parser.parse_args()
    path = ROOT / VALIDATION_PATH
    if args.check:
        if not path.is_file():
            print(json.dumps({"status": "FAIL", "errors": ["C2_VALIDATION_RECORD_MISSING"]}))
            return 1
        value = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_record(value)
    else:
        value = build_validation_record()
        errors = validate_record(value)
        if not errors:
            errors.extend(check_or_write_json(path, value, check=False))
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "errors": errors,
                "record_hash": value.get("record_hash"),
                "command_count": len(value.get("commands", [])),
                "pytest": value.get("pytest"),
                "remote_ci": value.get("remote_ci"),
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
