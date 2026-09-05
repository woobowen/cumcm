"""Frozen prosecutor attacks against the actual completion-controller boundary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

MATRIX = Path("evals/results/phase-004c4/frozen_adversarial_controller_probe_matrix.json")
PROBES = {
    "AP-001-SELECTION-COMPARISON-SPLIT-BRAIN": (
        "GATE_COMPARISON_SELECTION",
        "RC_SELECTION_COMPARISON_DECISION_MISMATCH",
    ),
    "AP-002-LATE-TEST-DECODE-UNTRACED-MUTATION": (
        "GATE_FINALIZATION",
        "RC_SEALED_TEST_PAYLOAD_INVALID",
    ),
    "AP-003-BLOCK-PATH-SEALS-MANIFESTS": (
        "GATE_COMPATIBILITY_PORTFOLIO",
        "RC_SELECTION_PORTFOLIO_HASHES_MISSING",
    ),
    "AP-004-SCENARIO-HASH-NOT-RUN-MANIFEST-BOUND": (
        "GATE_COMPATIBILITY_PORTFOLIO",
        "RC_SELECTION_SCENARIO_NOT_CAPTURE_BOUND",
    ),
    "AP-005-POLICY-EVIDENCE-SELF-ATTESTATION": (
        "GATE_SEMANTIC_CLAIM",
        "RC_POLICY_OUTPUT_EVIDENCE_MISSING",
    ),
}


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def _builders(repo_root: Path, suffix: str):
    neutral = _module(
        repo_root / "tests/integration/test_actual_controller_neutral_e2e.py",
        f"adversarial_neutral_{suffix}",
    )
    frozen = _module(
        repo_root / "tests/integration/test_actual_controller_black_box.py",
        f"adversarial_frozen_{suffix}",
    )
    return neutral, frozen


def _assert_structured_block(completed, *, gate_id: str, reason_code: str, core, case: Path):
    assert completed.returncode != 0
    assert completed.stdout.strip(), completed.stderr
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    assert result["status"] == "BLOCK_NATIVE_CONTRACTS"
    assert reason_code in result["reason_codes"]
    assert core.load_state(case)["state"] == "RUNNING"
    trace_path = case / "evidence/gate_execution_trace.json"
    assert trace_path.is_file()
    trace = core.load_json(trace_path)
    assert trace["final_disposition"] == "BLOCK"
    assert trace["gate_sequence"][-1]["gate_id"] == gate_id
    return result


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_frozen_adversarial_probe_matrix_is_complete_and_hash_bound(repo_root) -> None:
    matrix = json.loads((repo_root / MATRIX).read_text(encoding="utf-8"))
    payload = dict(matrix)
    matrix_hash = payload.pop("matrix_hash")
    assert _canonical_hash(payload) == matrix_hash
    assert matrix["subject_commit"] == "557f0972e14773fdf362c9549adb7d54c5abae6b"
    assert matrix["probe_count"] == len(PROBES) == 5
    assert [item["probe_id"] for item in matrix["probes"]] == list(PROBES)
    assert (
        matrix["test_sha256"]
        == hashlib.sha256((repo_root / matrix["test_file"]).read_bytes()).hexdigest()
    )
    assert (
        matrix["auditor_report_sha256"]
        == hashlib.sha256((repo_root / matrix["auditor_report_file"]).read_bytes()).hexdigest()
    )


def test_split_brain_selection_cannot_finalize_a_different_run(repo_root, tmp_path) -> None:
    neutral, frozen = _builders(repo_root, tmp_path.name)
    core, case = neutral._build_data_sufficiency_case(repo_root, tmp_path)
    selection = core.read_artifact(case, "requirement_selection")["content"]
    semantic = core.read_artifact(case, "semantic_claim_support")["content"]
    selected_run = "RUN-CAND-20260906"
    for requirement in selection["requirements"]:
        requirement["selected_run_ids"] = [selected_run]
    for requirement_id in selection["selection"]["requirement_to_run_map"]:
        selection["selection"]["requirement_to_run_map"][requirement_id] = [selected_run]
    for claim in semantic["claims"]:
        claim["selected_run_ids"] = [selected_run]
    for output in semantic["outputs"]:
        output["owner_run_id"] = selected_run
    neutral._accepted(core, case, "requirement_selection", selection)
    neutral._accepted(core, case, "semantic_claim_support", semantic)
    frozen._sync_bound_hashes(core, case)

    completed, _ = neutral._run_controller(repo_root, case)
    _assert_structured_block(
        completed,
        gate_id=PROBES["AP-001-SELECTION-COMPARISON-SPLIT-BRAIN"][0],
        reason_code=PROBES["AP-001-SELECTION-COMPARISON-SPLIT-BRAIN"][1],
        core=core,
        case=case,
    )


def test_invalid_selected_test_payload_fails_closed_before_durable_output(
    repo_root, tmp_path
) -> None:
    neutral, _ = _builders(repo_root, tmp_path.name)
    core, case = neutral._build_data_sufficiency_case(repo_root, tmp_path)
    capture_path = case / "runs/RUN-BASE-20260906/execution_capture.json"
    capture = core.load_json(capture_path)
    output_path = case / capture["output"]["path"]
    output = core.load_json(output_path)
    output["sealed_test_metrics_b64"] = "%%%"
    core.write_json(output_path, output)
    capture["output"]["sha256"] = core.file_hash(output_path)
    core.write_json(capture_path, capture)
    assert not list(case.glob("runs/*/manifest.json"))

    completed, _ = neutral._run_controller(repo_root, case)
    _assert_structured_block(
        completed,
        gate_id=PROBES["AP-002-LATE-TEST-DECODE-UNTRACED-MUTATION"][0],
        reason_code=PROBES["AP-002-LATE-TEST-DECODE-UNTRACED-MUTATION"][1],
        core=core,
        case=case,
    )
    assert not list(case.glob("runs/*/manifest.json"))
    assert not (case / "evidence/selection_before_test_access.json").exists()
    assert not (case / "evidence/selected_test_access.json").exists()


def test_rejected_portfolio_does_not_seal_manifests(repo_root, tmp_path) -> None:
    neutral, frozen = _builders(repo_root, tmp_path.name)
    core, case = neutral._build_portfolio_case(repo_root, tmp_path)
    selection = core.read_artifact(case, "requirement_selection")["content"]
    selection["selection"]["shared_input_hashes"] = []
    neutral._accepted(core, case, "requirement_selection", selection)
    frozen._sync_bound_hashes(core, case)
    assert not list(case.glob("runs/*/manifest.json"))

    completed, _ = neutral._run_controller(repo_root, case)
    _assert_structured_block(
        completed,
        gate_id=PROBES["AP-003-BLOCK-PATH-SEALS-MANIFESTS"][0],
        reason_code=PROBES["AP-003-BLOCK-PATH-SEALS-MANIFESTS"][1],
        core=core,
        case=case,
    )
    assert not list(case.glob("runs/*/manifest.json"))


def test_scenario_hash_must_be_bound_by_execution_capture_and_manifest(repo_root, tmp_path) -> None:
    neutral, frozen = _builders(repo_root, tmp_path.name)
    core, case = neutral._build_portfolio_case(repo_root, tmp_path)
    forged = "c" * 64
    plan = core.read_artifact(case, "experiment_plan")["content"]
    selection = core.read_artifact(case, "requirement_selection")["content"]
    semantic = core.read_artifact(case, "semantic_claim_support")["content"]
    plan["scenario_hash"] = forged
    selection["selection"]["shared_scenario_hashes"] = [forged]
    for run in selection["runs"]:
        run["scenario_hash"] = forged
    for run in semantic["runs"]:
        run["scenario_hash"] = forged
    for bridge in selection["selection"]["dependency_bridges"]:
        bridge["scenario_hash"] = forged
        body = {key: value for key, value in bridge.items() if key != "lineage_hash"}
        bridge["lineage_hash"] = core.canonical_hash(body)
    neutral._accepted(core, case, "experiment_plan", plan)
    neutral._accepted(core, case, "requirement_selection", selection)
    neutral._accepted(core, case, "semantic_claim_support", semantic)
    frozen._sync_bound_hashes(core, case)

    completed, _ = neutral._run_controller(repo_root, case)
    _assert_structured_block(
        completed,
        gate_id=PROBES["AP-004-SCENARIO-HASH-NOT-RUN-MANIFEST-BOUND"][0],
        reason_code=PROBES["AP-004-SCENARIO-HASH-NOT-RUN-MANIFEST-BOUND"][1],
        core=core,
        case=case,
    )


def test_policy_claim_requires_run_output_policy_evidence(repo_root, tmp_path) -> None:
    neutral, frozen = _builders(repo_root, tmp_path.name)
    core, case = frozen._build_running_case(repo_root, tmp_path)
    semantic = core.read_artifact(case, "semantic_claim_support")["content"]
    claim = semantic["claims"][0]
    claim["claim_type"] = "POLICY_EVALUATION"
    claim["comparator_ids"] = ["COMP-POLICY-1"]
    claim["support_predicates"].update(
        policy_executed=True,
        policy_exposure_positive=True,
        benefit_recorded=True,
        cost_recorded=True,
    )
    semantic["comparators"] = [{"comparator_id": "COMP-POLICY-1"}]
    neutral._accepted(core, case, "semantic_claim_support", semantic)
    frozen._sync_bound_hashes(core, case)

    completed, _ = neutral._run_controller(repo_root, case)
    _assert_structured_block(
        completed,
        gate_id=PROBES["AP-005-POLICY-EVIDENCE-SELF-ATTESTATION"][0],
        reason_code=PROBES["AP-005-POLICY-EVIDENCE-SELF-ATTESTATION"][1],
        core=core,
        case=case,
    )
