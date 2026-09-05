"""Regression checks for the frozen Phase 004C4 fresh Validation terminal."""

from __future__ import annotations

import importlib.util


def load_checker(repo_root):
    path = repo_root / "scripts/check_phase004c4_fresh_validation.py"
    spec = importlib.util.spec_from_file_location("phase004c4_fresh_validation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase004c4_fresh_validation_terminal_is_frozen(repo_root) -> None:
    checker = load_checker(repo_root)
    result = checker.evaluate(verify_workspace=False, require_delivery=False)
    assert result["status"] == "PASS", result
    assert result["verdict"] == "C_TARGET_VALIDATION_FAILED"
    assert result["answer_access_status"] == "SEALED"
    assert result["run_count"] == 9


def test_phase004c4_terminal_hard_failures_are_noncompensable(repo_root) -> None:
    checker = load_checker(repo_root)
    freeze = checker.load_json(repo_root / checker.FREEZE_RELATIVE)
    assert freeze["hard_failure_ids"] == ["HF14", "HF21", "HF23"]
    assert freeze["terminal_constraints"]["final_run_accepted"] is False
    assert freeze["terminal_constraints"]["handoff_accepted"] is False
    assert freeze["next_phase_allowed"] == "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5"
