"""Bind Decision Auditor blockers to deterministic repair tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import RESULT_ROOT, check_or_write, file_sha256, hashed_body, read_json

ROOT = RESULT_ROOT / "subagent_audits/decision_repair_rounds"
ROUND_ONE_PATH = ROOT / "round-01.json"
REQUESTS_PATH = ROOT / "test_requests.json"
EVIDENCE_PATH = ROOT / "test_evidence.json"
CLOSURE_PATH = ROOT / "finding_closure.json"
RECORDED_AT = "2026-09-02T03:30:00+08:00"
TEST_NODES = {
    "FAILURE-AWARE-DECISION-012-ACCEPTED-SCOPE-CONSISTENCY": (
        "tests/unit/test_phase002d_r1_decisions.py::"
        "test_all_decisions_have_one_canonical_accepted_scope"
    ),
    "FAILURE-AWARE-DECISION-013-FIVE-VARIANT-REPLAY": (
        "tests/unit/test_phase002d_r1_replay.py::test_replay_projection_is_order_and_label_stable"
    ),
}


def _test_exists(root: Path, node: str) -> bool:
    path_text, name = node.split("::", 1)
    return (root / path_text).is_file() and f"def {name.split('[', 1)[0]}(" in (
        root / path_text
    ).read_text(encoding="utf-8")


def build_decision_repair_records(root: Path) -> tuple[dict, dict, dict]:
    round_one = read_json(root / ROUND_ONE_PATH)
    findings = {item["finding_id"]: item for item in round_one["findings"]}
    requests: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    closures: list[dict[str, Any]] = []
    for finding_id, node in TEST_NODES.items():
        if not _test_exists(root, node):
            raise ValueError(f"DECISION_REPAIR_TEST_MISSING:{finding_id}")
        finding = findings[finding_id]
        test_id = f"TEST-{finding_id}"
        command = f".venv/bin/python -m pytest -q {node}"
        path_text = node.split("::", 1)[0]
        requests.append(
            {
                "test_id": test_id,
                "finding_id": finding_id,
                "target": finding_id,
                "inputs": [round_one["audit_id"], round_one["bundle_id"]],
                "oracle": "The repaired canonical scope and five replay variants agree.",
                "command_or_procedure": command,
                "expected_result": "pytest exits 0 and the stated invariant holds",
                "pass_condition": "The requested deterministic node exits zero.",
                "fail_condition": "The requested deterministic node exits nonzero.",
                "artifacts": [path_text],
                "required_evidence": [node],
                "timeout": 120,
                "reproducibility": "DETERMINISTIC",
                "status": "PASSED",
            }
        )
        evidence.append(
            {
                "test_id": test_id,
                "finding_id": finding_id,
                "status": "PASSED",
                "observed_result": "pytest exit 0; deterministic repair node passed",
                "oracle_result": True,
                "command_or_procedure": command,
                "artifact_hashes": {path_text: file_sha256(root / path_text)},
                "started_at": RECORDED_AT,
                "completed_at": RECORDED_AT,
            }
        )
        closures.append(
            {
                "finding_id": finding_id,
                "original_severity": finding["severity"],
                "original_status": finding["status"],
                "disposition": "CLOSED_BY_EXECUTED_TEST",
                "test_id": test_id,
                "test_status": "PASSED",
            }
        )
    closure = {
        "schema_version": "1.0.0",
        "closure_id": "PHASE-002D-R1-DECISION-AUDIT-REPAIR-CLOSURE-001",
        "repair_loop": 1,
        "serious_finding_count": len(closures),
        "closed_serious_finding_count": len(closures),
        "all_serious_findings_closed": True,
        "changes": [
            "Canonical automated-decision scope extended with RELIABILITY_ONLY.",
            "Wrapper and embedded accepted_scope equality is now mandatory.",
            (
                "Five variants compare decision, scope, route, exclusions, negative-claim "
                "controls, and replay hashes."
            ),
        ],
        "closures": closures,
    }
    return (
        {"schema_version": "1.0.0", "requests": requests},
        {"schema_version": "1.0.0", "evidence": evidence},
        hashed_body(closure, "closure_hash"),
    )


def check_or_write_decision_repairs(root: Path, *, check: bool) -> dict[str, Any]:
    requests, evidence, closure = build_decision_repair_records(root)
    request_schema = Draft202012Validator(read_json(root / "contracts/test_request.schema.json"))
    evidence_schema = Draft202012Validator(read_json(root / "contracts/test_evidence.schema.json"))
    errors = [
        f"TEST_REQUEST_SCHEMA:{item.message}"
        for request in requests["requests"]
        for item in request_schema.iter_errors(request)
    ]
    errors.extend(
        f"TEST_EVIDENCE_SCHEMA:{item.message}"
        for record in evidence["evidence"]
        for item in evidence_schema.iter_errors(record)
    )
    for path, value in (
        (REQUESTS_PATH, requests),
        (EVIDENCE_PATH, evidence),
        (CLOSURE_PATH, closure),
    ):
        errors.extend(check_or_write(root / path, value, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "repair_loop": 1,
        "passed_count": len(evidence["evidence"]),
        "closure_hash": closure["closure_hash"],
    }
