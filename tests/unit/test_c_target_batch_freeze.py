from __future__ import annotations

import copy
import json

from scripts.check_c_target_batch_freeze import evaluate, validate_document


def test_c_target_batch_freeze_is_current_and_complete(repo_root) -> None:
    result = evaluate(repo_root)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["case_count"] == 3
    assert len(result["freeze_payload_sha256"]) == 64


def test_c_target_batch_freeze_rejects_payload_or_answer_tampering(repo_root) -> None:
    path = repo_root / "evals/results/phase-004c-c-batch/batch_pre_run_freeze.json"
    frozen = json.loads(path.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(frozen)
    tampered["cases"][0]["answer_state"] = "UNLOCKED_AFTER_FIRST_RUN"

    errors = validate_document(tampered)

    assert "BATCH_FREEZE_PAYLOAD_HASH_MISMATCH" in errors
    assert any(error.startswith("BATCH_FREEZE_CASE_INVALID:") for error in errors)


def test_c_target_batch_freeze_rejects_parallelism_drift(repo_root) -> None:
    path = repo_root / "evals/results/phase-004c-c-batch/batch_pre_run_freeze.json"
    frozen = json.loads(path.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(frozen)
    tampered["parallelism"]["maximum_concurrent_case_workers"] = 3

    errors = validate_document(tampered)

    assert "BATCH_FREEZE_PAYLOAD_HASH_MISMATCH" in errors
    assert "BATCH_FREEZE_PARALLELISM_INVALID" in errors
