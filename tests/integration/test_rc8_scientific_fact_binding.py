"""Prospective RC8 actual-controller counterexamples; frozen before implementation."""

from __future__ import annotations

import importlib.util
import sys

import pytest


def _helpers(repo_root):
    path = repo_root / "tests/integration/test_p0_01_finalization_hf22_reproduction.py"
    spec = importlib.util.spec_from_file_location("rc8_fact_p0", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _case(repo_root, tmp_path):
    helpers = _helpers(repo_root)
    core, case = helpers._build_case(
        repo_root, tmp_path, model_fixture="tests/fixtures/authorized_final_eval_model.py"
    )
    # A semantic proposal must quote the actually captured local result, never substitute prose.
    semantic = core.read_artifact(case, "semantic_claim_support")["content"]
    for claim in semantic["claims"]:
        output = core.load_json(case / "runs" / claim["selected_run_ids"][0] / "output.json")
        claim["statement"] = output["requirement_claims"][claim["requirement_id"]]["claim_text"]
    _write(core, case, "semantic_claim_support", semantic)
    return helpers, core, case


def _write(core, case, key, value):
    core.write_json(case / core.ARTIFACT_PATHS[key], core.artifact(key, value))


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("scope_fields", "RC_CLAIM_SCOPE_OUTSIDE_SOURCE"),
        ("scope_time", "RC_CLAIM_SCOPE_OUTSIDE_SOURCE"),
        ("scope_entities", "RC_CLAIM_SCOPE_OUTSIDE_SOURCE"),
        ("statement", "RC_CLAIM_STATEMENT_OUTPUT_MISMATCH"),
        ("source_hash", "RC_SOURCE_INPUT_HASH_UNBOUND"),
        ("feasibility_true", "RC_FEASIBILITY_INDEPENDENT_RECALC_MISSING"),
        ("causal_true", "RC_CAUSAL_IDENTIFICATION_MISSING"),
        ("simulation_true", "RC_SIMULATION_CONDITIONAL_ASSUMPTIONS_MISSING"),
        ("metric_alias", "RC_CLAIM_METRIC_BINDING_MISSING"),
        ("counter_evidence", "RC_CLAIM_COUNTER_EVIDENCE_UNRESOLVED"),
    ],
)
def test_actual_controller_rejects_unsupported_fact_mutation(repo_root, tmp_path, mutation, reason):
    helpers, core, case = _case(repo_root, tmp_path)
    semantic = core.read_artifact(case, "semantic_claim_support")["content"]
    claim = semantic["claims"][0]
    before = {
        run: core.file_hash(case / "runs" / run / "output.json")
        for run in ("RUN-BASE-20260905", "RUN-CAND-20260905")
    }
    if mutation.startswith("scope_"):
        claim["scope"][mutation.removeprefix("scope_")] = ["OUTSIDE_REGISTERED_SCOPE"]
    elif mutation == "statement":
        claim["statement"] = "Zero error for all future and external entities."
    elif mutation == "source_hash":
        source = core.read_artifact(case, "source_ledger")["content"]
        source["sources"][0]["hash"] = "f" * 64
        _write(core, case, "source_ledger", source)
        suff = core.read_artifact(case, "data_sufficiency")["content"]
        suff["sources"] = source["sources"]
        _write(core, case, "data_sufficiency", suff)
    elif mutation == "feasibility_true":
        claim["claim_type"] = "FEASIBILITY"
        claim["support_predicates"]["independent_constraint_recalculation"] = True
    elif mutation == "causal_true":
        claim["claim_type"] = "CAUSAL"
        claim["support_predicates"]["causal_identification_design"] = True
    elif mutation == "simulation_true":
        claim["claim_type"] = "SIMULATION_CONDITIONAL"
        claim["support_predicates"]["registered_assumptions_bound"] = True
    elif mutation == "metric_alias":
        claim["metric_ids"].append("metric_not_computed")
        semantic["outputs"][0]["metric_ids"].append("metric_not_computed")
    elif mutation == "counter_evidence":
        claim["counter_evidence"] = [{"status": "UNRESOLVED", "finding": "contradicted"}]
    _write(core, case, "semantic_claim_support", semantic)
    completed, result = helpers._run_controller(repo_root, case)
    assert completed.returncode != 0, result
    assert reason in result["reason_codes"], result
    assert "GATE_HANDOFF" not in helpers._gate_map(core, case)
    assert before == {run: core.file_hash(case / "runs" / run / "output.json") for run in before}


def test_actual_semantic_cli_rejects_unsupported_proposal(repo_root, tmp_path):
    import json
    import subprocess

    _, core, case = _case(repo_root, tmp_path)
    semantic = core.read_artifact(case, "semantic_claim_support")["content"]
    semantic["claims"][0]["scope"]["entities"] = ["UNOBSERVED_POPULATION"]
    _write(core, case, "semantic_claim_support", semantic)
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"),
            "semantic-check",
            "--case-root",
            str(case),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    result = json.loads(completed.stdout)
    assert completed.returncode != 0, result
    assert "RC_CLAIM_SCOPE_OUTSIDE_SOURCE" in result["reason_codes"]
