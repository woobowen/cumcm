"""Prospective scientific positive route and actual Final lifecycle attacks."""

import importlib.util
import sys

import pytest


def _module(repo_root, relative, name):
    spec = importlib.util.spec_from_file_location(name, repo_root / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _nonpredictive(repo_root, tmp_path):
    helper = _module(repo_root, "tests/integration/test_actual_controller_neutral_e2e.py", "rc8_np")
    core = _module(
        repo_root, ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py", "rc8_np_core"
    )
    requirements = [helper._requirement(req) for req in ["REQ-A", "REQ-B"]]
    sources = [helper._source("SRC-ALL", ["REQ-A", "REQ-B"], "AUTO")]
    sufficiency = {
        "contract_version": "data-sufficiency/v1",
        "requirements": requirements,
        "sources": sources,
        "acquisition_plans": [],
        "source_compositions": [],
        "coverage_mode_by_requirement": {
            req: {"mode": "SINGLE_SOURCE", "source_id": "SRC-ALL"} for req in ["REQ-A", "REQ-B"]
        },
        "aggregate_completion_claimed": False,
        "requirement_assessments": [helper._assessment(req) for req in ["REQ-A", "REQ-B"]],
    }
    selection, semantic = helper._selection_and_semantic(
        core,
        requirements,
        "",
        mode="GLOBAL_JOINT",
        selected_candidates={"REQ-A": "CAND", "REQ-B": "CAND"},
        claim_types={"REQ-A": "FEASIBILITY", "REQ-B": "FEASIBILITY"},
    )
    selection["requirements"][1]["selection_direction"] = "MAX"
    for claim in semantic["claims"]:
        claim["support_predicates"]["independent_constraint_recalculation"] = True
    core, case = helper._build_runtime_case(
        repo_root,
        tmp_path,
        requirements=requirements,
        sources=sources,
        sufficiency=sufficiency,
        selection=selection,
        semantic=semantic,
        model_fixture="tests/fixtures/scientific_optimization_model.py",
        checker_fixture="tests/fixtures/scientific_independent_check.py",
        nonpredictive=True,
    )
    return helper, core, case


def test_real_optimization_without_fake_prediction_splits_reaches_handoff(repo_root, tmp_path):
    helper, core, case = _nonpredictive(repo_root, tmp_path)
    run_id = "RUN-CAND-20260906"
    core.execute_scientific_check(case, run_id=run_id, code_path="models/independent_check.py")
    completed, result = helper._run_controller(repo_root, case)
    assert completed.returncode == 0, result
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    assert result["test_access_count"] == 0
    assert result["scientific_final_verification_count"] == 1
    assert not (case / "evidence/final_evaluation_ledger.json").exists()


@pytest.mark.parametrize("mutation", ["missing_check", "tampered_check", "predictive_rename"])
def test_nonpredictive_route_requires_real_check_and_cannot_support_prediction(
    repo_root, tmp_path, mutation
):
    helper, core, case = _nonpredictive(repo_root, tmp_path)
    run_id = "RUN-CAND-20260906"
    if mutation != "missing_check":
        core.execute_scientific_check(case, run_id=run_id, code_path="models/independent_check.py")
    if mutation == "tampered_check":
        path = case / "runs" / run_id / "scientific_check.json"
        record = core.load_json(path)
        record["requirements"]["REQ-A"]["constraint_residuals"]["demand"]["value"] = 100
        core.write_json(path, record)
    if mutation == "predictive_rename":
        semantic = core.read_artifact(case, "semantic_claim_support")["content"]
        semantic["claims"][0]["claim_type"] = "PREDICTIVE"
        semantic["claims"][0]["support_predicates"].update(
            validation_boundary_frozen=True, held_out_test_valid=True
        )
        helper._accepted(core, case, "semantic_claim_support", semantic)
    completed, result = helper._run_controller(repo_root, case)
    assert completed.returncode != 0, result
    assert core.load_state(case)["state"] == "RUNNING"


@pytest.mark.parametrize("mutation", ["code", "input"])
def test_actual_evaluate_final_rejects_drift_before_execution(repo_root, tmp_path, mutation):
    helper = _module(repo_root, "tests/integration/test_p0_02_final_evaluation.py", "rc8_final")
    core, case = helper._build_authorized(repo_root, tmp_path)
    _, decision_hash = helper._decision(core, case)
    capture = core.load_json(case / "runs" / helper.SELECTED_RUN / "execution_capture.json")
    relative = capture["argv"][0] if mutation == "code" else capture["input_files"][0]["path"]
    with (case / relative).open("a") as stream:
        stream.write("\n ")
    completed, result = helper._evaluate_final(repo_root, case, helper.SELECTED_RUN, decision_hash)
    assert completed.returncode != 0, result
    assert not (case / "runs" / helper.SELECTED_RUN / "sealed_test.json").exists()


def test_failed_final_evaluator_consumes_access_budget_and_preserves_failure(repo_root, tmp_path):
    helper = _module(repo_root, "tests/integration/test_p0_02_final_evaluation.py", "rc8_failure")
    p001 = helper._p001(repo_root, tmp_path)
    core, case = p001._build_case(
        repo_root, tmp_path, model_fixture="tests/fixtures/failed_final_eval_model.py"
    )
    _, decision_hash = helper._decision(core, case)
    completed, result = helper._evaluate_final(repo_root, case, helper.SELECTED_RUN, decision_hash)
    assert completed.returncode != 0, result
    ledger = core.load_json(case / helper.LEDGER)
    assert ledger["status"] == "FAILED"
    assert ledger["count"] == 1
    again, second = helper._evaluate_final(repo_root, case, helper.SELECTED_RUN, decision_hash)
    assert again.returncode != 0
    assert "RC_FINAL_TEST_ALREADY_ACCESSED" in second["reason_codes"]


def test_actual_controller_rejects_missing_generation_facts(repo_root, tmp_path):
    helper = _module(
        repo_root, "tests/integration/test_p0_02_final_evaluation.py", "rc8_missing_facts"
    )
    p001 = helper._p001(repo_root, tmp_path)
    core, case = p001._build_case(
        repo_root, tmp_path, model_fixture="tests/fixtures/missing_scientific_facts_model.py"
    )
    completed, result = p001._run_controller(repo_root, case)
    assert completed.returncode != 0, result
    assert "RC_CLAIM_GENERATION_FACTS_INVALID" in result["reason_codes"]
    assert core.load_state(case)["state"] == "RUNNING"
