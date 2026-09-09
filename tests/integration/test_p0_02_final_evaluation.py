"""P0-02 Final evaluation authorization: legal path and fail-closed attacks.

All tests use the actual `evaluate-final` CLI and/or `finalize_fresh_c_validation.py`.
They do not mock those entrypoints, reuse Development metrics as Final, or edit
frozen 2017 artifacts.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

AUTHORIZED_FIXTURE = "tests/fixtures/authorized_final_eval_model.py"
SELECTED_RUN = "RUN-CAND-20260905"
NON_SELECTED_RUN = "RUN-BASE-20260905"
LEDGER = "evidence/final_evaluation_ledger.json"
CASE_CLI = ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def _p001(repo_root: Path, tmp_path: Path):
    return _module(
        repo_root / "tests/integration/test_p0_01_finalization_hf22_reproduction.py",
        f"p002_p001_{tmp_path.name}",
    )


def _build_authorized(repo_root: Path, tmp_path: Path):
    p001 = _p001(repo_root, tmp_path)
    return p001._build_case(repo_root, tmp_path, model_fixture=AUTHORIZED_FIXTURE)


def _parse(completed: subprocess.CompletedProcess) -> dict:
    stdout = completed.stdout.strip()
    assert stdout, completed.stderr
    return json.loads(stdout.splitlines()[-1])


def _decision(core, case: Path) -> tuple[dict, str]:
    plan = core.read_artifact(case, "experiment_plan")["content"]
    attempts = core._development_attempt_registry(case, plan)
    selected = core.select_development_candidate(attempts, plan)
    return selected, core.canonical_hash(selected)


def _evaluate_final(repo_root: Path, case: Path, run_id: str, decision_hash: str):
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / CASE_CLI),
            "evaluate-final",
            "--case-root",
            str(case),
            "--run-id",
            run_id,
            "--decision-hash",
            decision_hash,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return completed, _parse(completed)


def _assert_no_accepted_final(core, case: Path) -> None:
    assert core.load_state(case)["state"] == "RUNNING"
    assert not list(case.glob("runs/*/manifest.json"))
    assert not (case / "evidence/selected_test_access.json").exists()
    handoff = core.load_json(case / core.ARTIFACT_PATHS["modeling_to_paper_handoff"])
    assert handoff["approved_by"] == []


def test_authorized_controller_path_reaches_handoff(repo_root, tmp_path) -> None:
    p001 = _p001(repo_root, tmp_path)
    core, case = _build_authorized(repo_root, tmp_path)
    selected_output = core.load_json(case / f"runs/{SELECTED_RUN}/output.json")
    capture = core.load_json(case / f"runs/{SELECTED_RUN}/execution_capture.json")
    development_hash = capture["output"]["sha256"]
    assert "sealed_test_metrics_b64" not in selected_output

    completed, result = p001._run_controller(repo_root, case)
    assert completed.returncode == 0, (completed.stderr, result)
    assert result["status"] == "PASS_NATIVE_CONTRACTS"
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    assert result["test_access_count"] == 1
    gates = p001._gate_map(core, case)
    assert gates["GATE_FINALIZATION"]["result"] == "PASS"
    assert gates["GATE_HANDOFF"]["result"] == "PASS"

    assert core.file_hash(case / f"runs/{SELECTED_RUN}/output.json") == development_hash
    assert "sealed_test_metrics_b64" not in core.load_json(
        case / f"runs/{SELECTED_RUN}/output.json"
    )
    ledger = core.load_json(case / LEDGER)
    assert ledger["count"] == 1
    assert ledger["max_count"] == 1
    assert ledger["used_for_selection"] is False
    assert ledger["run_id"] == SELECTED_RUN
    access = core.load_json(case / "evidence/selected_test_access.json")
    assert access["count"] == 1
    assert access["used_for_selection"] is False
    assert access["test_metrics"] == {"selected": "CAND"}


def test_evaluate_final_cli_then_controller_reuses_ledger(repo_root, tmp_path) -> None:
    p001 = _p001(repo_root, tmp_path)
    core, case = _build_authorized(repo_root, tmp_path)
    _, decision_hash = _decision(core, case)
    completed, payload = _evaluate_final(repo_root, case, SELECTED_RUN, decision_hash)
    assert completed.returncode == 0, (completed.stderr, payload)
    assert payload["command"] == "evaluate-final"
    assert payload["status"] == "PASS"
    assert payload["result"]["run_id"] == SELECTED_RUN
    first_ledger = core.load_json(case / LEDGER)
    assert first_ledger["count"] == 1

    completed, result = p001._run_controller(repo_root, case)
    assert completed.returncode == 0, (completed.stderr, result)
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    second_ledger = core.load_json(case / LEDGER)
    assert second_ledger["authorization_hash"] == first_ledger["authorization_hash"]
    assert second_ledger["count"] == 1


def test_premature_evaluate_final_blocks(repo_root, tmp_path) -> None:
    core, case = _build_authorized(repo_root, tmp_path)
    shutil.rmtree(case / f"runs/{SELECTED_RUN}")
    completed, payload = _evaluate_final(repo_root, case, NON_SELECTED_RUN, "a" * 64)
    assert completed.returncode != 0
    assert "RC_FINAL_TEST_PREMATURE" in payload["reason_codes"]
    assert not (case / LEDGER).exists()
    _assert_no_accepted_final(core, case)


def test_non_selected_run_evaluate_final_blocks(repo_root, tmp_path) -> None:
    core, case = _build_authorized(repo_root, tmp_path)
    _, decision_hash = _decision(core, case)
    completed, payload = _evaluate_final(repo_root, case, NON_SELECTED_RUN, decision_hash)
    assert completed.returncode != 0
    assert "RC_FINAL_TEST_RUN_NOT_SELECTED" in payload["reason_codes"]
    assert not (case / LEDGER).exists()
    _assert_no_accepted_final(core, case)


def test_repeat_evaluate_final_blocks(repo_root, tmp_path) -> None:
    core, case = _build_authorized(repo_root, tmp_path)
    _, decision_hash = _decision(core, case)
    first, first_payload = _evaluate_final(repo_root, case, SELECTED_RUN, decision_hash)
    assert first.returncode == 0, first_payload
    second, second_payload = _evaluate_final(repo_root, case, SELECTED_RUN, decision_hash)
    assert second.returncode != 0
    assert "RC_FINAL_TEST_ALREADY_ACCESSED" in second_payload["reason_codes"]
    ledger = core.load_json(case / LEDGER)
    assert ledger["count"] == 1
    assert not (case / "evidence/selected_test_access.json").exists()


def test_wrong_decision_hash_blocks(repo_root, tmp_path) -> None:
    core, case = _build_authorized(repo_root, tmp_path)
    completed, payload = _evaluate_final(repo_root, case, SELECTED_RUN, "ab" * 32)
    assert completed.returncode != 0
    assert "RC_FINAL_TEST_AUTHORIZATION_HASH_MISMATCH" in payload["reason_codes"]
    assert not (case / LEDGER).exists()
    _assert_no_accepted_final(core, case)


def test_tampered_payload_hash_blocks_controller(repo_root, tmp_path) -> None:
    p001 = _p001(repo_root, tmp_path)
    core, case = _build_authorized(repo_root, tmp_path)
    _, decision_hash = _decision(core, case)
    completed, payload = _evaluate_final(repo_root, case, SELECTED_RUN, decision_hash)
    assert completed.returncode == 0, payload
    sidecar = case / f"runs/{SELECTED_RUN}/sealed_test.json"
    mutated = core.load_json(sidecar)
    mutated["sealed_test_payload_sha256"] = "b" * 64
    core.write_json(sidecar, mutated)
    completed, result = p001._run_controller(repo_root, case)
    assert completed.returncode != 0
    assert result["status"] == "BLOCK_NATIVE_CONTRACTS"
    assert "RC_FINAL_TEST_PAYLOAD_HASH_MISMATCH" in result["reason_codes"]
    gates = p001._gate_map(core, case)
    assert gates["GATE_FINALIZATION"]["result"] == "BLOCK"
    assert "GATE_HANDOFF" not in gates
    _assert_no_accepted_final(core, case)


def test_development_output_mutation_blocks(repo_root, tmp_path) -> None:
    core, case = _build_authorized(repo_root, tmp_path)
    _, decision_hash = _decision(core, case)
    output_path = case / f"runs/{SELECTED_RUN}/output.json"
    output = core.load_json(output_path)
    output["limitations"].append("silent development mutation")
    core.write_json(output_path, output)
    completed, payload = _evaluate_final(repo_root, case, SELECTED_RUN, decision_hash)
    assert completed.returncode != 0
    assert "RC_EXECUTION_CAPTURE_OUTPUT_MISMATCH" in payload["reason_codes"]
    assert not (case / LEDGER).exists()
    _assert_no_accepted_final(core, case)


def test_self_attested_development_payload_blocks_controller(repo_root, tmp_path) -> None:
    p001 = _p001(repo_root, tmp_path)
    probes = _module(
        repo_root / "tests/integration/test_actual_controller_black_box.py",
        f"p002_self_attest_{tmp_path.name}",
    )
    core, case = probes._build_running_case(repo_root, tmp_path)
    selected = core.load_json(case / f"runs/{SELECTED_RUN}/output.json")
    assert "sealed_test_metrics_b64" in selected
    completed, result = p001._run_controller(repo_root, case)
    assert completed.returncode != 0
    assert "RC_FINAL_TEST_SELF_ATTESTED_IN_DEVELOPMENT_OUTPUT" in result["reason_codes"]
    gates = p001._gate_map(core, case)
    assert gates["GATE_FINALIZATION"]["result"] == "BLOCK"
    assert "GATE_HANDOFF" not in gates
    assert not (case / LEDGER).exists()
    _assert_no_accepted_final(core, case)
