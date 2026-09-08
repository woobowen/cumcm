"""P0-01 black-box reproductions of RC7 Finalization block and HF22 fail-open.

These tests invoke the actual completion CLI. They freeze current RC7 observations; they do not
mutate the formal Skill, frozen 2017 artifacts, or technical state.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

# P0-01 fixtures after P0-03 predictive cross-bind.
FINALIZATION_BLOCK_GATE = "GATE_FINALIZATION"
FINALIZATION_OBSERVED_REASON = "RC_FINAL_TEST_EVALUATION_FAILED"
HF22_SEMANTIC_BLOCK_REASON = "RC_PREDICTIVE_SUPPORT_CONTRADICTS_SELECTED_OUTPUT"
HF22_OBSERVED_SEMANTIC_RESULT = "BLOCK"

REQUIRED_GATES_BEFORE_FINAL = [
    "GATE_PROBLEM_REQUIREMENT",
    "GATE_SOURCE_EVIDENCE",
    "GATE_DATA_SUFFICIENCY_PREFLIGHT",
    "GATE_COMPARISON_SELECTION",
    "GATE_RUN_ELIGIBILITY",
    "GATE_COMPATIBILITY_PORTFOLIO",
    "GATE_SEMANTIC_CLAIM",
    "GATE_AGGREGATE_CLAIM",
]


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def _run_controller(repo_root: Path, case: Path) -> tuple[subprocess.CompletedProcess, dict]:
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/finalize_fresh_c_validation.py"),
            "--case-root",
            str(case),
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=120 if sys.platform == "win32" else 30,
    )
    stdout = completed.stdout.strip()
    assert stdout, completed.stderr
    result = json.loads(stdout.splitlines()[-1])
    return completed, result


def _hf22_semantic(semantic: dict) -> dict:
    for claim in semantic["claims"]:
        if claim["requirement_id"] == "REQ-B":
            claim["claim_type"] = "PREDICTIVE"
            claim["support_predicates"] = {
                "scope_bounded": True,
                "validation_boundary_frozen": True,
                "held_out_test_valid": True,
            }
    return semantic


def _build_case(
    repo_root: Path,
    tmp_path: Path,
    *,
    model_fixture: str,
    semantic_adjust: Callable[[dict], dict] | None = None,
):
    probes = _module(
        repo_root / "tests/integration/test_actual_controller_black_box.py",
        f"p001_probes_{tmp_path.name}",
    )
    core = _module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        f"p001_core_{tmp_path.name}",
    )
    synthetic = _module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/synthetic_cases.py",
        f"p001_synthetic_{tmp_path.name}",
    )
    case = tmp_path / "case"
    core.initialize_case(case, "P0-01-REPRODUCTION", "general")
    core.write_json(case / "data/raw/input.json", {"x": [1, 2, 3]})
    raw_hash = core.file_hash(case / "data/raw/input.json")
    probes._accepted(
        core,
        case,
        "problem_requirements",
        {
            "contract_version": "requirement-evidence/v1",
            "case_id": "P0-01-REPRODUCTION",
            "requirements": probes._requirements(),
        },
    )
    probes._advance_to(core, case, "REQUIREMENTS_VALIDATED")
    probes._accepted(
        core,
        case,
        "research_plan",
        {
            "mode": "OFFLINE_PROJECT_ORIGINAL",
            "questions": ["p0-01"],
            "external_search": False,
        },
    )
    source = probes._source(raw_hash)
    probes._accepted(
        core,
        case,
        "source_ledger",
        {
            "contract_version": "requirement-evidence/v1",
            "sources": [source],
            "answer_access_status": "NOT_ACCESSED",
        },
    )
    probes._accepted(
        core,
        case,
        "data_sufficiency",
        {
            "contract_version": "data-sufficiency/v1",
            "requirements": probes._requirements(),
            "sources": [source],
            "acquisition_plans": [],
            "source_compositions": [],
            "coverage_mode_by_requirement": {
                "REQ-A": {"mode": "SINGLE_SOURCE", "source_id": "SRC-PROVIDED"},
                "REQ-B": {"mode": "SINGLE_SOURCE", "source_id": "SRC-PROVIDED"},
            },
            "aggregate_completion_claimed": False,
            "requirement_assessments": [
                probes._assessment("REQ-A"),
                probes._assessment("REQ-B"),
            ],
        },
    )
    probes._advance_to(core, case, "SOURCES_PLANNED")
    probes._accepted(
        core,
        case,
        "assumptions_and_symbols",
        {
            "assumptions": ["finite p0-01 fixture"],
            "symbols": {"x": "unitless"},
            "formulas": ["mean(x)"],
        },
    )
    probes._accepted(
        core,
        case,
        "data_audit",
        {"raw_immutable": True, "data_hashes": {"data/raw/input.json": raw_hash}},
    )
    core.advance_once(case)
    probes._accepted(
        core,
        case,
        "model_candidates",
        {
            "candidates": [
                {"candidate_id": "BASE", "baseline": True},
                {"candidate_id": "CAND", "baseline": False},
            ]
        },
    )
    core.advance_once(case)
    fixture = repo_root / model_fixture
    model = case / "models/controller_model.py"
    shutil.copyfile(fixture, model)
    code = synthetic._required_code_files(core) + [
        {
            "scope": "CASE_ROOT",
            "path": "models/controller_model.py",
            "repository_path": model_fixture,
            "sha256": core.file_hash(model),
        }
    ]
    commit = core.current_git_commit()
    splits = {"train": [1], "validation": [2], "test": [3]}
    inputs = {"data/raw/input.json": raw_hash}
    generated = "2026-09-06T00:00:00Z"
    freezes = synthetic._freezes(
        core,
        ["BASE", "CAND"],
        "loss",
        splits,
        "BASE",
        inputs,
        "one deterministic run per candidate",
        generated,
        code,
        commit,
    )
    freezes["seed_schedule"] = core.canonical_hash([20260905])
    probes._accepted(
        core,
        case,
        "experiment_plan",
        {
            "preregistered": True,
            "execution_prepared": True,
            "candidate_ids": ["BASE", "CAND"],
            "baseline_id": "BASE",
            "metric": "loss",
            "metric_direction": "MIN",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
            "selection_rule": "ARGMIN_THEN_ID",
            "random_seeds": [20260905],
            "splits": splits,
            "required_input_hashes": inputs,
            "required_code_files": code,
            "code_commit": commit,
            "trusted_freeze_registry": freezes,
            "stop_rule": "one deterministic run per candidate",
            "handoff_generated_at": generated,
            "scenario_hash": raw_hash,
        },
    )
    synthetic._write_output_contract_probe(core, case, ["REQ-A", "REQ-B"], metric="loss")
    core.advance_once(case)
    core.advance_once(case)
    for candidate_id in ("BASE", "CAND"):
        executed = core.execute_case_code(
            case,
            run_id=f"RUN-{candidate_id}-20260905",
            candidate_id=candidate_id,
            seed=20260905,
            code_path="models/controller_model.py",
            timeout_seconds=30,
        )
        assert executed["outcome"] == "SUCCESS", executed
    selection = probes._selection(core, raw_hash)
    semantic = probes._semantic(selection)
    if semantic_adjust is not None:
        semantic = semantic_adjust(semantic)
    probes._accepted(core, case, "requirement_selection", selection)
    probes._accepted(core, case, "semantic_claim_support", semantic)
    return core, case


def _gate_map(core, case: Path) -> dict[str, dict]:
    trace = core.load_json(case / "evidence/gate_execution_trace.json")
    return {item["gate_id"]: item for item in trace["gate_sequence"]}


def test_honest_development_output_blocks_at_finalization_without_test_payload(
    repo_root, tmp_path
) -> None:
    core, case = _build_case(
        repo_root,
        tmp_path,
        model_fixture="tests/fixtures/development_only_no_test_payload_model.py",
    )
    selected = core.load_json(case / "runs/RUN-CAND-20260905/output.json")
    assert "sealed_test_metrics_b64" not in selected
    assert selected["evaluation_boundary"] == "DEVELOPMENT_GROUPED_OOS"
    assert selected["held_out_test_valid"] is False

    completed, result = _run_controller(repo_root, case)
    assert completed.returncode != 0, completed.stderr
    assert result["status"] == "BLOCK_NATIVE_CONTRACTS"
    assert FINALIZATION_OBSERVED_REASON in result["reason_codes"]
    assert result.get("test_access_count", 0) == 0
    assert core.load_state(case)["state"] == "RUNNING"

    gates = _gate_map(core, case)
    observed = [item for item in REQUIRED_GATES_BEFORE_FINAL if item in gates]
    assert observed == REQUIRED_GATES_BEFORE_FINAL
    for gate_id in REQUIRED_GATES_BEFORE_FINAL:
        assert gates[gate_id]["result"] == "PASS", gate_id
    assert gates[FINALIZATION_BLOCK_GATE]["result"] == "BLOCK"
    assert FINALIZATION_OBSERVED_REASON in gates[FINALIZATION_BLOCK_GATE]["reason_codes"]
    assert "GATE_HANDOFF" not in gates
    handoff = core.load_json(case / core.ARTIFACT_PATHS["modeling_to_paper_handoff"])
    assert handoff["approved_by"] == []


def test_hf22_false_heldout_predicate_blocks_semantic_gate(repo_root, tmp_path) -> None:
    core, case = _build_case(
        repo_root,
        tmp_path,
        model_fixture="tests/fixtures/predictive_false_heldout_model.py",
        semantic_adjust=_hf22_semantic,
    )
    selected = core.load_json(case / "runs/RUN-CAND-20260905/output.json")
    semantic = core.read_artifact(case, "semantic_claim_support")["content"]
    predictive = next(item for item in semantic["claims"] if item["requirement_id"] == "REQ-B")
    assert predictive["claim_type"] == "PREDICTIVE"
    assert predictive["support_predicates"]["held_out_test_valid"] is True
    assert selected["evaluation_boundary"] == "DEVELOPMENT_GROUPED_OOS"
    assert selected["test_access_status"] == "NOT_AUTHORIZED"
    assert selected["test_access_count"] == 0
    assert selected["held_out_test_valid"] is False

    completed, result = _run_controller(repo_root, case)
    gates = _gate_map(core, case)
    assert gates["GATE_SEMANTIC_CLAIM"]["result"] == HF22_OBSERVED_SEMANTIC_RESULT
    assert HF22_SEMANTIC_BLOCK_REASON in gates["GATE_SEMANTIC_CLAIM"]["reason_codes"]
    assert HF22_SEMANTIC_BLOCK_REASON in result["reason_codes"]
    assert "GATE_AGGREGATE_CLAIM" not in gates
    assert "GATE_FINALIZATION" not in gates
    assert "GATE_HANDOFF" not in gates
    # Self-attested payload remains on Development output; it is not used as held-out proof.
    assert "sealed_test_metrics_b64" in selected
    assert completed.returncode != 0, (completed.stderr, result)
    assert result["status"] == "BLOCK_NATIVE_CONTRACTS"
    assert result.get("test_access_count", 0) == 0
    assert core.load_state(case)["state"] == "RUNNING"
    handoff = core.load_json(case / core.ARTIFACT_PATHS["modeling_to_paper_handoff"])
    assert handoff["approved_by"] == []
