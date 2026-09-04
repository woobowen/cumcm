from __future__ import annotations

import copy
import json

import yaml

from scripts.check_c_target_first_run_freezes import evaluate, validate_freeze


def test_c_target_first_run_freezes_are_current(repo_root) -> None:
    result = evaluate(repo_root)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["frozen_count"] >= 1
    assert result["frozen_count"] + result["in_progress_count"] == 3


def test_first_run_freeze_rejects_payload_and_answer_tampering(repo_root) -> None:
    registry = yaml.safe_load(
        (repo_root / "benchmarks/case_registry.yaml").read_text(encoding="utf-8")
    )
    record = next(
        item
        for item in registry["cases"]
        if item.get("case_id") == "CUMCM-2022-C-DEVELOPMENT-BATCH-001"
    )
    path = repo_root / record["first_run_freeze"]["path"]
    freeze = json.loads(path.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(freeze)
    tampered["answer_state_at_freeze"] = "UNLOCKED_AFTER_FIRST_RUN"

    errors = validate_freeze(tampered, record)

    assert any("PAYLOAD_HASH_MISMATCH" in error for error in errors)
    assert any("HEADER_INVALID" in error for error in errors)


def test_first_run_freeze_rejects_missing_required_hash(repo_root) -> None:
    registry = yaml.safe_load(
        (repo_root / "benchmarks/case_registry.yaml").read_text(encoding="utf-8")
    )
    record = next(
        item
        for item in registry["cases"]
        if item.get("case_id") == "CUMCM-2022-C-DEVELOPMENT-BATCH-001"
    )
    path = repo_root / record["first_run_freeze"]["path"]
    freeze = json.loads(path.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(freeze)
    tampered.pop("timing_hash")

    errors = validate_freeze(tampered, record)

    assert any("FIELDS_MISSING" in error for error in errors)
    assert any(error.endswith(":timing_hash") for error in errors)
