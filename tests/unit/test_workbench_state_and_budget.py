"""Engineering identity must not inherit release eligibility or old experiment budgets."""

import copy
import importlib.util
import json
import sys

import pytest
from jsonschema import Draft202012Validator

from cumcm_skill_lab.training_registry import validate_registry


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "mutation",
    [
        "none",
        "old_plan",
        "wrong_phase",
        "blind_case",
        "early_active",
        "human_override",
        "research_status",
        "wrong_subphase",
    ],
)
def test_build_tuple_is_enforced_at_schema_root(repo_root, mutation):
    state = json.loads((repo_root / "state/project_state.json").read_text())
    state.update(
        phase="PHASE-SKILL-MODULAR-WORKBENCH-004C7",
        current_plan="plans/active/PLAN-0004C7-modular-workbench.md",
        active_skill_version="0.2.0-competition-rc8",
        target_candidate_version="0.2.0-competition-rc10",
        technical_adjudication_status="MODULAR_WORKBENCH_BUILD_IN_PROGRESS",
        subphase="WORKBENCH-BUILD-AND-ACCEPT",
        current_validation_case=None,
    )
    changes = {
        "old_plan": ("current_plan", "plans/active/PLAN-0004C6-rc9-repair-and-development.md"),
        "wrong_phase": ("phase", "PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C6"),
        "blind_case": ("current_validation_case", "CUMCM-2016-C-VALIDATION-004"),
        "early_active": ("active_skill_version", "0.2.0-competition-rc10"),
        "human_override": ("team_compliance_review_status", "PASS"),
        "research_status": ("technical_adjudication_status", "C_TARGET_RC9_RESEARCH_READY"),
        "wrong_subphase": ("subphase", "WORKBENCH-ENGINEERING-TERMINAL"),
    }
    if mutation in changes:
        key, value = changes[mutation]
        state[key] = value
    schema = json.loads((repo_root / "contracts/project_state.schema.json").read_text())
    errors = list(Draft202012Validator(schema).iter_errors(state))
    assert (not errors) if mutation == "none" else bool(errors)


@pytest.mark.parametrize("attack", ["none", "old_version", "wrong_role", "excess", "wrong_root"])
def test_registered_usability_child_has_its_own_bounded_identity(repo_root, attack):
    helper = load(repo_root / "tests/unit/test_phase004c6_registry.py", "workbench_registry_helper")
    registry, history, registrations = helper.extension(repo_root)
    child = registry["cases"][-1]
    reg = registrations[child["case_id"]]
    for target in (child, reg):
        target.update(
            skill_version="0.2.0-competition-rc10",
            evidence_role="MODULE_USABILITY_DEVELOPMENT",
            case_root=".cache/modular-workbench-001/known/child-r1",
        )
    reg.update(
        schema_version="module-usability-development-registration/v1",
        phase="PHASE-SKILL-MODULAR-WORKBENCH-004C7",
        authorization_path="CUMCM_MODULAR_WORKBENCH_BUILD_PROMPT.md",
    )
    reg["budget"]["independent_checker_starts"] = 6
    if attack == "old_version":
        child["skill_version"] = reg["skill_version"] = "0.2.0-competition-rc9"
    elif attack == "wrong_role":
        child["evidence_role"] = reg["evidence_role"] = "DEVELOPMENT_AFTER_VALIDATION"
    elif attack == "excess":
        reg["budget"]["independent_checker_starts"] = 7
    elif attack == "wrong_root":
        reg["case_root"] = child["case_root"] = ".cache/pr12-rc9/development/old"
    errors = validate_registry(registry, history, registrations)
    assert (not errors) if attack == "none" else bool(errors)


