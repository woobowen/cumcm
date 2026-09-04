from __future__ import annotations

import copy
import json

from scripts.check_c_target_2024c_validation_outcome import evaluate, validate_document


def test_terminal_validation_outcome_is_delivered_and_replayable() -> None:
    result = evaluate(verify_workspace=False, require_delivery=True)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["decision"] == "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT"
    assert len(result["freeze_payload_sha256"]) == 64


def test_terminal_validation_outcome_rejects_forced_pass(repo_root) -> None:
    path = repo_root / "evals/results/phase-004c-c-validation/terminal_validation_freeze.json"
    freeze = json.loads(path.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(freeze)
    tampered["decision"]["status"] = "C_TARGET_VALIDATION_PASSED"

    errors = validate_document(tampered)

    assert "VALIDATION_TERMINAL_PAYLOAD_HASH_MISMATCH" in errors
    assert "VALIDATION_TERMINAL_DECISION_INVALID" in errors


def test_terminal_validation_outcome_rejects_hidden_extra_run(repo_root) -> None:
    path = repo_root / "evals/results/phase-004c-c-validation/terminal_validation_freeze.json"
    freeze = json.loads(path.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(freeze)
    tampered["case_workspace"]["run_ids"].append("RUN-UNREGISTERED-999")

    errors = validate_document(tampered)

    assert "VALIDATION_TERMINAL_PAYLOAD_HASH_MISMATCH" in errors
    assert "VALIDATION_TERMINAL_WORKSPACE_RECORD_INVALID" in errors
