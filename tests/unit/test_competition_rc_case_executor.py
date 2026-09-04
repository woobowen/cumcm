from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture
def case_cli(repo_root: Path):
    path = repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
    spec = importlib.util.spec_from_file_location("cumcm_case_executor_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def accepted(case_cli, case_root: Path, key: str, content: dict) -> None:
    case_cli.write_json(
        case_root / case_cli.ARTIFACT_PATHS[key],
        case_cli.artifact(key, content),
    )


def test_case_executor_captures_seals_and_detects_log_mutation(
    case_cli, repo_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case_root = tmp_path / "case"
    case_cli.initialize_case(case_root, "EXECUTOR-GENERIC-001", "general")
    raw_relative = "data/raw/observations.json"
    raw_path = case_root / raw_relative
    case_cli.write_json(raw_path, [{"x": 1.0}, {"x": 2.0}], overwrite=False)
    raw_hash = case_cli.file_hash(raw_path)
    accepted(
        case_cli,
        case_root,
        "problem_requirements",
        {
            "case_id": "EXECUTOR-GENERIC-001",
            "requirements": [{"requirement_id": "REQ-1", "text": "fit"}],
        },
    )
    case_cli.advance_once(case_root)
    case_cli.advance_once(case_root)
    accepted(
        case_cli,
        case_root,
        "research_plan",
        {
            "mode": "DEVELOPMENT_REGRESSION",
            "external_search": False,
            "first_run_freeze_sha256": "a" * 64,
        },
    )
    accepted(
        case_cli,
        case_root,
        "source_ledger",
        {
            "sources": [{"source_id": "SRC-1"}],
            "answer_access_status": "UNLOCKED_AFTER_FIRST_RUN",
        },
    )
    case_cli.advance_once(case_root)
    accepted(case_cli, case_root, "assumptions_and_symbols", {"assumptions": ["finite"]})
    accepted(
        case_cli,
        case_root,
        "data_audit",
        {"raw_immutable": True, "data_hashes": {raw_relative: raw_hash}},
    )
    case_cli.advance_once(case_root)
    candidates = [
        {"candidate_id": "BASE", "baseline": True},
        {"candidate_id": "CAND", "baseline": False},
        {"candidate_id": "INVALID", "baseline": False},
    ]
    accepted(case_cli, case_root, "model_candidates", {"candidates": candidates})
    case_cli.advance_once(case_root)

    model_relative = "models/generic_model.py"
    model_path = case_root / model_relative
    model_path.write_text(
        "import argparse, json\n"
        "p=argparse.ArgumentParser(); p.add_argument('--case-root'); "
        "p.add_argument('--candidate-id'); p.add_argument('--seed'); "
        "p.add_argument('--output'); a=p.parse_args(); "
        "output={'candidate_id':a.candidate_id,'status':'SUCCESS',"
        "'validation_metrics':{'loss':1.0}}; "
        "output.update({'final_metrics':{'loss':1.0},'claim_scope':'generic',"
        "'requirement_claims':{'REQ-1':{'claim_id':'CLAIM-GENERIC-1',"
        "'claim_text':'generic','evidence_artifact_ids':[a.output]}},"
        "'figure_ready_data':[{'figure_id':'GENERIC'}],"
        "'uncertainty':{'scope':'bounded'},'limitations':['generic limitation'],"
        "'robustness_evidence':{'metric':'loss','metric_direction':'MIN',"
        "'perturbations':[{'perturbation_id':'GENERIC-SHIFT','metric':'loss',"
        "'result':1.1,'evidence':'DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS'}],"
        "'failure_cases':['generic failure']}}) if a.candidate_id != 'INVALID' else None; "
        "json.dump(output, open(a.output,'w'), sort_keys=True); "
        "raise SystemExit(2 if a.candidate_id == 'BASE' else 0)\n",
        encoding="utf-8",
    )
    commit = case_cli.current_git_commit()
    code_files = [
        {
            "scope": "SKILL_ROOT",
            "path": "scripts/cumcm_case.py",
            "repository_path": ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
            "sha256": case_cli.file_hash(case_cli.SKILL_ROOT / "scripts/cumcm_case.py"),
        },
        {
            "scope": "CASE_ROOT",
            "path": model_relative,
            "repository_path": "tests/fixtures/generic_model.py",
            "sha256": case_cli.file_hash(model_path),
        },
    ]
    blob_hashes = {record["repository_path"]: record["sha256"] for record in code_files}
    monkeypatch.setattr(
        case_cli,
        "git_blob_hash",
        lambda observed_commit, repository_path: (
            blob_hashes.get(repository_path) if observed_commit == commit else None
        ),
    )
    splits = {"train": [1], "validation": [2], "test": [3]}
    required_inputs = {raw_relative: raw_hash}
    seeds = [11]
    stop_rule = "one bounded run"
    generated_at = "2026-09-04T00:00:00Z"
    freezes = {
        "candidate_set": case_cli.canonical_hash(["BASE", "CAND", "INVALID"]),
        "metric": case_cli.canonical_hash(
            {
                "name": "loss",
                "direction": "MIN",
                "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
                "selection_rule": "ARGMIN_THEN_ID",
            }
        ),
        "seed_schedule": case_cli.canonical_hash(seeds),
        "split_assignment": case_cli.canonical_hash(splits),
        "baseline": case_cli.canonical_hash("BASE"),
        "input_set": case_cli.canonical_hash(required_inputs),
        "execution_policy": case_cli.canonical_hash(
            {"stop_rule": stop_rule, "handoff_generated_at": generated_at}
        ),
        "code_set": case_cli.canonical_hash(code_files),
        "code_commit": case_cli.canonical_hash(commit),
    }
    accepted(
        case_cli,
        case_root,
        "experiment_plan",
        {
            "preregistered": True,
            "execution_prepared": True,
            "candidate_ids": ["BASE", "CAND", "INVALID"],
            "baseline_id": "BASE",
            "metric": "loss",
            "metric_direction": "MIN",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
            "selection_rule": "ARGMIN_THEN_ID",
            "random_seeds": seeds,
            "splits": splits,
            "required_input_hashes": required_inputs,
            "required_code_files": code_files,
            "code_commit": commit,
            "trusted_freeze_registry": freezes,
            "stop_rule": stop_rule,
            "handoff_generated_at": generated_at,
        },
    )
    case_cli.write_json(
        case_root / "experiments/selected_output_contract_probe.json",
        {
            "candidate_id": "CONTRACT-PROBE",
            "status": "CONTRACT_PROBE",
            "probe_only": True,
            "ranking_eligible": False,
            "result_values_are_placeholders": True,
            "final_metrics": {"loss": 0.0},
            "claim_scope": "generic placeholder",
            "requirement_claims": {
                "REQ-1": {
                    "claim_id": "CLAIM-PROBE-1",
                    "claim_text": "generic placeholder",
                    "evidence_artifact_ids": ["experiments/selected_output_contract_probe.json"],
                }
            },
            "figure_ready_data": [{"figure_id": "GENERIC-PROBE"}],
            "uncertainty": {"scope": "placeholder"},
            "limitations": ["placeholder values are not results"],
            "robustness_evidence": {
                "metric": "loss",
                "metric_direction": "MIN",
                "perturbations": [
                    {
                        "perturbation_id": "GENERIC-PROBE-SHIFT",
                        "metric": "loss",
                        "result": 0.0,
                        "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                    }
                ],
                "failure_cases": ["probe does not establish robustness"],
            },
        },
        overwrite=False,
    )
    case_cli.advance_once(case_root)
    case_cli.advance_once(case_root)

    captured = case_cli.execute_case_code(
        case_root,
        run_id="RUN-CAND-11",
        candidate_id="CAND",
        seed=11,
        code_path=model_relative,
        timeout_seconds=30,
    )
    assert captured["outcome"] == "SUCCESS"
    sealed = case_cli.seal_captured_run(case_root, run_id="RUN-CAND-11", decision_hash="a" * 64)
    manifest = case_cli.load_json(case_root / sealed["manifest_path"])
    assert case_cli.validate_manifest(
        manifest, case_root=case_root, trusted_freezes=freezes
    ).accepted

    failed_capture = case_cli.execute_case_code(
        case_root,
        run_id="RUN-BASE-11",
        candidate_id="BASE",
        seed=11,
        code_path=model_relative,
        timeout_seconds=30,
    )
    assert failed_capture["outcome"] == "FAILED"
    failed_capture_record = case_cli.load_json(case_root / failed_capture["capture_path"])
    assert failed_capture_record["failure"] == {
        "reason_code": "RC_EXECUTION_NONZERO_EXIT",
        "retained": True,
    }
    failed_seal = case_cli.seal_captured_run(
        case_root, run_id="RUN-BASE-11", decision_hash="b" * 64
    )
    failed_manifest = case_cli.load_json(case_root / failed_seal["manifest_path"])
    assert failed_manifest["outcome"] == "FAILED"
    assert failed_manifest["failure"] == {
        "reason_code": "RC_EXECUTION_NONZERO_EXIT",
        "retained": True,
    }
    failed_gate = case_cli.validate_manifest(
        failed_manifest, case_root=case_root, trusted_freezes=freezes
    )
    assert not failed_gate.accepted
    assert failed_gate.reason_codes == ("RC_MANIFEST_NOT_SUCCESS:FAILED",)

    invalid_capture = case_cli.execute_case_code(
        case_root,
        run_id="RUN-INVALID-11",
        candidate_id="INVALID",
        seed=11,
        code_path=model_relative,
        timeout_seconds=30,
    )
    assert invalid_capture["outcome"] == "FAILED"
    invalid_output = case_cli.load_json(case_root / invalid_capture["output"]["path"])
    assert invalid_output == {
        "candidate_id": "INVALID",
        "status": "SUCCESS",
        "validation_metrics": {"loss": 1.0},
    }
    invalid_capture_record = case_cli.load_json(case_root / invalid_capture["capture_path"])
    assert invalid_capture_record["failure"]["reason_code"] == (
        "RC_EXECUTION_OUTPUT_CONTRACT_INVALID"
    )
    assert (
        "RC_OUTPUT_CONTRACT_REQUIRED_FIELDS_MISSING"
        in invalid_capture_record["failure"]["reason_codes"]
    )

    stdout = case_root / "runs/RUN-CAND-11/stdout.txt"
    stdout.write_text("tampered", encoding="utf-8")
    rejected = case_cli.validate_manifest(manifest, case_root=case_root, trusted_freezes=freezes)
    assert "RC_EXECUTION_CAPTURE_STDOUT_MUTATION" in rejected.reason_codes


def test_unlocked_answer_status_requires_bound_development_regression(
    case_cli, tmp_path: Path
) -> None:
    case_root = tmp_path / "case"
    case_cli.initialize_case(case_root, "EXECUTOR-GENERIC-BOUNDARY-001", "general")
    accepted(
        case_cli,
        case_root,
        "problem_requirements",
        {
            "case_id": "EXECUTOR-GENERIC-BOUNDARY-001",
            "requirements": [{"requirement_id": "REQ-1", "text": "fit"}],
        },
    )
    case_cli.advance_once(case_root)
    case_cli.advance_once(case_root)
    accepted(case_cli, case_root, "research_plan", {"external_search": False})
    accepted(
        case_cli,
        case_root,
        "source_ledger",
        {
            "sources": [{"source_id": "SRC-1"}],
            "answer_access_status": "UNLOCKED_AFTER_FIRST_RUN",
        },
    )

    with pytest.raises(ValueError, match="RC_ANSWER_ACCESS_PROHIBITED"):
        case_cli.advance_once(case_root)
