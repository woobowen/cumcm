"""Neutral end-to-end execution through the actual completion controller."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


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
        timeout=30,
    )
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    return completed, result


def _accepted(core, case: Path, key: str, content: dict) -> None:
    core.write_json(case / core.ARTIFACT_PATHS[key], core.artifact(key, content))


def _advance_to(core, case: Path, target: str) -> None:
    while core.load_state(case)["state"] != target:
        core.advance_once(case)


def _requirement(
    requirement_id: str,
    *,
    evidence_class: str = "PROVIDED_EMPIRICAL",
    fields: list[str] | None = None,
    external_allowed: bool = False,
    external_required: bool = False,
    simulation_allowed: bool = False,
    partial_allowed: bool = False,
    dependencies: list[str] | None = None,
) -> dict:
    return {
        "requirement_id": requirement_id,
        "role": "PRIMARY",
        "required_evidence_classes": [evidence_class],
        "allowed_evidence_classes": [evidence_class],
        "minimum_data_fields": fields or ["x"],
        "required_time_scope": ["FROZEN_SCOPE"],
        "required_entity_scope": ["ENTITY-SET"],
        "external_data_allowed": external_allowed,
        "external_data_required": external_required,
        "simulation_substitution_allowed": simulation_allowed,
        "partial_completion_allowed": partial_allowed,
        "dependency_requirements": dependencies or [],
        "completion_rule": "ALL_REQUIRED_EVIDENCE",
    }


def _source(
    source_id: str,
    requirement_ids: list[str],
    source_hash: str,
    *,
    evidence_class: str = "PROVIDED_EMPIRICAL",
    fields: list[str] | None = None,
    time_scope: list[str] | None = None,
    entity_scope: list[str] | None = None,
) -> dict:
    return {
        "source_id": source_id,
        "supports_requirement_ids": requirement_ids,
        "evidence_class": evidence_class,
        "provenance": "PROJECT_ORIGINAL_TEST_INPUT",
        "authority": "FIRST_PARTY_FIXTURE",
        "retrieval_time": "2026-09-05T00:00:00Z",
        "license_or_usage_status": "ALLOWED",
        "geographic_scope": [],
        "time_scope": time_scope if time_scope is not None else ["FROZEN_SCOPE"],
        "entity_scope": entity_scope if entity_scope is not None else ["ENTITY-SET"],
        "field_schema": fields or ["x"],
        "hash": source_hash,
        "freshness": "CURRENT_FOR_SCOPE",
        "limitations": ["Project-original neutral source."],
    }


def _assessment(requirement_id: str) -> dict:
    return {
        "requirement_id": requirement_id,
        "data_sufficiency_status": "SUFFICIENT",
        "missing_fields": [],
        "missing_entities": [],
        "missing_time_scope": [],
        "candidate_sources": [],
        "acquisition_cost": "NONE",
        "acquisition_time": "NONE",
        "allowed_substitutions": [],
        "forbidden_substitutions": [],
        "affected_downstream_stages": [],
    }


def _run_record(core, candidate_id: str, requirement_ids: list[str], seed: int) -> dict:
    return {
        "run_id": f"RUN-{candidate_id}-{seed}",
        "outcome": "SUCCESS",
        "sealed": True,
        "current": True,
        "supported_requirement_ids": requirement_ids,
        "selected_output_ids": [f"OUT-{item}" for item in requirement_ids],
        "metric_ids": [f"metric_{chr(ord('a') + index)}" for index in range(len(requirement_ids))],
        "input_hash": "",
        "scenario_hash": "",
        "configuration_hash": core.canonical_hash({"candidate_id": candidate_id, "seed": seed}),
        "policy_exposure": 0,
    }


def _selection_and_semantic(
    core,
    requirements: list[dict],
    raw_hash: str,
    *,
    mode: str,
    selected_candidates: dict[str, str],
    dependency_bridges: list[dict] | None = None,
    constraints: list[dict] | None = None,
    evidence_classes: dict[str, str] | None = None,
    claim_types: dict[str, str] | None = None,
    seed: int = 20260906,
) -> tuple[dict, dict]:
    requirement_ids = [item["requirement_id"] for item in requirements]
    input_hash = core.canonical_hash([raw_hash])
    runs = [
        _run_record(core, candidate_id, requirement_ids, seed) for candidate_id in ("BASE", "CAND")
    ]
    for run in runs:
        run["input_hash"] = input_hash
        run["scenario_hash"] = raw_hash
    run_map = {
        requirement_id: [f"RUN-{selected_candidates[requirement_id]}-{seed}"]
        for requirement_id in requirement_ids
    }
    output_map = {requirement_id: [f"OUT-{requirement_id}"] for requirement_id in requirement_ids}
    selection = {
        "contract_version": "requirement-selection/v1",
        "requirements": [
            {
                "requirement_id": requirement_id,
                "candidate_run_ids": [run["run_id"] for run in runs],
                "selection_metric": f"metric_{chr(ord('a') + index)}",
                "selection_direction": "MIN",
                "feasibility_gate": "PASS",
                "selected_run_ids": run_map[requirement_id],
                "selected_output_ids": output_map[requirement_id],
                "dependency_requirements": requirements[index]["dependency_requirements"],
                "dependency_bindings": [],
                "cross_requirement_constraints": constraints or [],
                "support_predicates": {"metric_bound": True},
            }
            for index, requirement_id in enumerate(requirement_ids)
        ],
        "runs": runs,
        "selection": {
            "selection_mode": mode,
            "requirement_to_run_map": run_map,
            "requirement_to_output_map": output_map,
            "shared_input_hashes": [input_hash],
            "shared_scenario_hashes": [raw_hash],
            "compatibility_checks": ["INPUT", "SCENARIO", "CONSTRAINTS"],
            "compatibility": {
                "kind": "RUN_PORTFOLIO_V1",
                "version": "compatibility/v1",
                "ordered_ids": requirement_ids,
                "permuted_ids": list(reversed(requirement_ids)),
            },
            "dependency_bridges": dependency_bridges or [],
            "cross_requirement_constraints": constraints or [],
            "aggregate_objective": "DECLARED_TRADEOFF",
            "tradeoff_rule": "REQUIREMENT_LOCAL_METRICS",
            "limitations": ["Project-original neutral selection."],
        },
    }
    claims = []
    outputs = []
    for index, requirement_id in enumerate(requirement_ids):
        metric = f"metric_{chr(ord('a') + index)}"
        run_id = run_map[requirement_id][0]
        claim_type = (claim_types or {}).get(requirement_id, "DESCRIPTIVE")
        predicates = {"scope_bounded": True}
        if claim_type == "SIMULATION_CONDITIONAL":
            predicates["registered_assumptions_bound"] = True
        claims.append(
            {
                "claim_id": f"CLAIM-{requirement_id}",
                "requirement_id": requirement_id,
                "claim_type": claim_type,
                "statement": f"Bounded statement for {requirement_id}.",
                "scope": {
                    "fields": requirements[index]["minimum_data_fields"],
                    "time": requirements[index]["required_time_scope"],
                    "entities": requirements[index]["required_entity_scope"],
                },
                "evidence_class": (evidence_classes or {}).get(
                    requirement_id, "PROVIDED_EMPIRICAL"
                ),
                "selected_run_ids": [run_id],
                "selected_output_ids": [f"OUT-{requirement_id}"],
                "metric_ids": [metric],
                "comparator_ids": [],
                "support_predicates": predicates,
                "uncertainty": {"status": "BOUNDED"},
                "counter_evidence": [],
                "limitations": ["Project-original neutral Claim."],
                "claim_strength": "BOUNDED",
                "status": "SUPPORTED",
            }
        )
        outputs.append(
            {
                "output_id": f"OUT-{requirement_id}",
                "requirement_id": requirement_id,
                "owner_run_id": run_id,
                "metric_ids": [metric],
            }
        )
    semantic = {
        "contract_version": "claim-evidence/v3",
        "claims": claims,
        "runs": copy.deepcopy(runs),
        "outputs": outputs,
        "comparators": [],
        "validation": {"counter_evidence_detected": False},
        "aggregate": {
            "primary_requirement_ids": requirement_ids,
            "supported_requirement_ids": list(reversed(requirement_ids)),
            "requirement_claim_ids": {
                requirement_id: f"CLAIM-{requirement_id}" for requirement_id in requirement_ids
            },
        },
    }
    return selection, semantic


def _build_runtime_case(
    repo_root: Path,
    tmp_path: Path,
    *,
    requirements: list[dict],
    sources: list[dict],
    sufficiency: dict,
    selection: dict,
    semantic: dict,
    seed: int = 20260906,
):
    core = _module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        f"neutral_runtime_core_{tmp_path.name}",
    )
    synthetic = _module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/synthetic_cases.py",
        f"neutral_runtime_synthetic_{tmp_path.name}",
    )
    case = tmp_path / "case"
    core.initialize_case(case, "NEUTRAL-RUNTIME-E2E", "general")
    core.write_json(case / "data/raw/input.json", {"x": [1, 2], "y": [3, 4]})
    raw_hash = core.file_hash(case / "data/raw/input.json")
    sources = copy.deepcopy(sources)
    for source in sources:
        if source.get("hash") == "AUTO":
            source["hash"] = raw_hash
    sufficiency = copy.deepcopy(sufficiency)
    sufficiency["requirements"] = requirements
    sufficiency["sources"] = sources
    for composition in sufficiency.get("source_compositions", []):
        if composition.get("composition_hash") == "AUTO":
            body = {key: value for key, value in composition.items() if key != "composition_hash"}
            composition["composition_hash"] = core.canonical_hash(body)
    selection = copy.deepcopy(selection)
    semantic = copy.deepcopy(semantic)
    input_hash = core.canonical_hash([raw_hash])
    for run in selection["runs"]:
        run["input_hash"] = input_hash
        run["scenario_hash"] = raw_hash
    for run in semantic["runs"]:
        run["input_hash"] = input_hash
        run["scenario_hash"] = raw_hash
    selection["selection"]["shared_input_hashes"] = [input_hash]
    selection["selection"]["shared_scenario_hashes"] = [raw_hash]
    for bridge in selection["selection"].get("dependency_bridges", []):
        bridge["input_hash"] = input_hash
        bridge["scenario_hash"] = raw_hash
        body = {key: value for key, value in bridge.items() if key != "lineage_hash"}
        bridge["lineage_hash"] = core.canonical_hash(body)
    _accepted(
        core,
        case,
        "problem_requirements",
        {
            "contract_version": "requirement-evidence/v1",
            "case_id": "NEUTRAL-RUNTIME-E2E",
            "requirements": requirements,
        },
    )
    _advance_to(core, case, "REQUIREMENTS_VALIDATED")
    _accepted(
        core,
        case,
        "research_plan",
        {"mode": "OFFLINE_PROJECT_ORIGINAL", "questions": ["neutral"], "external_search": False},
    )
    _accepted(
        core,
        case,
        "source_ledger",
        {
            "contract_version": "requirement-evidence/v1",
            "sources": sources,
            "answer_access_status": "NOT_ACCESSED",
        },
    )
    _accepted(core, case, "data_sufficiency", sufficiency)
    _advance_to(core, case, "SOURCES_PLANNED")
    _accepted(
        core,
        case,
        "assumptions_and_symbols",
        {
            "assumptions": ["finite neutral fixture"],
            "symbols": {"x": "unitless"},
            "formulas": ["mean(x)"],
        },
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
    fixture = repo_root / "tests/fixtures/runtime_portfolio_model.py"
    model = case / "models/runtime_model.py"
    shutil.copyfile(fixture, model)
    code = synthetic._required_code_files(core) + [
        {
            "scope": "CASE_ROOT",
            "path": "models/runtime_model.py",
            "repository_path": "tests/fixtures/runtime_portfolio_model.py",
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
        "metric_a",
        splits,
        "BASE",
        inputs,
        "one deterministic run per candidate",
        generated,
        code,
        commit,
    )
    freezes["seed_schedule"] = core.canonical_hash([seed])
    _accepted(
        core,
        case,
        "experiment_plan",
        {
            "preregistered": True,
            "execution_prepared": True,
            "candidate_ids": ["BASE", "CAND"],
            "baseline_id": "BASE",
            "metric": "metric_a",
            "metric_direction": "MIN",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
            "selection_rule": "ARGMIN_THEN_ID",
            "random_seeds": [seed],
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
    synthetic._write_output_contract_probe(
        core,
        case,
        [item["requirement_id"] for item in requirements],
        metric="metric_a",
    )
    core.advance_once(case)
    core.advance_once(case)
    for candidate_id in ("BASE", "CAND"):
        core.execute_case_code(
            case,
            run_id=f"RUN-{candidate_id}-{seed}",
            candidate_id=candidate_id,
            seed=seed,
            code_path="models/runtime_model.py",
            timeout_seconds=30,
        )
    _accepted(core, case, "requirement_selection", selection)
    _accepted(core, case, "semantic_claim_support", semantic)
    return core, case


def test_neutral_per_requirement_actual_controller_reaches_handoff(repo_root, tmp_path) -> None:
    probes = _module(
        repo_root / "tests/integration/test_actual_controller_black_box.py",
        f"neutral_probe_builder_{tmp_path.name}",
    )
    core, case = probes._build_running_case(repo_root, tmp_path)
    completed, result = _run_controller(repo_root, case)
    assert completed.returncode == 0, completed.stderr
    assert result["status"] == "PASS_NATIVE_CONTRACTS"
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    assert result["selected_run_ids"] == ["RUN-BASE-20260905", "RUN-CAND-20260905"]
    trace = core.load_json(case / "evidence/gate_execution_trace.json")
    assert [item["gate_id"] for item in trace["gate_sequence"]] == [
        "GATE_PROBLEM_REQUIREMENT",
        "GATE_SOURCE_EVIDENCE",
        "GATE_DATA_SUFFICIENCY_PREFLIGHT",
        "GATE_COMPARISON_SELECTION",
        "GATE_RUN_ELIGIBILITY",
        "GATE_COMPATIBILITY_PORTFOLIO",
        "GATE_SEMANTIC_CLAIM",
        "GATE_AGGREGATE_CLAIM",
        "GATE_FINALIZATION",
        "GATE_HANDOFF",
    ]
    handoff = core.load_json(case / core.ARTIFACT_PATHS["modeling_to_paper_handoff"])
    assert {item["run_id"] for item in handoff["final_runs"]} == {
        "RUN-BASE-20260905",
        "RUN-CAND-20260905",
    }


@pytest.mark.parametrize("mutation", ["REQUIREMENT_ORDER", "CLAIM_ORDER"])
def test_neutral_per_requirement_legal_permutations_are_stable(
    repo_root, tmp_path, mutation
) -> None:
    probes = _module(
        repo_root / "tests/integration/test_actual_controller_black_box.py",
        f"neutral_legal_builder_{mutation}_{tmp_path.name}",
    )
    core, case = probes._build_running_case(repo_root, tmp_path)
    if mutation == "REQUIREMENT_ORDER":
        requirement_record = core.read_artifact(case, "problem_requirements")["content"]
        sufficiency = core.read_artifact(case, "data_sufficiency")["content"]
        selection = core.read_artifact(case, "requirement_selection")["content"]
        requirement_record["requirements"].reverse()
        sufficiency["requirements"].reverse()
        sufficiency["requirement_assessments"].reverse()
        selection["requirements"].reverse()
        _accepted(core, case, "problem_requirements", requirement_record)
        _accepted(core, case, "data_sufficiency", sufficiency)
        _accepted(core, case, "requirement_selection", selection)
    else:
        semantic = core.read_artifact(case, "semantic_claim_support")["content"]
        semantic["claims"].reverse()
        _accepted(core, case, "semantic_claim_support", semantic)
    probes._sync_bound_hashes(core, case)
    completed, result = _run_controller(repo_root, case)
    assert completed.returncode == 0, completed.stderr
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"


@pytest.mark.parametrize("mutation", ["RUN_BINDING", "OUTPUT_OWNER", "AGGREGATE_MAP"])
def test_neutral_per_requirement_invalid_bindings_block(repo_root, tmp_path, mutation) -> None:
    probes = _module(
        repo_root / "tests/integration/test_actual_controller_black_box.py",
        f"neutral_invalid_builder_{mutation}_{tmp_path.name}",
    )
    core, case = probes._build_running_case(repo_root, tmp_path)
    if mutation == "RUN_BINDING":
        selection = core.read_artifact(case, "requirement_selection")["content"]
        selection["selection"]["requirement_to_run_map"]["REQ-A"] = []
        _accepted(core, case, "requirement_selection", selection)
    else:
        semantic = core.read_artifact(case, "semantic_claim_support")["content"]
        if mutation == "OUTPUT_OWNER":
            semantic["outputs"][0]["owner_run_id"] = "RUN-CAND-20260905"
        else:
            semantic["aggregate"]["requirement_claim_ids"]["REQ-A"] = "CLAIM-REQ-B"
        _accepted(core, case, "semantic_claim_support", semantic)
    probes._sync_bound_hashes(core, case)
    completed, result = _run_controller(repo_root, case)
    assert completed.returncode != 0
    assert result["status"] == "BLOCK_NATIVE_CONTRACTS"
    assert core.load_state(case)["state"] == "RUNNING"
    handoff = core.load_json(case / core.ARTIFACT_PATHS["modeling_to_paper_handoff"])
    assert handoff["approved_by"] == []


def _build_portfolio_case(repo_root: Path, tmp_path: Path):
    preview = _module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        f"neutral_portfolio_preview_{tmp_path.name}",
    )
    requirements = [
        _requirement("REQ-A"),
        _requirement("REQ-B"),
        _requirement("REQ-C", dependencies=["REQ-A"]),
    ]
    sources = [_source("SRC-ALL", ["REQ-A", "REQ-B", "REQ-C"], "AUTO")]
    sufficiency = {
        "contract_version": "data-sufficiency/v1",
        "requirements": requirements,
        "sources": sources,
        "acquisition_plans": [],
        "source_compositions": [],
        "coverage_mode_by_requirement": {
            requirement["requirement_id"]: {"mode": "SINGLE_SOURCE", "source_id": "SRC-ALL"}
            for requirement in requirements
        },
        "aggregate_completion_claimed": False,
        "requirement_assessments": [
            _assessment(requirement["requirement_id"]) for requirement in requirements
        ],
    }
    bridge = {
        "dependency_requirement_id": "REQ-A",
        "dependent_requirement_id": "REQ-C",
        "upstream_run_ids": ["RUN-BASE-20260906"],
        "downstream_run_ids": ["RUN-CAND-20260906"],
        "input_hash": "AUTO",
        "scenario_hash": "AUTO",
        "lineage_hash": "AUTO",
    }
    constraints = [{"constraint_id": "CROSS-REQ-1", "status": "SATISFIED"}]
    selection, semantic = _selection_and_semantic(
        preview,
        requirements,
        "AUTO",
        mode="JOINT_PORTFOLIO",
        selected_candidates={"REQ-A": "BASE", "REQ-B": "CAND", "REQ-C": "CAND"},
        dependency_bridges=[bridge],
        constraints=constraints,
    )
    return _build_runtime_case(
        repo_root,
        tmp_path,
        requirements=requirements,
        sources=sources,
        sufficiency=sufficiency,
        selection=selection,
        semantic=semantic,
    )


def test_neutral_joint_portfolio_actual_controller_reaches_handoff(repo_root, tmp_path) -> None:
    core, case = _build_portfolio_case(repo_root, tmp_path)
    completed, result = _run_controller(repo_root, case)
    assert completed.returncode == 0, completed.stderr
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    final = core.read_artifact(case, "final_result")["content"]
    assert final["selection_mode"] == "JOINT_PORTFOLIO"
    assert final["selected_run_ids"] == ["RUN-BASE-20260906", "RUN-CAND-20260906"]
    assert final["run_bindings"]["RUN-BASE-20260906"]["requirement_ids"] == ["REQ-A"]
    assert final["run_bindings"]["RUN-CAND-20260906"]["requirement_ids"] == [
        "REQ-B",
        "REQ-C",
    ]


@pytest.mark.parametrize(
    ("mutation", "reason_code"),
    [
        ("SHARED_HASH", "RC_SELECTION_PORTFOLIO_HASHES_MISSING"),
        ("ACTUAL_HASH", "RC_SELECTION_PORTFOLIO_HASH_MISMATCH"),
        ("DEPENDENCY_BRIDGE", "RC_SELECTION_DEPENDENCY_BRIDGE_MISSING"),
        ("SCENARIO", "RC_SELECTION_PORTFOLIO_HASH_MISMATCH"),
        ("CONSTRAINT", "RC_PORTFOLIO_CROSS_REQUIREMENT_INCONSISTENT"),
    ],
)
def test_neutral_joint_portfolio_invalid_mutations_block(
    repo_root, tmp_path, mutation, reason_code
) -> None:
    core, case = _build_portfolio_case(repo_root, tmp_path)
    selection = core.read_artifact(case, "requirement_selection")["content"]
    if mutation == "SHARED_HASH":
        selection["selection"]["shared_input_hashes"] = []
    elif mutation == "DEPENDENCY_BRIDGE":
        selection["selection"]["dependency_bridges"] = []
    elif mutation == "SCENARIO":
        selection["runs"][1]["scenario_hash"] = "b" * 64
    elif mutation == "CONSTRAINT":
        selection["selection"]["cross_requirement_constraints"][0]["status"] = "CONFLICT"
    else:
        controller = _module(
            repo_root / "scripts/finalize_fresh_c_validation.py",
            f"neutral_manifest_mutator_{tmp_path.name}",
        )
        plan = core.read_artifact(case, "experiment_plan")["content"]
        attempts, _ = controller._attempt_registry(core, case, plan)
        decision = core.canonical_hash(controller.select_candidate(attempts, plan))
        for attempt in attempts:
            core.seal_captured_run(case, run_id=attempt["run_id"], decision_hash=decision)
        manifest_path = case / "runs/RUN-CAND-20260906/manifest.json"
        manifest = core.load_json(manifest_path)
        manifest["input_hash"] = "b" * 64
        core.write_json(manifest_path, manifest)
    _accepted(core, case, "requirement_selection", selection)
    completed, result = _run_controller(repo_root, case)
    assert completed.returncode != 0
    assert reason_code in result["reason_codes"]
    trace = core.load_json(case / "evidence/gate_execution_trace.json")
    assert trace["gate_sequence"][-1]["gate_id"] == "GATE_COMPATIBILITY_PORTFOLIO"
    assert core.load_state(case)["state"] == "RUNNING"


def _build_data_sufficiency_case(repo_root: Path, tmp_path: Path):
    preview = _module(
        repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        f"neutral_data_preview_{tmp_path.name}",
    )
    requirements = [
        _requirement("REQ-P", fields=["x", "y"]),
        _requirement(
            "REQ-A",
            evidence_class="ACQUIRED_EMPIRICAL",
            external_allowed=True,
            external_required=True,
        ),
        _requirement("REQ-X"),
        _requirement(
            "REQ-S",
            evidence_class="SIMULATION",
            simulation_allowed=True,
        ),
    ]
    sources = [
        _source("SRC-PX", ["REQ-P"], "AUTO", fields=["x"]),
        _source("SRC-PY", ["REQ-P"], "AUTO", fields=["y"]),
        _source(
            "SRC-ACQUIRED",
            ["REQ-A"],
            "AUTO",
            evidence_class="ACQUIRED_EMPIRICAL",
        ),
        _source("SRC-EXTERNAL-SAFE", ["REQ-X"], "AUTO"),
        _source("SRC-UNION-1", ["REQ-X"], "AUTO", fields=["x"], entity_scope=["OTHER"]),
        _source("SRC-UNION-2", ["REQ-X"], "AUTO", fields=["z"], time_scope=["OTHER"]),
        _source("SRC-SIM", ["REQ-S"], "AUTO", evidence_class="SIMULATION"),
    ]
    acquisition_plan = {
        "requirement_id": "REQ-A",
        "required_fields": ["x"],
        "required_time_scope": ["FROZEN_SCOPE"],
        "required_entity_scope": ["ENTITY-SET"],
        "authoritative_source_candidates": ["SRC-ACQUIRED"],
        "acquisition_method": "PROJECT_ORIGINAL_FIXTURE",
        "provenance_plan": "HASH_AND_LEDGER_BINDING",
        "license_or_usage_plan": "FIRST_PARTY_ALLOWED",
        "validation_plan": "SCHEMA_SCOPE_AND_HASH",
        "time_budget": "BOUNDED",
        "fallback_disposition": "BLOCK",
        "status": "ACQUIRED",
    }
    composition = {
        "composition_id": "COMP-P",
        "source_ids": ["SRC-PX", "SRC-PY"],
        "join_keys": ["entity_id"],
        "join_cardinality": "ONE_TO_ONE",
        "entity_alignment": "EXACT",
        "time_alignment": "EXACT",
        "field_ownership": {"x": "SRC-PX", "y": "SRC-PY"},
        "deduplication_policy": "EXACT_KEY_UNIQUE",
        "conflict_resolution": "OWNER_SOURCE_WINS",
        "provenance": "PROJECT_ORIGINAL_COMPOSITION",
        "composition_hash": "AUTO",
    }
    sufficiency = {
        "contract_version": "data-sufficiency/v1",
        "requirements": requirements,
        "sources": sources,
        "acquisition_plans": [acquisition_plan],
        "source_compositions": [composition],
        "coverage_mode_by_requirement": {
            "REQ-P": {"mode": "REGISTERED_COMPOSITION", "composition_id": "COMP-P"},
            "REQ-A": {"mode": "SINGLE_SOURCE", "source_id": "SRC-ACQUIRED"},
            "REQ-X": {"mode": "SINGLE_SOURCE", "source_id": "SRC-EXTERNAL-SAFE"},
            "REQ-S": {"mode": "SINGLE_SOURCE", "source_id": "SRC-SIM"},
        },
        "aggregate_completion_claimed": False,
        "requirement_assessments": [
            _assessment(requirement["requirement_id"]) for requirement in requirements
        ],
    }
    selection, semantic = _selection_and_semantic(
        preview,
        requirements,
        "AUTO",
        mode="GLOBAL_JOINT",
        selected_candidates={requirement["requirement_id"]: "BASE" for requirement in requirements},
        evidence_classes={
            "REQ-P": "PROVIDED_EMPIRICAL",
            "REQ-A": "ACQUIRED_EMPIRICAL",
            "REQ-X": "PROVIDED_EMPIRICAL",
            "REQ-S": "SIMULATION",
        },
        claim_types={"REQ-S": "SIMULATION_CONDITIONAL"},
    )
    return _build_runtime_case(
        repo_root,
        tmp_path,
        requirements=requirements,
        sources=sources,
        sufficiency=sufficiency,
        selection=selection,
        semantic=semantic,
    )


def test_neutral_data_sufficiency_composition_actual_controller_reaches_handoff(
    repo_root, tmp_path
) -> None:
    core, case = _build_data_sufficiency_case(repo_root, tmp_path)
    completed, result = _run_controller(repo_root, case)
    assert completed.returncode == 0, completed.stderr
    assert result["native_state"] == "READY_FOR_PAPER_HANDOFF"
    handoff = core.load_json(case / core.ARTIFACT_PATHS["modeling_to_paper_handoff"])
    assert set(handoff["requirement_traceability"]) == {"REQ-P", "REQ-A", "REQ-X", "REQ-S"}


@pytest.mark.parametrize(
    ("mutation", "reason_code", "source_status"),
    [
        ("EXTERNAL_FORBIDDEN", "RC_EXTERNAL_DATA_POLICY_FORBIDDEN", "BLOCK"),
        ("SIMULATION_EMPIRICAL", "RC_SIMULATION_CANNOT_SUPPORT_EMPIRICAL_CLAIM", "BLOCK"),
        ("UNREGISTERED_UNION", "RC_DATA_SOURCE_COMPOSITION_INVALID", "BLOCK"),
        ("PARTIAL", "RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE", "PARTIAL"),
    ],
)
def test_neutral_data_sufficiency_invalid_or_partial_never_completes(
    repo_root, tmp_path, mutation, reason_code, source_status
) -> None:
    core, case = _build_data_sufficiency_case(repo_root, tmp_path)
    requirements_record = core.read_artifact(case, "problem_requirements")["content"]
    ledger = core.read_artifact(case, "source_ledger")["content"]
    sufficiency = core.read_artifact(case, "data_sufficiency")["content"]
    if mutation == "EXTERNAL_FORBIDDEN":
        source = next(
            item for item in ledger["sources"] if item["source_id"] == "SRC-EXTERNAL-SAFE"
        )
        source["evidence_class"] = "ACQUIRED_EMPIRICAL"
    elif mutation == "SIMULATION_EMPIRICAL":
        requirement = next(
            item
            for item in requirements_record["requirements"]
            if item["requirement_id"] == "REQ-S"
        )
        requirement["required_evidence_classes"] = ["PROVIDED_EMPIRICAL"]
        requirement["allowed_evidence_classes"] = ["PROVIDED_EMPIRICAL"]
    elif mutation == "UNREGISTERED_UNION":
        sufficiency["coverage_mode_by_requirement"]["REQ-P"]["composition_id"] = "UNKNOWN"
    else:
        requirement = next(
            item
            for item in requirements_record["requirements"]
            if item["requirement_id"] == "REQ-X"
        )
        requirement["partial_completion_allowed"] = True
        source = next(
            item for item in ledger["sources"] if item["source_id"] == "SRC-EXTERNAL-SAFE"
        )
        source["entity_scope"] = ["OTHER"]
    sufficiency["requirements"] = requirements_record["requirements"]
    sufficiency["sources"] = ledger["sources"]
    _accepted(core, case, "problem_requirements", requirements_record)
    _accepted(core, case, "source_ledger", ledger)
    _accepted(core, case, "data_sufficiency", sufficiency)
    state = core.load_json(case / "case_state.json")
    for relative in state["evidence_bindings"]:
        if (case / relative).is_file():
            state["evidence_bindings"][relative] = core.file_hash(case / relative)
    core.write_json(case / "case_state.json", state)
    completed, result = _run_controller(repo_root, case)
    assert completed.returncode != 0
    assert reason_code in result["reason_codes"]
    trace = core.load_json(case / "evidence/gate_execution_trace.json")
    data_gate = trace["gate_sequence"][-1]
    assert data_gate["gate_id"] == "GATE_DATA_SUFFICIENCY_PREFLIGHT"
    if source_status == "PARTIAL":
        assert data_gate["result"] == "BLOCK"
    assert core.load_state(case)["state"] == "RUNNING"
    handoff = core.load_json(case / core.ARTIFACT_PATHS["modeling_to_paper_handoff"])
    assert handoff["approved_by"] == []
