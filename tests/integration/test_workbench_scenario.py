"""R7 closure must execute the public model and completion paths, before any Final."""

import copy
import importlib.util

import pytest


def fixture_module(repo):
    spec = importlib.util.spec_from_file_location(
        "workbench_science_fixture", repo / "tests/integration/test_rc9_science_semantics.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preparation(repo, *, change=None):
    science = fixture_module(repo)
    helper = science.module(repo)
    science.module = lambda _: helper
    original = helper._accepted

    def accept(core, case, key, content):
        if key == "experiment_plan" and change:
            content = copy.deepcopy(content)
            change(core, case, content)
        original(core, case, key, content)

    helper._accepted = accept
    return science


@pytest.mark.parametrize("kind", ["optimization", "prediction", "mixed"])
@pytest.mark.parametrize("explicit", [False, True])
def test_default_and_equivalent_explicit_reach_public_handoff(repo_root, tmp_path, kind, explicit):
    def declare(core, case, plan):
        if explicit:
            plan["scenario_hash"] = core.resolve_scenario_identity(case, plan)

    science = preparation(repo_root, change=declare)
    _, core, case = science.build(repo_root, tmp_path, kind)
    before = core.file_hash(case / core.ARTIFACT_PATHS["experiment_plan"])
    process, result = science.complete(repo_root, case)
    assert process.returncode == 0, result
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    assert core.file_hash(case / core.ARTIFACT_PATHS["experiment_plan"]) == before
    assert len(list((case / "runs").glob("*/execution_capture.json"))) == 2
    assert (case / core.FINAL_EVALUATION_LEDGER).is_file()
    assert (case / core.ARTIFACT_PATHS["claim_evidence"]).is_file()
    assert (case / core.ARTIFACT_PATHS["modeling_to_paper_handoff"]).is_file()


@pytest.mark.parametrize("bad", [None, "", False, 42, [], {}, "x" * 64, "a" * 64])
def test_bad_explicit_rejected_before_model_start(repo_root, tmp_path, bad):
    def change(core, case, plan):
        plan["scenario_hash"] = bad

    science = preparation(repo_root, change=change)
    with pytest.raises(ValueError, match="RC_SCENARIO_HASH_"):
        science.build(repo_root, tmp_path, "optimization")
    assert not list((tmp_path / "case/runs").glob("*/execution_capture.json"))
    assert not (tmp_path / "case/evidence/final_evaluation_ledger.json").exists()


@pytest.mark.parametrize("mutation", ["EMPTY", "ROLES", "SCOPE", "INPUT", "ASSUMPTIONS"])
def test_conflicting_prepared_identity_rejected_before_start(repo_root, tmp_path, mutation):
    def change(core, case, plan):
        plan["scenario_hash"] = core.resolve_scenario_identity(case, plan)
        if mutation == "EMPTY":
            plan["required_input_hashes"] = {}
        elif mutation == "ROLES":
            plan["input_roles"] = {"training": "data/raw/input.json", "test": "data/raw/input.json"}
        elif mutation == "SCOPE":
            plan["scenario"] = {
                "schema_version": "scenario/v1",
                "revision": 1,
                "requirement_ids": ["UNKNOWN"],
            }
        elif mutation == "INPUT":
            core.write_json(case / "data/raw/input.json", {"changed": True})
        else:
            plan["scenario"] = {
                "schema_version": "scenario/v1",
                "revision": 1,
                "constraints": ["new capacity"],
            }

    science = preparation(repo_root, change=change)
    expected = "RC_UPSTREAM_DEPENDENCY_STALE" if mutation == "INPUT" else "RC_SCENARIO_"
    with pytest.raises(ValueError, match=expected):
        science.build(repo_root, tmp_path, "optimization")
    assert not list((tmp_path / "case/runs").glob("*/execution_capture.json"))


def test_input_registry_order_equivalent_but_data_order_is_not(repo_root, tmp_path):
    science = fixture_module(repo_root)
    _, core, case = science.build(repo_root, tmp_path, "optimization")
    plan = core.read_artifact(case, "experiment_plan")["content"]
    core.write_json(case / "data/processed/other.json", [1, 2])
    plan["required_input_hashes"]["data/processed/other.json"] = core.file_hash(
        case / "data/processed/other.json"
    )
    expected = core.resolve_scenario_identity(case, plan)
    plan["required_input_hashes"] = dict(reversed(list(plan["required_input_hashes"].items())))
    assert core.resolve_scenario_identity(case, plan) == expected
    core.write_json(case / "data/processed/other.json", [2, 1])
    with pytest.raises(ValueError, match="RC_SCENARIO_INPUT_IDENTITY_INVALID"):
        core.resolve_scenario_identity(case, plan)
    plan["required_input_hashes"]["data/processed/other.json"] = core.file_hash(
        case / "data/processed/other.json"
    )
    assert core.resolve_scenario_identity(case, plan) != expected
