"""Meaningful extension and history/terminal attacks against the current contract."""

import copy
import importlib.util
import json
import subprocess

import pytest

from cumcm_skill_lab.training_registry import (
    PHASE,
    historical_registry,
    repository_registry_errors,
    state_identity_errors,
    validate_registry,
)


def test_rc8_history_never_qualifies_changed_current_implementation(repo_root, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "rc9_historical_subject_probe", repo_root / "scripts/check_phase004c4_rc7_release.py"
    )
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    assert checker.evaluate_rc8_repository(stage="live", historical=True)["status"] == "PASS"
    current = checker.evaluate_rc8_repository(stage="candidate")
    assert current["status"] == "BLOCK"
    assert "RC8_CANDIDATE_CURRENT_IMPLEMENTATION_DRIFT" in current["reason_codes"]
    original = checker._subject_mapping

    def changed(subject, paths):
        mapping = original(subject, paths)
        mapping[".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"] = "0" * 64
        return mapping

    monkeypatch.setattr(checker, "_subject_mapping", changed)
    assert checker.evaluate_rc8_repository(stage="live", historical=True)["status"] == "BLOCK"


def extension(root):
    history = historical_registry(root)
    registry = copy.deepcopy(history)
    parent = registry["cases"][-2]
    case = {k: copy.deepcopy(parent[k]) for k in registry["required_case_fields"]}
    case.update(
        case_id="NEUTRAL-POSTVALIDATION-CHILD",
        set_type="DEVELOPMENT",
        skill_version="0.2.0-competition-rc9",
        first_run_status="NOT_STARTED",
        start_time=None,
        freeze_time=None,
        unlock_time=None,
        evidence_role="DEVELOPMENT_AFTER_VALIDATION",
        independent_problem=False,
        contamination_status="KNOWN_PROBLEM_AND_PRIOR_RESULTS",
        parent_case_id=parent["case_id"],
        parent_terminal_sha256="a" * 64,
        case_root=".cache/pr12-rc9/development/neutral-child",
    )
    registration = copy.deepcopy(case)
    registration.update(
        schema_version="postvalidation-development-registration/v1",
        phase=PHASE,
        authorization_path="evals/results/phase-004c6/qualification/proposal.json",
        parent_terminal_path=parent["terminal_decision"],
        budget={"model_cli_starts": 4, "independent_checker_starts": 4, "final_starts": 1},
    )
    registry["cases"].append(case)
    return registry, history, {case["case_id"]: registration}


def test_current_records_and_registered_extension_are_not_a_closed_count(repo_root):
    current = historical_registry(repo_root)
    assert repository_registry_errors(repo_root, current) == []
    registry, history, registrations = extension(repo_root)
    assert validate_registry(registry, history, registrations) == []
    registry["cases"].reverse()
    assert validate_registry(registry, history, registrations) == []


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("delete", "REGISTRY_HISTORY_MISSING"),
        ("old_hash", "REGISTRY_HISTORY_DRIFT"),
        ("old_freeze", "REGISTRY_HISTORY_DRIFT"),
        ("old_answer", "REGISTRY_HISTORY_DRIFT"),
        ("duplicate", "CASE_ID_DUPLICATE"),
        ("missing", "CASE_REQUIRED_FIELDS_MISSING"),
        ("wrong_type", "CASE_DEVELOPMENT_IDENTITY_INVALID"),
        ("unregistered", "CASE_REGISTRATION_MISSING"),
        ("parent", "CASE_PARENT_TERMINAL_INVALID"),
        ("budget", "CASE_DEVELOPMENT_BUDGET_INVALID"),
        ("root", "CASE_DEVELOPMENT_ROOT_INVALID"),
    ],
)
def test_extension_cannot_hide_history_or_contract_attacks(repo_root, mutation, reason):
    registry, history, registrations = extension(repo_root)
    old, child = registry["cases"][0], registry["cases"][-1]
    reg = registrations[child["case_id"]]
    if mutation == "delete":
        registry["cases"].pop(0)
    elif mutation == "old_hash":
        old["problem_hash"] = "0" * 64
    elif mutation == "old_freeze":
        old["first_run_freeze"]["sha256"] = "0" * 64
    elif mutation == "old_answer":
        old["answer_access_status"] = "SEALED"
    elif mutation == "duplicate":
        registry["cases"].append(copy.deepcopy(child))
    elif mutation == "missing":
        del child["problem_hash"]
    elif mutation == "wrong_type":
        child["set_type"] = reg["set_type"] = "VALIDATION"
    elif mutation == "unregistered":
        registrations.clear()
    elif mutation == "parent":
        reg["parent_case_id"] = old["case_id"]
    elif mutation == "budget":
        reg["budget"]["final_starts"] = 2
    elif mutation == "root":
        reg["case_root"] = child["case_root"] = ".cache/pr12-rc9/development/../old"
    assert any(e.startswith(reason) for e in validate_registry(registry, history, registrations))


@pytest.mark.parametrize(
    "subject",
    [
        "a03597be9a83a38ce4bcc4dba76cf8c574327045",
        "bcf498907cbf282e2c79580ea56b043fc1a7b52b",
        "17f109cadc8524c285af6a50776e6c3decb8b3e8",
    ],
)
def test_historical_terminal_contexts_remain_valid_and_bound(repo_root, subject):
    state = json.loads(
        subprocess.check_output(
            ["git", "show", f"{subject}:state/project_state.json"], cwd=repo_root
        )
    )
    schema = json.loads((repo_root / "contracts/project_state.schema.json").read_text())
    history = historical_registry(repo_root)
    assert state_identity_errors(state, schema, history) == []
    for field, value in (
        ("phase", "ARBITRARY_PHASE"),
        ("active_skill_version", "0.2.0-competition-rc999"),
        ("current_validation_case", "NEUTRAL-POSTVALIDATION-CHILD"),
        ("automated_decision_ids", []),
        (
            "technical_adjudication_status",
            "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT"
            if state["technical_adjudication_status"] == "C_TARGET_VALIDATION_FAILED"
            else "C_TARGET_VALIDATION_FAILED",
        ),
    ):
        changed = copy.deepcopy(state)
        changed[field] = value
        assert state_identity_errors(changed, schema, history), field


def test_current_maintenance_cannot_activate_wrong_version_or_start_validation(repo_root):
    state = json.loads((repo_root / "state/project_state.json").read_text())
    schema = json.loads((repo_root / "contracts/project_state.schema.json").read_text())
    history = historical_registry(repo_root)
    assert state_identity_errors(state, schema, history) == []
    for field, value in (
        ("target_candidate_version", "0.2.0-competition-rc8"),
        ("current_validation_case", "CUMCM-2016-C-VALIDATION-004"),
        ("next_phase_allowed", "PHASE-SKILL-C-TARGET-HELDOUT-004D"),
    ):
        changed = copy.deepcopy(state)
        changed[field] = value
        assert state_identity_errors(changed, schema, history)
