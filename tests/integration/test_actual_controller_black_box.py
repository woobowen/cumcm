"""Frozen black-box attacks against the real fresh-case completion controller."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

MATRIX = Path("evals/results/phase-004c4/frozen_actual_controller_probe_matrix.json")
SENTINEL = "opaque-probe-value-771"
HEX_A = "a" * 64
HEX_B = "b" * 64
PROBES = {
    "AC-001-EXTERNAL-DATA-FORBIDDEN": (
        "GATE_DATA_SUFFICIENCY_PREFLIGHT",
        "RC_EXTERNAL_DATA_POLICY_FORBIDDEN",
    ),
    "AC-002-ACQUISITION-PLAN-INCOMPLETE": (
        "GATE_DATA_SUFFICIENCY_PREFLIGHT",
        "RC_DATA_ACQUISITION_PLAN_INCOMPLETE",
    ),
    "AC-003-SOURCE-SCOPE-NOT-CONJUNCTIVE": (
        "GATE_DATA_SUFFICIENCY_PREFLIGHT",
        "RC_DATA_SOURCE_COMPOSITION_UNREGISTERED",
    ),
    "AC-004-DEPENDENCY-SPLIT-WITHOUT-BRIDGE": (
        "GATE_COMPATIBILITY_PORTFOLIO",
        "RC_SELECTION_DEPENDENCY_BRIDGE_MISSING",
    ),
    "AC-005-PORTFOLIO-HASHES-MISSING": (
        "GATE_COMPATIBILITY_PORTFOLIO",
        "RC_SELECTION_PORTFOLIO_HASHES_MISSING",
    ),
    "AC-006-PORTFOLIO-HASH-MISMATCH": (
        "GATE_COMPATIBILITY_PORTFOLIO",
        "RC_SELECTION_PORTFOLIO_HASH_MISMATCH",
    ),
    "AC-007-SELECTED-RUN-INELIGIBLE": (
        "GATE_RUN_ELIGIBILITY",
        "RC_REQUIREMENT_SELECTED_RUN_INVALID_STATUS",
    ),
    "AC-008-CLAIM-REQUIREMENT-NOT-COVERED": (
        "GATE_SEMANTIC_CLAIM",
        "RC_REQUIREMENT_SELECTED_RUN_SEMANTIC_MISMATCH",
    ),
    "AC-009-CLAIM-OUTPUT-NOT-OWNED": (
        "GATE_SEMANTIC_CLAIM",
        "RC_REQUIREMENT_SELECTED_OUTPUT_NOT_OWNED",
    ),
    "AC-010-CLAIM-METRIC-MISSING": (
        "GATE_SEMANTIC_CLAIM",
        "RC_CLAIM_METRIC_BINDING_MISSING",
    ),
    "AC-011-CLAIM-SCOPE-UNBOUNDED": (
        "GATE_SEMANTIC_CLAIM",
        "RC_CLAIM_SCOPE_UNBOUNDED",
    ),
    "AC-012-AGGREGATE-MAPPING-WRONG": (
        "GATE_AGGREGATE_CLAIM",
        "RC_AGGREGATE_CLAIM_MAPPING_INVALID",
    ),
    "AC-013-COMPATIBILITY-UNKNOWN-NONBIJECTION": (
        "GATE_COMPATIBILITY_PORTFOLIO",
        "RC_EVIDENCE_COMPATIBILITY_KIND_INVALID",
    ),
}


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def _accepted(core, case: Path, key: str, content: dict) -> None:
    core.write_json(case / core.ARTIFACT_PATHS[key], core.artifact(key, content))


def _advance_to(core, case: Path, target: str) -> None:
    while core.load_state(case)["state"] != target:
        core.advance_once(case)


def _requirements() -> list[dict]:
    return [
        {
            "requirement_id": requirement_id,
            "role": "PRIMARY",
            "required_evidence_classes": ["PROVIDED_EMPIRICAL"],
            "allowed_evidence_classes": ["PROVIDED_EMPIRICAL"],
            "minimum_data_fields": ["x"],
            "required_time_scope": ["FROZEN_SCOPE"],
            "required_entity_scope": ["ENTITY-SET"],
            "external_data_allowed": False,
            "external_data_required": False,
            "simulation_substitution_allowed": False,
            "partial_completion_allowed": False,
            "dependency_requirements": [],
            "completion_rule": "ALL_REQUIRED_EVIDENCE",
        }
        for requirement_id in ("REQ-A", "REQ-B")
    ]


def _source(source_hash: str) -> dict:
    return {
        "source_id": "SRC-PROVIDED",
        "supports_requirement_ids": ["REQ-A", "REQ-B"],
        "evidence_class": "PROVIDED_EMPIRICAL",
        "provenance": "PROJECT_ORIGINAL_TEST_INPUT",
        "authority": "FIRST_PARTY_FIXTURE",
        "retrieval_time": "2026-09-05T00:00:00Z",
        "license_or_usage_status": "ALLOWED",
        "geographic_scope": [],
        "time_scope": ["FROZEN_SCOPE"],
        "entity_scope": ["ENTITY-SET"],
        "field_schema": ["x"],
        "hash": source_hash,
        "freshness": "CURRENT_FOR_SCOPE",
        "limitations": [SENTINEL],
    }


def _assessment(requirement_id: str) -> dict:
    return {
        "requirement_id": requirement_id,
        "data_sufficiency_status": "SUFFICIENT",
        "missing_fields": [],
        "missing_entities": [],
        "missing_time_scope": [],
        "candidate_sources": ["SRC-PROVIDED"],
        "acquisition_cost": "NONE",
        "acquisition_time": "NONE",
        "allowed_substitutions": [],
        "forbidden_substitutions": ["SIMULATION"],
        "affected_downstream_stages": [],
    }


def _selection(core, raw_hash: str) -> dict:
    input_hash = core.canonical_hash([raw_hash])
    runs = []
    for candidate_id in ("BASE", "CAND"):
        run_id = f"RUN-{candidate_id}-20260905"
        runs.append(
            {
                "run_id": run_id,
                "outcome": "SUCCESS",
                "sealed": True,
                "current": True,
                "supported_requirement_ids": ["REQ-A", "REQ-B"],
                "selected_output_ids": ["OUT-REQ-A", "OUT-REQ-B"],
                "metric_ids": ["loss"],
                "input_hash": input_hash,
                "scenario_hash": raw_hash,
                "configuration_hash": core.canonical_hash(
                    {"candidate_id": candidate_id, "seed": 20260905}
                ),
                "policy_exposure": 1,
            }
        )
    return {
        "contract_version": "requirement-selection/v1",
        "requirements": [
            {
                "requirement_id": requirement_id,
                "candidate_run_ids": [item["run_id"] for item in runs],
                "selection_metric": "loss",
                "selection_direction": "MIN",
                "feasibility_gate": "PASS",
                "selected_run_ids": [
                    "RUN-BASE-20260905" if requirement_id == "REQ-A" else "RUN-CAND-20260905"
                ],
                "selected_output_ids": [f"OUT-{requirement_id}"],
                "dependency_requirements": [],
                "dependency_bindings": [],
                "cross_requirement_constraints": [],
                "support_predicates": {"metric_bound": True},
            }
            for requirement_id in ("REQ-A", "REQ-B")
        ],
        "runs": runs,
        "selection": {
            "selection_mode": "PER_REQUIREMENT",
            "requirement_to_run_map": {
                "REQ-A": ["RUN-BASE-20260905"],
                "REQ-B": ["RUN-CAND-20260905"],
            },
            "requirement_to_output_map": {
                "REQ-A": ["OUT-REQ-A"],
                "REQ-B": ["OUT-REQ-B"],
            },
            "shared_input_hashes": [input_hash],
            "shared_scenario_hashes": [raw_hash],
            "compatibility_checks": ["INPUT", "SCENARIO", "CONSTRAINTS"],
            "compatibility": {
                "kind": "RUN_PORTFOLIO_V1",
                "version": "compatibility/v1",
                "ordered_ids": ["REQ-A", "REQ-B"],
                "permuted_ids": ["REQ-B", "REQ-A"],
            },
            "dependency_bridges": [],
            "cross_requirement_constraints": [],
            "aggregate_objective": "DECLARED_TRADEOFF",
            "tradeoff_rule": "REQUIREMENT_LOCAL_METRICS",
            "limitations": ["Project-original black-box fixture."],
        },
    }


def _semantic(selection: dict) -> dict:
    runs = copy.deepcopy(selection["runs"])
    outputs = [
        {
            "output_id": "OUT-REQ-A",
            "requirement_id": "REQ-A",
            "owner_run_id": "RUN-BASE-20260905",
            "metric_ids": ["loss"],
        },
        {
            "output_id": "OUT-REQ-B",
            "requirement_id": "REQ-B",
            "owner_run_id": "RUN-CAND-20260905",
            "metric_ids": ["loss"],
        },
    ]
    claims = []
    for requirement_id, run_id in (
        ("REQ-A", "RUN-BASE-20260905"),
        ("REQ-B", "RUN-CAND-20260905"),
    ):
        claims.append(
            {
                "claim_id": f"CLAIM-{requirement_id}",
                "requirement_id": requirement_id,
                "claim_type": "DESCRIPTIVE",
                "statement": f"Bounded statement for {requirement_id}.",
                "scope": {
                    "fields": ["x"],
                    "time": ["FROZEN_SCOPE"],
                    "entities": ["ENTITY-SET"],
                },
                "evidence_class": "PROVIDED_EMPIRICAL",
                "selected_run_ids": [run_id],
                "selected_output_ids": [f"OUT-{requirement_id}"],
                "metric_ids": ["loss"],
                "comparator_ids": [],
                "support_predicates": {"scope_bounded": True},
                "uncertainty": {"status": "BOUNDED"},
                "counter_evidence": [],
                "limitations": ["Project-original black-box fixture."],
                "claim_strength": "BOUNDED",
                "status": "SUPPORTED",
            }
        )
    return {
        "contract_version": "claim-evidence/v3",
        "claims": claims,
        "runs": runs,
        "outputs": outputs,
        "comparators": [],
        "validation": {"counter_evidence_detected": False},
        "aggregate": {
            "primary_requirement_ids": ["REQ-A", "REQ-B"],
            "supported_requirement_ids": ["REQ-B", "REQ-A"],
            "requirement_claim_ids": {
                "REQ-A": "CLAIM-REQ-A",
                "REQ-B": "CLAIM-REQ-B",
            },
        },
    }


def _build_running_case(repo_root: Path, tmp_path: Path):
    core = _module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        f"actual_controller_core_{tmp_path.name}",
    )
    synthetic = _module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/synthetic_cases.py",
        f"actual_controller_synthetic_{tmp_path.name}",
    )
    case = tmp_path / "case"
    core.initialize_case(case, "ACTUAL-CONTROLLER-PROBE", "general")
    core.write_json(case / "data/raw/input.json", {"x": [1, 2, 3]})
    raw_hash = core.file_hash(case / "data/raw/input.json")
    requirements = _requirements()
    _accepted(
        core,
        case,
        "problem_requirements",
        {
            "contract_version": "requirement-evidence/v1",
            "case_id": "ACTUAL-CONTROLLER-PROBE",
            "requirements": requirements,
        },
    )
    _advance_to(core, case, "REQUIREMENTS_VALIDATED")
    _accepted(
        core,
        case,
        "research_plan",
        {"mode": "OFFLINE_PROJECT_ORIGINAL", "questions": ["generic"], "external_search": False},
    )
    source = _source(raw_hash)
    _accepted(
        core,
        case,
        "source_ledger",
        {
            "contract_version": "requirement-evidence/v1",
            "sources": [source],
            "answer_access_status": "NOT_ACCESSED",
        },
    )
    _accepted(
        core,
        case,
        "data_sufficiency",
        {
            "contract_version": "data-sufficiency/v1",
            "requirements": requirements,
            "sources": [source],
            "acquisition_plans": [],
            "source_compositions": [],
            "coverage_mode_by_requirement": {
                "REQ-A": {"mode": "SINGLE_SOURCE", "source_id": "SRC-PROVIDED"},
                "REQ-B": {"mode": "SINGLE_SOURCE", "source_id": "SRC-PROVIDED"},
            },
            "aggregate_completion_claimed": False,
            "requirement_assessments": [_assessment("REQ-A"), _assessment("REQ-B")],
        },
    )
    _advance_to(core, case, "SOURCES_PLANNED")
    _accepted(
        core,
        case,
        "assumptions_and_symbols",
        {"assumptions": ["finite fixture"], "symbols": {"x": "unitless"}, "formulas": ["mean(x)"]},
    )
    _accepted(
        core,
        case,
        "data_audit",
        {"raw_immutable": True, "data_hashes": {"data/raw/input.json": raw_hash}},
    )
    core.advance_once(case)
    candidates = [
        {"candidate_id": "BASE", "baseline": True},
        {"candidate_id": "CAND", "baseline": False},
    ]
    _accepted(core, case, "model_candidates", {"candidates": candidates})
    core.advance_once(case)
    fixture = repo_root / "tests/fixtures/actual_controller_model.py"
    model = case / "models/controller_model.py"
    shutil.copyfile(fixture, model)
    code = synthetic._required_code_files(core) + [
        {
            "scope": "CASE_ROOT",
            "path": "models/controller_model.py",
            "repository_path": "tests/fixtures/actual_controller_model.py",
            "sha256": core.file_hash(model),
        }
    ]
    commit = core.current_git_commit()
    splits = {"train": [1], "validation": [2], "test": [3]}
    inputs = {"data/raw/input.json": raw_hash}
    generated = "2026-09-05T00:00:00Z"
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
    _accepted(
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
        core.execute_case_code(
            case,
            run_id=f"RUN-{candidate_id}-20260905",
            candidate_id=candidate_id,
            seed=20260905,
            code_path="models/controller_model.py",
            timeout_seconds=30,
        )
    selection = _selection(core, raw_hash)
    semantic = _semantic(selection)
    _accepted(core, case, "requirement_selection", selection)
    _accepted(core, case, "semantic_claim_support", semantic)
    return core, case


def _sync_bound_hashes(core, case: Path) -> None:
    state = core.load_json(case / "case_state.json")
    for relative in list(state["evidence_bindings"]):
        path = case / relative
        if path.is_file():
            state["evidence_bindings"][relative] = core.file_hash(path)
    core.write_json(case / "case_state.json", state)
    core.load_state(case)


def _apply_mutation(core, case: Path, probe_id: str) -> None:
    requirements_record = core.read_artifact(case, "problem_requirements")["content"]
    ledger = core.read_artifact(case, "source_ledger")["content"]
    sufficiency = core.read_artifact(case, "data_sufficiency")["content"]
    selection = core.read_artifact(case, "requirement_selection")["content"]
    semantic = core.read_artifact(case, "semantic_claim_support")["content"]
    if probe_id == "AC-001-EXTERNAL-DATA-FORBIDDEN":
        requirements_record["requirements"][0]["required_evidence_classes"] = ["ACQUIRED_EMPIRICAL"]
        requirements_record["requirements"][0]["allowed_evidence_classes"] = ["ACQUIRED_EMPIRICAL"]
        ledger["sources"][0]["evidence_class"] = "ACQUIRED_EMPIRICAL"
        sufficiency["requirements"] = requirements_record["requirements"]
        sufficiency["sources"] = ledger["sources"]
    elif probe_id == "AC-002-ACQUISITION-PLAN-INCOMPLETE":
        requirement = requirements_record["requirements"][0]
        requirement["external_data_allowed"] = True
        requirement["external_data_required"] = True
        requirement["required_evidence_classes"] = ["ACQUIRED_EMPIRICAL"]
        requirement["allowed_evidence_classes"] = ["ACQUIRED_EMPIRICAL"]
        ledger["sources"] = []
        sufficiency["requirements"] = requirements_record["requirements"]
        sufficiency["sources"] = []
        sufficiency["acquisition_plans"] = [
            {"requirement_id": "REQ-A", "status": "PLANNED", "provenance_plan": SENTINEL}
        ]
    elif probe_id == "AC-003-SOURCE-SCOPE-NOT-CONJUNCTIVE":
        first = copy.deepcopy(ledger["sources"][0])
        first.update(source_id="SRC-FIELD-TIME", entity_scope=["OTHER"])
        second = copy.deepcopy(ledger["sources"][0])
        second.update(source_id="SRC-ENTITY", field_schema=["y"], time_scope=["OTHER"])
        ledger["sources"] = [first, second]
        sufficiency["sources"] = ledger["sources"]
        sufficiency["source_compositions"] = []
    elif probe_id == "AC-004-DEPENDENCY-SPLIT-WITHOUT-BRIDGE":
        selection["requirements"][1]["dependency_requirements"] = ["REQ-A"]
        selection["selection"]["dependency_bridges"] = []
    elif probe_id == "AC-005-PORTFOLIO-HASHES-MISSING":
        selection["selection"]["selection_mode"] = "JOINT_PORTFOLIO"
        selection["selection"]["shared_input_hashes"] = []
        selection["selection"]["shared_scenario_hashes"] = []
        for run in selection["runs"]:
            run.pop("input_hash")
            run.pop("scenario_hash")
    elif probe_id == "AC-006-PORTFOLIO-HASH-MISMATCH":
        selection["selection"]["selection_mode"] = "JOINT_PORTFOLIO"
        selection["selection"]["shared_input_hashes"] = [HEX_B]
        selection["selection"]["shared_scenario_hashes"] = [HEX_B]
    elif probe_id == "AC-007-SELECTED-RUN-INELIGIBLE":
        semantic["runs"][0].update(outcome="FAILED", sealed=False, current=False)
    elif probe_id == "AC-008-CLAIM-REQUIREMENT-NOT-COVERED":
        semantic["runs"][0]["supported_requirement_ids"] = ["REQ-B"]
    elif probe_id == "AC-009-CLAIM-OUTPUT-NOT-OWNED":
        semantic["outputs"][0]["owner_run_id"] = "RUN-CAND-20260905"
    elif probe_id == "AC-010-CLAIM-METRIC-MISSING":
        semantic["claims"][0]["metric_ids"] = []
    elif probe_id == "AC-011-CLAIM-SCOPE-UNBOUNDED":
        semantic["claims"][0]["support_predicates"]["scope_bounded"] = False
    elif probe_id == "AC-012-AGGREGATE-MAPPING-WRONG":
        semantic["aggregate"]["requirement_claim_ids"]["REQ-A"] = "CLAIM-REQ-B"
    elif probe_id == "AC-013-COMPATIBILITY-UNKNOWN-NONBIJECTION":
        selection["selection"]["selection_mode"] = "JOINT_PORTFOLIO"
        selection["selection"]["compatibility"] = {
            "kind": "UNKNOWN_KIND",
            "version": "compatibility/v999",
            "ordered_ids": ["REQ-A", "REQ-B"],
            "permuted_ids": ["REQ-A", "REQ-A"],
        }
    else:  # pragma: no cover - frozen matrix completeness prevents this branch
        raise AssertionError(probe_id)
    _accepted(core, case, "problem_requirements", requirements_record)
    _accepted(core, case, "source_ledger", ledger)
    _accepted(core, case, "data_sufficiency", sufficiency)
    _accepted(core, case, "requirement_selection", selection)
    _accepted(core, case, "semantic_claim_support", semantic)
    _sync_bound_hashes(core, case)


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_frozen_actual_controller_probe_matrix_is_complete_and_hash_bound(repo_root) -> None:
    matrix_path = repo_root / MATRIX
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    payload = dict(matrix)
    matrix_hash = payload.pop("matrix_hash")
    assert _canonical_hash(payload) == matrix_hash
    assert matrix["probe_count"] == 13
    assert [item["probe_id"] for item in matrix["probes"]] == list(PROBES)
    assert all(item["expected_exit"] == "NONZERO" for item in matrix["probes"])
    assert all(item["expected_final_disposition"] == "BLOCK" for item in matrix["probes"])
    assert (
        matrix["test_sha256"]
        == hashlib.sha256((repo_root / matrix["test_file"]).read_bytes()).hexdigest()
    )
    assert (
        matrix["fixture_sha256"]
        == hashlib.sha256((repo_root / matrix["fixture_file"]).read_bytes()).hexdigest()
    )


@pytest.mark.parametrize("probe_id", list(PROBES))
def test_actual_controller_blocks_frozen_probe(repo_root, tmp_path, probe_id) -> None:
    core, case = _build_running_case(repo_root, tmp_path)
    _apply_mutation(core, case, probe_id)
    gate_id, reason_code = PROBES[probe_id]
    immutable_paths = [
        "case_state.json",
        "data/raw/input.json",
        core.ARTIFACT_PATHS["problem_requirements"],
        core.ARTIFACT_PATHS["source_ledger"],
        core.ARTIFACT_PATHS["data_audit"],
        core.ARTIFACT_PATHS["data_sufficiency"],
        core.ARTIFACT_PATHS["experiment_plan"],
        core.ARTIFACT_PATHS["requirement_selection"],
        core.ARTIFACT_PATHS["semantic_claim_support"],
        core.ARTIFACT_PATHS["modeling_to_paper_handoff"],
    ]
    before = {relative: core.file_hash(case / relative) for relative in immutable_paths}
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
        timeout=30,
    )
    assert completed.returncode != 0
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    assert result["status"] == "BLOCK_NATIVE_CONTRACTS"
    assert reason_code in result["reason_codes"]
    after = {relative: core.file_hash(case / relative) for relative in immutable_paths}
    assert after == before
    assert core.load_state(case)["state"] == "RUNNING"
    trace_path = case / "evidence/gate_execution_trace.json"
    assert trace_path.is_file()
    trace = core.load_json(trace_path)
    payload = dict(trace)
    trace_hash = payload.pop("trace_hash")
    assert _canonical_hash(payload) == trace_hash
    assert trace["state_before_hash"] == before["case_state.json"]
    assert trace["state_after_hash"] == before["case_state.json"]
    assert trace["final_disposition"] == "BLOCK"
    assert gate_id in [item["gate_id"] for item in trace["gate_sequence"]]
    assert all(item["input_hashes"] and item["output_hash"] for item in trace["gate_sequence"])
    exposed = "\n".join(
        [
            completed.stdout,
            completed.stderr,
            trace_path.read_text(encoding="utf-8"),
            (case / "evidence/native_completion.json").read_text(encoding="utf-8"),
            (case / core.ARTIFACT_PATHS["modeling_to_paper_handoff"]).read_text(encoding="utf-8"),
        ]
    )
    assert SENTINEL not in exposed
