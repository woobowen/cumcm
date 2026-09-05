"""Synthetic subprocess integration for the one-shot completion controller."""

from __future__ import annotations

import importlib.util
import sys

import pytest


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize("all_failed", [False, True])
def test_captured_episode_preserves_failure_and_accesses_only_selected_test(
    repo_root, tmp_path, monkeypatch, all_failed
):
    controller = module(
        repo_root / "scripts/finalize_fresh_c_validation.py", "test_fresh_controller"
    )
    core = controller.load_core()
    synthetic = module(core.SKILL_ROOT / "scripts/synthetic_cases.py", "fresh_toy_helpers")
    monkeypatch.setattr(controller, "load_core", lambda: core)
    case = tmp_path / "case"
    core.initialize_case(case, "COMPLETION-TOY-001", "general")
    synthetic._common_intake(core, case, [{"requirement_id": "REQ-1"}], ["toy mean"])
    core.write_json(case / "data/raw/toy.json", [2, 4])

    def accepted(key, value):
        synthetic._accepted(core, case, key, value)

    accepted(
        "assumptions_and_symbols",
        {"assumptions": ["toy finite data"], "symbols": {"x": "unitless"}, "formulas": ["mean(x)"]},
    )
    inputs = {"data/raw/toy.json": core.file_hash(case / "data/raw/toy.json")}
    accepted("data_audit", {"raw_immutable": True, "data_hashes": inputs})
    core.advance_once(case)
    candidates = ["BASE", "CAND", "FAILED"]
    accepted(
        "model_candidates",
        {"candidates": [{"candidate_id": c, "baseline": c == "BASE"} for c in candidates]},
    )
    core.advance_once(case)
    model = case / "models/toy.py"
    model.write_text(
        "import argparse, base64, hashlib, json\n"
        "p=argparse.ArgumentParser();p.add_argument('--case-root');"
        "p.add_argument('--candidate-id');p.add_argument('--seed');p.add_argument('--output');"
        "a=p.parse_args();v={'BASE':2.0,'CAND':1.0,'FAILED':0.0}[a.candidate_id]\n"
        "o={'candidate_id':a.candidate_id,'status':'SUCCESS',"
        "'validation_metrics':{'loss':v},'final_metrics':{'loss':v},'claim_scope':'toy scope',"
        "'requirement_claims':{'REQ-1':{'claim_id':'CLAIM-TOY-1','claim_text':'local toy scope',"
        "'evidence_artifact_ids':[a.output]}},'figure_ready_data':[{'series':[v]}],"
        "'uncertainty':{'scope':'synthetic'},'limitations':['toy only'],"
        "'sealed_test_metrics_b64':base64.b64encode(json.dumps({'selected':a.candidate_id}).encode()).decode(),"
        "'sealed_test_payload_sha256':hashlib.sha256(json.dumps({'selected':a.candidate_id}).encode()).hexdigest(),"
        "'robustness_evidence':{'metric':'loss','metric_direction':'MIN',"
        "'perturbations':[{'perturbation_id':'SHIFT','metric':'loss','result':v+0.1,"
        "'evidence':'DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS'}],"
        "'failure_cases':['toy failure']}}\n"
        "json.dump(o,open(a.output,'w'));raise SystemExit(23 if "
        + ("True" if all_failed else "a.candidate_id=='FAILED'")
        + " else 0)\n"
    )
    code = synthetic._required_code_files(core)[:1] + [
        {
            "scope": "CASE_ROOT",
            "path": "models/toy.py",
            "repository_path": "tests/fixtures/toy.py",
            "sha256": core.file_hash(model),
        }
    ]
    commit = core.current_git_commit()
    blobs = {item["repository_path"]: item["sha256"] for item in code}
    monkeypatch.setattr(
        core, "git_blob_hash", lambda actual, path: blobs.get(path) if actual == commit else None
    )
    splits = {"train": [1], "validation": [2], "test": [3]}
    stop = "one synthetic run per candidate"
    generated = "2026-09-05T00:00:00Z"
    freezes = synthetic._freezes(
        core, candidates, "loss", splits, "BASE", inputs, stop, generated, code, commit
    )
    accepted(
        "experiment_plan",
        {
            "preregistered": True,
            "execution_prepared": True,
            "candidate_ids": candidates,
            "baseline_id": "BASE",
            "metric": "loss",
            "metric_direction": "MIN",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
            "selection_rule": "ARGMIN_THEN_ID",
            "random_seeds": [20260904],
            "splits": splits,
            "required_input_hashes": inputs,
            "required_code_files": code,
            "code_commit": commit,
            "trusted_freeze_registry": freezes,
            "stop_rule": stop,
            "handoff_generated_at": generated,
        },
    )
    synthetic._write_output_contract_probe(core, case, ["REQ-1"], metric="loss")
    core.advance_once(case)
    core.advance_once(case)
    for candidate in candidates:
        core.execute_case_code(
            case,
            run_id=f"RUN-{candidate}-20260904",
            candidate_id=candidate,
            seed=20260904,
            code_path="models/toy.py",
            timeout_seconds=30,
        )
    result = controller.complete(case, "sealed_test_metrics_b64")
    if all_failed:
        assert result["reason_codes"] == ["VALIDATION_NO_ELIGIBLE_SUCCESS"]
        assert result["selected_candidate_id"] is None
        assert all(item["validation_score"] is None for item in result["attempts"])
        assert len(list(case.glob("runs/*/manifest.json"))) == len(candidates)
        assert not (case / "evidence/selected_test_access.json").exists()
        return
    assert result["status"] == "PASS_NATIVE_CONTRACTS", result
    assert result["selected_candidate_id"] == "CAND"
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    failed = core.load_json(case / "runs/RUN-FAILED-20260904/manifest.json")
    assert failed["outcome"] == "FAILED"
    assert (
        next(x for x in result["attempts"] if x["candidate_id"] == "FAILED")["validation_score"]
        is None
    )
    access = core.load_json(case / "evidence/selected_test_access.json")
    assert access["test_metrics"] == {"selected": "CAND"}
    assert access["count"] == 1
    claim = core.read_artifact(case, "claim_evidence")["content"]
    assert claim["contract_version"] == "claim-evidence/v2"
    assert claim["claim_text"] != claim["requirement_claims"]["REQ-1"]["claim_text"]
    with pytest.raises(ValueError, match="STATE_INVALID"):
        controller.complete(case, "sealed_test_metrics_b64")