def test_engineering_accepted_requires_actual_manifest_object(repo_root):
    state = json.loads((repo_root / "state/project_state.json").read_text())
    state.update(
        technical_adjudication_status="MODULAR_WORKBENCH_ENGINEERING_ACCEPTED",
        active_skill_version="0.2.0-competition-rc10",
        blockers=[],
        subphase="WORKBENCH-ENGINEERING-TERMINAL",
        verification_manifest=None,
    )
    state["automated_decision_ids"].append("DECISION-MODULAR-WORKBENCH-004C7")
    schema = json.loads((repo_root / "contracts/project_state.schema.json").read_text())
    assert list(Draft202012Validator(schema).iter_errors(state))


@pytest.mark.parametrize("explicit_null", [True, False])
def test_registered_lab_budget_cannot_be_omitted(repo_root, tmp_path, explicit_null):
    core = load(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        "wb_missing_budget",
    )
    root = tmp_path / "case"
    state = core.initialize_case(root, "ORIGINAL-MISSING-BUDGET", "general")
    policy = {
        "schema_version": "case-policy/v1",
        "case_id": state["case_id"],
        "mode": "LAB_EVAL",
        "budget_protocol": "MODULE_USABILITY_DEVELOPMENT_V1",
        "start_budget": {"model_cli_starts": 4, "independent_checker_starts": 6, "final_starts": 1},
    }
    core.write_json(root / "state/case_policy.json", policy)
    state["evidence_bindings"]["state/case_policy.json"] = core.file_hash(
        root / "state/case_policy.json"
    )
    core.write_json(core.state_path(root), state)
    core.write_json(
        root / core.ARTIFACT_PATHS["experiment_plan"],
        core.artifact(
            "experiment_plan",
            {"evaluation_design": {"start_budget": None} if explicit_null else {}},
        ),
    )
    with pytest.raises(ValueError, match="RC_EXECUTION_BUDGET_POLICY_INVALID"):
        core.consume_start_budget(
            root, "independent_checker_starts", "TEST", check_only=True, needed=100
        )


@pytest.mark.parametrize(
    "mode,budget,expected",
    [
        ("LEGACY", 5, "RC_EXECUTION_BUDGET_INVALID"),
        ("LAB_EVAL", 6, None),
        ("LAB_EVAL", 7, "RC_EXECUTION_BUDGET_INVALID"),
        ("GUIDED_LOCAL", 8, None),
    ],
)
def test_budget_policy_does_not_refund_or_silently_inherit_four(
    repo_root, tmp_path, mode, budget, expected
):
    core = load(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py", "wb_budget_core"
    )
    root = tmp_path / "case"
    state = core.initialize_case(root, "ORIGINAL-BUDGET-CONTRACT", "general")
    limits = {"model_cli_starts": 4, "independent_checker_starts": budget, "final_starts": 1}
    core.write_json(
        root / core.ARTIFACT_PATHS["experiment_plan"],
        core.artifact("experiment_plan", {"evaluation_design": {"start_budget": limits}}),
    )
    if mode != "LEGACY":
        policy = {
            "schema_version": "case-policy/v1",
            "case_id": state["case_id"],
            "mode": mode,
            "budget_protocol": "MODULE_USABILITY_DEVELOPMENT_V1",
            "start_budget": copy.deepcopy(limits),
        }
        path = root / "state/case_policy.json"
        core.write_json(path, policy)
        state["evidence_bindings"]["state/case_policy.json"] = core.file_hash(path)
        core.write_json(core.state_path(root), state)
    if expected:
        with pytest.raises(ValueError, match=expected):
            core.consume_start_budget(root, "independent_checker_starts", "TEST-CONTRACT")
        assert not (root / "state/execution_budget.json").exists()
    else:
        # This is a budget-ledger unit test, not a claim that subprocesses ran.
        core.consume_start_budget(root, "final_starts", "TEST-CONTRACT")
        with pytest.raises(ValueError, match="RC_EXECUTION_BUDGET_EXHAUSTED"):
            core.consume_start_budget(root, "final_starts", "TEST-CONTRACT")
        assert len(core.load_json(root / "state/execution_budget.json")["events"]) == 1
