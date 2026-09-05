#!/usr/bin/env python3
"""Independently verify the frozen selection batch and bind requirement-local choices."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

CASE_ID = "CUMCM-2017-C-VALIDATION-003F"
REQ1 = "REQ-1-DATA1-RELATION-QUALITY"
REQ2 = "REQ-2-DATA2-CONCENTRATION-MODEL"
REQ3 = "REQ-3-SAMPLE-SIZE-FEATURE-DIMENSION"
REQUIREMENT_IDS = [REQ1, REQ2, REQ3]
METRICS = {
    REQ1: "REQ1_MACRO_GROUPED_NMAE",
    REQ2: "REQ2_GROUPED_MAE_PPM",
    REQ3: "REQ2_GROUPED_MAE_PPM",
}


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def selected_candidate(
    candidate_ids: list[str], outputs: dict[str, dict[str, Any]], metric: str
) -> tuple[str, dict[str, float]]:
    values: dict[str, list[float]] = defaultdict(list)
    for output in outputs.values():
        value = output.get("final_metrics", {}).get(metric)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"missing strict metric: {metric}")
        values[str(output["candidate_id"])].append(float(value))
    scores = {
        candidate_id: sum(values[candidate_id]) / len(values[candidate_id])
        for candidate_id in candidate_ids
        if values[candidate_id]
    }
    if set(scores) != set(candidate_ids):
        raise ValueError(f"incomplete candidate scores for {metric}")
    return min(scores, key=lambda item: (scores[item], item)), scores


def output_id(requirement_id: str, run_id: str) -> str:
    compact = {REQ1: "REQ1", REQ2: "REQ2", REQ3: "REQ3"}[requirement_id]
    return f"OUTPUT-{compact}-{run_id}"


def run_descriptor(
    core: Any,
    capture: dict[str, Any],
) -> dict[str, Any]:
    run_id = capture["run_id"]
    return {
        "run_id": run_id,
        "outcome": capture["outcome"],
        "sealed": True,
        "current": True,
        "supported_requirement_ids": REQUIREMENT_IDS,
        "selected_output_ids": [output_id(item, run_id) for item in REQUIREMENT_IDS],
        "metric_ids": sorted(set(METRICS.values())),
        "input_hash": core.canonical_hash([item["sha256"] for item in capture["input_files"]]),
        "scenario_hash": capture["scenario_hash"],
        "configuration_hash": capture["configuration_hash"],
    }


def independent_check(
    case_root: Path,
    code_root: Path,
    run_id: str,
    output: Path,
    candidate_id: str,
    seed: int,
) -> dict[str, Any]:
    split = case_root / "splits/development_payload.json"
    command = [
        sys.executable,
        str(code_root / "independent_checks.py"),
        "--output",
        str(output),
        "--raw-dir",
        str(case_root / "data/raw"),
        "--split-payload",
        str(split),
        "--split-payload-sha256",
        _sha256(split),
        "--candidate-id",
        candidate_id,
        "--seed",
        str(seed),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise ValueError(f"independent check failed for {run_id}: {completed.stdout}")
    result = json.loads(completed.stdout)
    if result.get("status") != "PASS":
        raise ValueError(f"independent check did not pass for {run_id}")
    return result


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", required=True, type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    case_root = args.case_root.resolve()
    repository_root = args.repository_root.resolve()
    core = load_module(
        repository_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
        "cumcm_2017c_post_selection_core",
    )
    state = core.load_state(case_root)
    if state["case_id"] != CASE_ID or state["state"] != "RUNNING":
        raise ValueError("post-selection binding requires the frozen RUNNING case")
    plan = core.read_artifact(case_root, "experiment_plan")["content"]
    expected = {
        (candidate_id, seed)
        for candidate_id in plan["candidate_ids"]
        for seed in plan["random_seeds"]
    }
    captures: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    observed: set[tuple[str, int]] = set()
    checks: dict[str, dict[str, Any]] = {}
    code_root = case_root / "code"
    for path in sorted(case_root.glob("runs/*/execution_capture.json")):
        capture = core.load_json(path)
        run_id = str(capture.get("run_id"))
        key = (capture.get("candidate_id"), capture.get("seed"))
        if key in observed or key not in expected or capture.get("outcome") != "SUCCESS":
            raise ValueError(f"invalid frozen attempt: {run_id}")
        observed.add(key)
        output_path = case_root / capture["output"]["path"]
        output = core.load_json(output_path)
        checks[run_id] = independent_check(
            case_root,
            code_root,
            run_id,
            output_path,
            str(capture["candidate_id"]),
            int(capture["seed"]),
        )
        captures[run_id] = capture
        outputs[run_id] = output
    if observed != expected:
        raise ValueError("candidate-by-seed attempt matrix is incomplete")

    chosen1, scores1 = selected_candidate(plan["candidate_ids"], outputs, METRICS[REQ1])
    chosen2, scores2 = selected_candidate(plan["candidate_ids"], outputs, METRICS[REQ2])
    selected_candidates = {REQ1: chosen1, REQ2: chosen2, REQ3: chosen2}
    selected_runs = {
        requirement_id: min(
            run_id
            for run_id, capture in captures.items()
            if capture["candidate_id"] == candidate_id
        )
        for requirement_id, candidate_id in selected_candidates.items()
    }

    global_scores = scores2
    global_candidate = min(global_scores, key=lambda item: (global_scores[item], item))
    controller_selection = {
        "selected_candidate_id": global_candidate,
        "validation_scores": global_scores,
        "metric": plan["metric"],
        "rule": plan["selection_rule"],
        "aggregation_rule": plan["aggregation_rule"],
    }
    decision_hash = core.canonical_hash(controller_selection)
    manifests = {
        run_id: core.build_captured_run_manifest(
            case_root,
            run_id=run_id,
            decision_hash=decision_hash,
        )
        for run_id in sorted(captures)
    }
    runs = [run_descriptor(core, captures[run_id]) for run_id in sorted(captures)]
    requirements = core.read_artifact(case_root, "problem_requirements")["content"]["requirements"]
    selection_requirements = []
    for requirement in requirements:
        requirement_id = requirement["requirement_id"]
        run_id = selected_runs[requirement_id]
        selection_requirements.append(
            {
                "requirement_id": requirement_id,
                "candidate_run_ids": sorted(captures),
                "selection_metric": METRICS[requirement_id],
                "selection_direction": "MIN",
                "feasibility_gate": "PASS",
                "selected_run_ids": [run_id],
                "selected_output_ids": [output_id(requirement_id, run_id)],
                "dependency_requirements": requirement["dependency_requirements"],
                "dependency_bindings": (
                    [{"requirement_id": REQ2, "run_id": run_id}] if requirement_id == REQ3 else []
                ),
                "cross_requirement_constraints": [],
                "support_predicates": {
                    "metric_bound": True,
                    "independent_recomputation_passed": True,
                    "group_leakage_absent": True,
                },
            }
        )
    shared_input_hashes = sorted({item["input_hash"] for item in runs})
    shared_scenario_hashes = sorted({item["scenario_hash"] for item in runs})
    selection = {
        "contract_version": "requirement-selection/v1",
        "requirements": selection_requirements,
        "runs": runs,
        "selection": {
            "selection_mode": "PER_REQUIREMENT",
            "requirement_to_run_map": {key: [selected_runs[key]] for key in REQUIREMENT_IDS},
            "requirement_to_output_map": {
                key: [output_id(key, selected_runs[key])] for key in REQUIREMENT_IDS
            },
            "shared_input_hashes": shared_input_hashes,
            "shared_scenario_hashes": shared_scenario_hashes,
            "compatibility_checks": ["INPUT", "SCENARIO", "DEPENDENCY", "CONSTRAINTS"],
            "compatibility": {
                "kind": "RUN_PORTFOLIO_V1",
                "version": "compatibility/v1",
                "ordered_ids": REQUIREMENT_IDS,
                "permuted_ids": list(reversed(REQUIREMENT_IDS)),
            },
            "dependency_bridges": [],
            "cross_requirement_constraints": [],
            "aggregate_objective": "DECLARED_REQUIREMENT_LOCAL_METRICS",
            "tradeoff_rule": "REQ1_AND_REQ2_ARGMIN_INDEPENDENTLY;REQ3_INHERITS_REQ2",
            "limitations": [
                (
                    "Selections are conditional on the three preregistered candidates "
                    "and frozen seeds."
                ),
                "Development grouped OOS evidence does not replace the sealed one-shot final test.",
            ],
        },
    }

    run_index = {item["run_id"]: item for item in runs}
    semantic_outputs = []
    claims = []
    claim_types = {REQ1: "EMPIRICAL", REQ2: "PREDICTIVE", REQ3: "EMPIRICAL"}
    for requirement in requirements:
        requirement_id = requirement["requirement_id"]
        run_id = selected_runs[requirement_id]
        output = outputs[run_id]
        out_id = output_id(requirement_id, run_id)
        metric = METRICS[requirement_id]
        semantic_outputs.append(
            {
                "output_id": out_id,
                "requirement_id": requirement_id,
                "owner_run_id": run_id,
                "metric_ids": [metric],
            }
        )
        support = {
            "scope_bounded": True,
            "provided_empirical_source_bound": True,
            "same_concentration_replicate_leakage_absent": True,
        }
        if requirement_id == REQ2:
            support.update(validation_boundary_frozen=True, held_out_test_valid=True)
        claim_record = output["requirement_claims"][requirement_id]
        claims.append(
            {
                "claim_id": claim_record["claim_id"],
                "requirement_id": requirement_id,
                "claim_type": claim_types[requirement_id],
                "statement": claim_record["claim_text"],
                "scope": {
                    "fields": requirement["minimum_data_fields"],
                    "time": requirement["required_time_scope"],
                    "entities": requirement["required_entity_scope"],
                },
                "evidence_class": "PROVIDED_EMPIRICAL",
                "selected_run_ids": [run_id],
                "selected_output_ids": [out_id],
                "metric_ids": [metric],
                "comparator_ids": [],
                "support_predicates": support,
                "uncertainty": output["uncertainty"],
                "counter_evidence": [],
                "limitations": output["limitations"],
                "claim_strength": "BOUNDED",
                "status": "SUPPORTED",
            }
        )
    semantic = {
        "contract_version": "claim-evidence/v3",
        "claims": claims,
        "runs": [run_index[item] for item in sorted(run_index)],
        "outputs": semantic_outputs,
        "comparators": [],
        "validation": {"counter_evidence_detected": False},
        "aggregate": {
            "primary_requirement_ids": REQUIREMENT_IDS,
            "supported_requirement_ids": list(reversed(REQUIREMENT_IDS)),
            "requirement_claim_ids": {
                claim["requirement_id"]: claim["claim_id"] for claim in claims
            },
        },
    }
    for key, content in (
        ("requirement_selection", selection),
        ("semantic_claim_support", semantic),
    ):
        core.write_json(case_root / core.ARTIFACT_PATHS[key], core.artifact(key, content))
    evidence_dir = case_root / "evidence/independent_checks"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for run_id, result in checks.items():
        core.write_json(evidence_dir / f"{run_id}.json", result, overwrite=False)
    record = {
        "case_id": CASE_ID,
        "attempt_count": len(captures),
        "independent_check_count": len(checks),
        "scores": {REQ1: scores1, REQ2: scores2, REQ3: scores2},
        "selected_candidates": selected_candidates,
        "selected_runs": selected_runs,
        "controller_selection": controller_selection,
        "selection_decision_hash": decision_hash,
        "manifest_preview_hashes": {
            run_id: core.canonical_hash(manifest) for run_id, manifest in manifests.items()
        },
        "sealed_test_access_count": 0,
    }
    core.write_json(case_root / "evidence/development_selection.json", record, overwrite=False)
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
