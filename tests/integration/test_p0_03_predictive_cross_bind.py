"""P0-03 PREDICTIVE held-out predicates must match Final evaluation facts.

Actual controller/CLI entrypoints only. Development output and semantic payload cannot
self-attest authorization. Frozen 2017 artifacts are not modified.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

AUTHORIZED_FIXTURE = "tests/fixtures/authorized_final_eval_model.py"
SELECTED_RUN = "RUN-CAND-20260905"
LEDGER = "evidence/final_evaluation_ledger.json"
CONTRADICTS = "RC_PREDICTIVE_SUPPORT_CONTRADICTS_SELECTED_OUTPUT"
NOT_OWNED = "RC_PREDICTIVE_TEST_RUN_NOT_OWNED"
ACCESS_INVALID = "RC_PREDICTIVE_TEST_ACCESS_INVALID"


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def _helpers(repo_root: Path, tmp_path: Path):
    p001 = _module(
        repo_root / "tests/integration/test_p0_01_finalization_hf22_reproduction.py",
        f"p003_p001_{tmp_path.name}",
    )
    p002 = _module(
        repo_root / "tests/integration/test_p0_02_final_evaluation.py",
        f"p003_p002_{tmp_path.name}",
    )
    return p001, p002


def _req_a_predictive(semantic: dict) -> dict:
    for claim in semantic["claims"]:
        if claim["requirement_id"] == "REQ-A":
            claim["claim_type"] = "PREDICTIVE"
            claim["support_predicates"] = {
                "scope_bounded": True,
                "validation_boundary_frozen": True,
                "held_out_test_valid": True,
            }
    return semantic


def test_hf22_false_heldout_blocks_semantic_gate(repo_root, tmp_path) -> None:
    p001, _p002 = _helpers(repo_root, tmp_path)
    core, case = p001._build_case(
        repo_root,
        tmp_path,
        model_fixture="tests/fixtures/predictive_false_heldout_model.py",
        semantic_adjust=p001._hf22_semantic,
    )
    selected = core.load_json(case / f"runs/{SELECTED_RUN}/output.json")
    assert selected["evaluation_boundary"] == "DEVELOPMENT_GROUPED_OOS"
    assert selected["held_out_test_valid"] is False
    assert selected["test_access_status"] == "NOT_AUTHORIZED"
    assert selected["test_access_count"] == 0

    completed, result = p001._run_controller(repo_root, case)
    gates = p001._gate_map(core, case)
    assert completed.returncode != 0
    assert result["status"] == "BLOCK_NATIVE_CONTRACTS"
    assert CONTRADICTS in result["reason_codes"]
    assert gates["GATE_SEMANTIC_CLAIM"]["result"] == "BLOCK"
    assert CONTRADICTS in gates["GATE_SEMANTIC_CLAIM"]["reason_codes"]
    assert "GATE_AGGREGATE_CLAIM" not in gates
    assert "GATE_HANDOFF" not in gates
    assert result.get("test_access_count", 0) == 0
    _p002._assert_no_accepted_final(core, case)


def test_legal_predictive_after_evaluate_final_reaches_handoff(repo_root, tmp_path) -> None:
    p001, p002 = _helpers(repo_root, tmp_path)
    core, case = p001._build_case(
        repo_root,
        tmp_path,
        model_fixture=AUTHORIZED_FIXTURE,
        semantic_adjust=p001._hf22_semantic,
    )
    selected = core.load_json(case / f"runs/{SELECTED_RUN}/output.json")
    assert selected["held_out_test_valid"] is False
    assert "sealed_test_metrics_b64" not in selected
    _, decision_hash = p002._decision(core, case)
    completed, payload = p002._evaluate_final(repo_root, case, SELECTED_RUN, decision_hash)
    assert completed.returncode == 0, payload

    completed, result = p001._run_controller(repo_root, case)
    gates = p001._gate_map(core, case)
    assert completed.returncode == 0, (completed.stderr, result)
    assert result["status"] == "PASS_NATIVE_CONTRACTS"
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    assert gates["GATE_SEMANTIC_CLAIM"]["result"] == "PASS"
    assert gates["GATE_AGGREGATE_CLAIM"]["result"] == "PASS"
    assert gates["GATE_HANDOFF"]["result"] == "PASS"
    assert CONTRADICTS not in result.get("reason_codes", [])
    assert core.load_json(case / f"runs/{SELECTED_RUN}/output.json")["held_out_test_valid"] is False
    ledger = core.load_json(case / LEDGER)
    assert ledger["count"] == 1
    assert ledger["used_for_selection"] is False
    assert ledger["run_id"] == SELECTED_RUN


def test_predictive_without_ledger_blocks_even_with_authorized_model(
    repo_root, tmp_path
) -> None:
    p001, p002 = _helpers(repo_root, tmp_path)
    core, case = p001._build_case(
        repo_root,
        tmp_path,
        model_fixture=AUTHORIZED_FIXTURE,
        semantic_adjust=p001._hf22_semantic,
    )
    completed, result = p001._run_controller(repo_root, case)
    gates = p001._gate_map(core, case)
    assert completed.returncode != 0
    assert CONTRADICTS in result["reason_codes"]
    assert gates["GATE_SEMANTIC_CLAIM"]["result"] == "BLOCK"
    assert "GATE_AGGREGATE_CLAIM" not in gates
    p002._assert_no_accepted_final(core, case)


def test_predictive_wrong_run_ownership_blocks(repo_root, tmp_path) -> None:
    p001, p002 = _helpers(repo_root, tmp_path)
    core, case = p001._build_case(
        repo_root,
        tmp_path,
        model_fixture=AUTHORIZED_FIXTURE,
        semantic_adjust=_req_a_predictive,
    )
    _, decision_hash = p002._decision(core, case)
    completed, payload = p002._evaluate_final(repo_root, case, SELECTED_RUN, decision_hash)
    assert completed.returncode == 0, payload
    completed, result = p001._run_controller(repo_root, case)
    gates = p001._gate_map(core, case)
    assert completed.returncode != 0
    assert NOT_OWNED in result["reason_codes"]
    assert gates["GATE_SEMANTIC_CLAIM"]["result"] == "BLOCK"
    assert "GATE_HANDOFF" not in gates
    p002._assert_no_accepted_final(core, case)


def test_predictive_stale_ledger_hash_blocks(repo_root, tmp_path) -> None:
    p001, p002 = _helpers(repo_root, tmp_path)
    core, case = p001._build_case(
        repo_root,
        tmp_path,
        model_fixture=AUTHORIZED_FIXTURE,
        semantic_adjust=p001._hf22_semantic,
    )
    _, decision_hash = p002._decision(core, case)
    completed, payload = p002._evaluate_final(repo_root, case, SELECTED_RUN, decision_hash)
    assert completed.returncode == 0, payload
    sidecar = case / f"runs/{SELECTED_RUN}/sealed_test.json"
    mutated = core.load_json(sidecar)
    mutated["sealed_test_payload_sha256"] = "b" * 64
    core.write_json(sidecar, mutated)
    completed, result = p001._run_controller(repo_root, case)
    gates = p001._gate_map(core, case)
    assert completed.returncode != 0
    assert "RC_FINAL_TEST_PAYLOAD_HASH_MISMATCH" in result["reason_codes"]
    assert gates["GATE_SEMANTIC_CLAIM"]["result"] == "BLOCK"
    assert "GATE_FINALIZATION" not in gates
    p002._assert_no_accepted_final(core, case)


def test_predictive_used_for_selection_blocks(repo_root, tmp_path) -> None:
    p001, p002 = _helpers(repo_root, tmp_path)
    core, case = p001._build_case(
        repo_root,
        tmp_path,
        model_fixture=AUTHORIZED_FIXTURE,
        semantic_adjust=p001._hf22_semantic,
    )
    _, decision_hash = p002._decision(core, case)
    completed, payload = p002._evaluate_final(repo_root, case, SELECTED_RUN, decision_hash)
    assert completed.returncode == 0, payload
    ledger = core.load_json(case / LEDGER)
    ledger["used_for_selection"] = True
    core.write_json(case / LEDGER, ledger)
    completed, result = p001._run_controller(repo_root, case)
    gates = p001._gate_map(core, case)
    assert completed.returncode != 0
    assert ACCESS_INVALID in result["reason_codes"]
    assert gates["GATE_SEMANTIC_CLAIM"]["result"] == "BLOCK"
    p002._assert_no_accepted_final(core, case)
