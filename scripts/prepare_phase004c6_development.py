"""Prepare registered known-problem children and proposals through the common RC9 core.

Preparation never runs a model, checker or Final. Numerical processes have separate
public CLI invocations and immutable execution receipts. Parent roots are read-only.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PHASE = REPO / "evals/results/phase-004c6"
CORE = REPO / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
CASES = {
    2016: "CUMCM-2016-C-POSTVALIDATION-DEVELOPMENT-006",
    2015: "CUMCM-2015-C-POSTVALIDATION-DEVELOPMENT-007",
}
PARENTS = {
    2016: REPO / ".cache/pr12-rc8/fresh/2016/case-r2",
    2015: REPO / ".cache/pr12-rc8/fresh/2015/case",
}


def load_core():
    spec = importlib.util.spec_from_file_location("rc9_development_core", CORE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def definition(target, unit, *, formula="VALUE", aggregation="SINGLE", remaining=False):
    relative = formula == "ABSOLUTE_RELATIVE_ERROR"
    return {
        "target": target,
        "quantity": "REMAINING_TIME" if remaining else "SCALAR",
        "target_unit": unit,
        "unit": "1" if relative else unit,
        "prediction_origin": "PER_SAMPLE" if remaining else "NOT_APPLICABLE",
        "formula": formula,
        "denominator": "TRUE_REMAINING_TIME" if remaining else "TRUE_VALUE" if relative else "ONE",
        "sample_unit": "historical_state_origin" if remaining else "declared_grid_or_event_summary",
        "aggregation": aggregation,
        "weights": "UNIFORM",
        "direction": "MIN",
        "zero_denominator_policy": "REJECT",
    }


def metric_definitions(year):
    if year == 2016:
        curve = definition(
            "elapsed_time_at_voltage", "min", formula="ABSOLUTE_RELATIVE_ERROR", aggregation="MEAN"
        )
        return {
            "q1_mean_fitted_MRE": {**curve, "sample_unit": "current_voltage_grid"},
            "q2_loco_MRE": {**curve, "sample_unit": "held_out_current_voltage_grid"},
            "q3_remaining_MRE": definition(
                "remaining_time",
                "min",
                formula="ABSOLUTE_RELATIVE_ERROR",
                aggregation="MEAN",
                remaining=True,
            ),
            "q3_remaining_min": definition("future_remaining_time", "min"),
        }
    result = {
        "reference_altitude_rmse_deg": definition(
            "solar_lunar_altitude", "degree", formula="SQUARED_ERROR", aggregation="ROOT_MEAN"
        ),
        "reference_altitude_max_abs_deg": definition(
            "altitude_absolute_error", "degree", aggregation="MAX"
        ),
        "definition_tree_angle_deg": definition("tree_angle", "degree"),
        "definition_calendar_rows": definition("calendar_rows", "count"),
        "scenario_event_count": definition("scenario_event_count", "count"),
    }
    for city in ("Beijing", "Harbin", "Shanghai", "Guangzhou", "Kunming", "Chengdu", "Urumqi"):
        result[city + "_event_count"] = definition(city + "_event_count", "count")
    return result


def temporal_index(root, core):
    """Read provided observations only; use an explicit discharge-order coordinate.

    10000 min separates observed discharge states, not inferred calendar dates.
    No state3 terminal label is present or manufactured.
    """
    from openpyxl import load_workbook

    book = load_workbook(root / "data/raw/appendix.xlsx", read_only=True, data_only=True)
    rows = [r for r in book["附件2"].values][2:303]
    book.close()
    if (
        len(rows) != 301
        or any(not isinstance(r[0], (int, float)) for r in rows)
        or any(rows[j][0] <= rows[j + 1][0] for j in range(len(rows) - 1))
    ):
        raise ValueError("ATTACHMENT2_ORDER_NOT_STRICTLY_DECREASING")
    if any(not isinstance(r[s + 1], (int, float)) for r in rows for s in range(3)):
        raise ValueError("HISTORICAL_STATE_ROWS_INCOMPLETE")
    known_target = [isinstance(r[4], (int, float)) for r in rows]
    if (
        not known_target
        or not known_target[0]
        or known_target != sorted(known_target, reverse=True)
    ):
        raise ValueError("FORECAST_PREFIX_HAS_INTERIOR_GAP")
    states = {}
    observations = []
    for state in range(4):
        states[state] = []
        for j, row in enumerate(rows):
            t = row[state + 1]
            if not isinstance(t, (int, float)):
                continue
            if not 0 <= t < 10000:
                raise ValueError("STATE_ORDER_COORDINATE_OVERLAP")
            item = {
                "observation_id": f"S{state}-U{j}",
                "entity_id": "BATTERY-1",
                "observed_at": state * 10000 + float(t),
                "available_at": state * 10000 + float(t),
                "value": float(t),
                "voltage_V": float(row[0]),
            }
            observations.append(item)
            states[state].append(item)
    samples = []
    for state in (1, 2, 3):
        for cut in (9.95, 9.85, 9.765) if state < 3 else (9.765,):
            prefix = [r for r in states[state] if r["voltage_V"] >= cut - 1e-10]
            before = [r["observation_id"] for s in range(state) for r in states[s]]
            ids = [r["observation_id"] for r in prefix]
            samples.append(
                {
                    "sample_id": f"S{state}-CUT-{cut}" if state < 3 else "S3-LAST",
                    "entity_id": "BATTERY-1",
                    "origin": prefix[-1]["observed_at"],
                    "target_time": states[state][-1]["observed_at"] if state < 3 else None,
                    "target_event": "discharge voltage reaches 9 V",
                    "split": "VALIDATION" if state < 3 else "FORECAST",
                    "target_observation_id": states[state][-1]["observation_id"]
                    if state < 3
                    else None,
                    "feature_observation_ids": ids,
                    "preprocess_fit_observation_ids": before + ids,
                    "model_fit_observation_ids": before + ids,
                }
            )
    path = "data/processed/temporal_index.json"
    core.write_json(
        root / path,
        {
            "schema_version": "provided-observation-index/v1",
            "observations": observations,
            "provenance": {
                "source_path": "data/raw/appendix.xlsx",
                "source_sha256": core.file_hash(root / "data/raw/appendix.xlsx"),
            },
            "coordinate": "10000*state+elapsed_min; ordering coordinate, not calendar",
        },
    )
    return {
        "schema_version": "temporal-visibility/v1",
        "task": "SAME_ENTITY_FUTURE",
        "time_unit": "min",
        "index_path": path,
        "samples": samples,
    }


def put(core, root, key, body):
    core.write_json(root / core.ARTIFACT_PATHS[key], core.artifact(key, body))


def advance(core, root, target):
    for _ in range(20):
        if core.load_state(root)["state"] == target:
            return
        core.advance_once(root)
    raise ValueError("STATE_TARGET_NOT_REACHED")


def prepare(year, subject):
    core = load_core()
    own = PHASE / CASES[year]
    design = core.load_json(own / "development_design.json")
    root = REPO / design["case_root"]
    if root.exists():
        raise ValueError("NEW_CHILD_ROOT_ALREADY_EXISTS")
    if (
        subprocess.check_output(["git", "rev-parse", subject], cwd=REPO, text=True).strip()
        != subject
    ):
        raise ValueError("EXACT_SUBJECT_SHA_REQUIRED")
    binding = core.load_json(own / "registration/case_registration.json")
    if binding["shared_subject"] != subject:
        raise ValueError("SHARED_SUBJECT_REGISTRATION_MISMATCH")
    core.initialize_case(root, CASES[year], "general")
    parent = PARENTS[year]
    audit = copy.deepcopy(core.read_artifact(parent, "data_audit")["content"])
    for relative, expected in audit["data_hashes"].items():
        source = parent / relative
        if core.file_hash(source) != expected:
            raise ValueError("PARENT_INPUT_HASH_MISMATCH")
        dest = root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        dest.chmod(0o444)
    requirements = copy.deepcopy(core.read_artifact(parent, "problem_requirements")["content"])
    requirements["case_id"] = CASES[year]
    requirements["development_provenance"] = binding
    definitions = metric_definitions(year)
    temporal = temporal_index(root, core) if year == 2016 else None
    if temporal:
        audit["data_hashes"][temporal["index_path"]] = core.file_hash(root / temporal["index_path"])
        audit["leakage_findings"] = [
            {
                "prior_exposure": "Known parent inputs/results; not blind evidence.",
                "current_design": "Origin-specific development and conditional forecast.",
                "answer_access": "NOT_ACCESSED",
            }
        ]
    for req in requirements["requirements"]:
        rid = req["requirement_id"]
        if year == 2016:
            mids = {
                "REQ-Q1": ["q1_mean_fitted_MRE"],
                "REQ-Q2": ["q2_loco_MRE"],
                "REQ-Q3": ["q3_remaining_MRE", "q3_remaining_min"],
            }[rid]
            req["minimum_data_fields"] = (
                ["voltage_V", "elapsed_min"]
                if rid == "REQ-Q3"
                else ["current_A", "voltage_V", "elapsed_min"]
            )
            req["accuracy_scope"] = (
                "Conditional calculation; historical diagnostics; target accuracy UNKNOWN."
            )
            if rid != "REQ-Q1":
                req["prediction_spec"] = {
                    "kind": "CONDITIONAL_ESTIMATE",
                    "claim_type": "PREDICTIVE",
                    "prediction_axis": "CONDITION_INTERPOLATION"
                    if rid == "REQ-Q2"
                    else "TIME_CONTINUATION",
                    "target_field": "55A_discharge_duration"
                    if rid == "REQ-Q2"
                    else "future_remaining_time",
                    "future_truth_field": "measured_55A_duration"
                    if rid == "REQ-Q2"
                    else "state3_terminal_elapsed_min",
                    "known_input_fields": req["minimum_data_fields"],
                    "model_basis": "Within-range current interpolation"
                    if rid == "REQ-Q2"
                    else "Prior-state trajectory transfer fitted to observed target prefix",
                    "conditions": [
                        "Conditions and aging/current transfer persist without regime change."
                    ],
                    "historical_validation_required": True,
                    "empirical_accuracy_required": False,
                }
                if rid == "REQ-Q3":
                    req["prediction_spec"]["conditions"].append(
                        "Discharge states share one constant current; its numeric value is unknown."
                    )
        elif rid == "REQ-DEFINITION":
            mids = ["definition_tree_angle_deg", "definition_calendar_rows"]
        elif rid == "REQ-VALIDATION":
            mids = ["reference_altitude_rmse_deg", "reference_altitude_max_abs_deg"]
        else:
            mids = [rid[4:].title() + "_event_count"]
        req["metric_contracts"] = {m: definitions[m] for m in mids}
    put(core, root, "problem_requirements", requirements)
    for key in ("research_plan", "source_ledger", "assumptions_and_symbols", "model_candidates"):
        body = copy.deepcopy(core.read_artifact(parent, key)["content"])
        if key == "research_plan":
            body.update(
                mode="POSTVALIDATION_DEVELOPMENT",
                external_search=False,
                parent_terminal_sha256=design["parent_terminal_sha256"],
            )
        if key == "assumptions_and_symbols":
            body["assumptions"].extend(design["scientific_limits"])
        if key == "model_candidates":
            body["baseline_definition"] = (
                "Frozen two-candidate portfolio; minimum preregistered primary metric, then ID."
            )
        put(core, root, key, body)
    suff = copy.deepcopy(core.read_artifact(parent, "data_sufficiency")["content"])
    suff["requirements"] = requirements["requirements"]
    suff["sources"] = core.read_artifact(root, "source_ledger")["content"]["sources"]
    if year == 2016:
        suff["interpretation"] = (
            "Conditional inputs suffice; 55A and state3 target accuracy unverified."
        )
        for row in suff["requirement_assessments"]:
            row.update(
                data_sufficiency_status="SUFFICIENT",
                missing_fields=[],
                missing_entities=[],
                missing_time_scope=[],
                candidate_sources=[],
                affected_downstream_stages=[],
            )
    put(core, root, "data_sufficiency", suff)
    put(core, root, "data_audit", audit)
    advance(core, root, "MODELS_PROPOSED")
    probe = copy.deepcopy(
        core.load_json(parent / "experiments/selected_output_contract_probe.json")
    )
    core.write_json(root / "experiments/selected_output_contract_probe.json", probe)
    subprocess.run(
        [
            sys.executable,
            str(CORE),
            "preflight-output",
            "--case-root",
            str(root),
            "--path",
            "experiments/selected_output_contract_probe.json",
        ],
        cwd=REPO,
        check=True,
    )
    producer = "produce.py" if year == 2016 else "solve.py"
    code = [
        {
            "scope": "SKILL_ROOT",
            "path": "scripts/cumcm_case.py",
            "repository_path": CORE.relative_to(REPO).as_posix(),
            "sha256": core.file_hash(CORE),
        }
    ]
    for name in (producer, "check.py"):
        source = own / "code" / name
        shutil.copyfile(source, root / "models" / name)
        code.append(
            {
                "scope": "CASE_ROOT",
                "path": "models/" + name,
                "repository_path": source.relative_to(REPO).as_posix(),
                "sha256": core.file_hash(source),
            }
        )
    plan = copy.deepcopy(core.read_artifact(parent, "experiment_plan")["content"])
    plan.update(
        code_commit=subject,
        required_code_files=code,
        required_input_hashes=audit["data_hashes"],
        random_seeds=design["seeds"],
        metric=design["selection_metric"],
        metric_definitions=definitions,
        handoff_generated_at=core.utc_now(),
        stop_rule=(
            "Two candidates; 4 model starts; 4 checker starts including replays; "
            "1 Final; no post-Final tuning. Deadline 2026-09-09T08:35:18Z."
        ),
    )
    plan["evaluation_design"].update(
        mode="CONDITIONAL_PREDICTION_FINAL_VERIFICATION"
        if year == 2016
        else "NONPREDICTIVE_FINAL_VERIFICATION",
        start_budget=design["budget"],
        development_design_sha256=core.file_hash(own / "development_design.json"),
        independent_validation=False,
    )
    plan["splits"] = {"train": [], "validation": [], "test": []}
    if temporal:
        plan["temporal_design"] = temporal
        plan["condition_design"] = {
            "REQ-Q2": {
                "schema_version": "condition-query/v1",
                "queries": [
                    {
                        "sample_id": "55A",
                        "entity_id": "BATTERY-1",
                        "origin": 0,
                        "conditions": {"current_A": 55},
                    }
                ],
                "historical_sample_ids": [f"LOCO-{i}" for i in range(30, 91, 10)],
            }
        }
        plan["splits"].update(
            train=["PRIOR_STATE_AND_TARGET_PREFIX"],
            validation=[s["sample_id"] for s in temporal["samples"] if s["split"] == "VALIDATION"],
        )
    h = core.canonical_hash
    plan["trusted_freeze_registry"] = {
        "candidate_set": h(plan["candidate_ids"]),
        "metric": h(core.metric_freeze_payload(plan)),
        "seed_schedule": h(plan["random_seeds"]),
        "split_assignment": h(plan["splits"]),
        "baseline": h(plan["baseline_id"]),
        "input_set": h(plan["required_input_hashes"]),
        "execution_policy": h(
            core.execution_policy_payload(
                plan["stop_rule"], plan["handoff_generated_at"], plan["evaluation_design"]
            )
        ),
        "code_set": h(code),
        "code_commit": h(subject),
    }
    put(core, root, "experiment_plan", plan)
    advance(core, root, "EXPERIMENT_PLAN_VALIDATED")
    core.trusted_freezes(root)
    core.write_json(
        root / "evidence/new_child_preparation.json",
        {
            "case_id": CASES[year],
            "shared_subject": subject,
            "created_at": core.utc_now(),
            "parent_input_hashes": audit["data_hashes"],
            "model_processes_started": 0,
            "registration_sha256": core.file_hash(own / "registration/case_registration.json"),
        },
        overwrite=False,
    )
    print(
        json.dumps(
            {
                "case_id": CASES[year],
                "state": core.load_state(root)["state"],
                "root": design["case_root"],
            }
        )
    )


def propose(year):
    core = load_core()
    design = core.load_json(PHASE / CASES[year] / "development_design.json")
    root = REPO / design["case_root"]
    if core.load_state(root)["state"] != "RUNNING":
        raise ValueError("PROPOSAL_REQUIRES_ACTUAL_DEVELOPMENT_RUNS")
    plan = core.read_artifact(root, "experiment_plan")["content"]
    attempts = core._development_attempt_registry(root, plan)
    choice = core.select_development_candidate(attempts, plan)
    selected = [a for a in attempts if a["candidate_id"] == choice["selected_candidate_id"]]
    if len(selected) != 1:
        raise ValueError("ONE_SEED_SHARED_PORTFOLIO_REQUIRED")
    item = selected[0]
    rid = item["run_id"]
    manifest = core.build_captured_run_manifest(
        root, run_id=rid, decision_hash=core.canonical_hash(choice)
    )
    output = core.load_json(root / "runs" / rid / "output.json")
    reqs = core.read_artifact(root, "problem_requirements")["content"]["requirements"]
    ids = [r["requirement_id"] for r in reqs]
    rec = {
        "run_id": rid,
        "outcome": "SUCCESS",
        "sealed": True,
        "current": True,
        "supported_requirement_ids": ids,
        "selected_output_ids": ["OUT-" + i for i in ids],
        "metric_ids": list(output["final_metrics"]),
        "input_hash": manifest["input_hash"],
        "scenario_hash": manifest["scenario_hash"],
        "configuration_hash": manifest["configuration_hash"],
        "policy_exposure": 0,
    }
    selection = {
        "contract_version": "requirement-selection/v1",
        "requirements": [
            {
                "requirement_id": r["requirement_id"],
                "selection_metric": next(iter(r["metric_contracts"])),
                "selection_direction": "MIN",
                "dependency_requirements": r["dependency_requirements"],
                "dependency_bindings": [],
                "cross_requirement_constraints": [],
            }
            for r in reqs
        ],
        "runs": [rec],
        "selection": {
            "selection_mode": "GLOBAL_JOINT",
            "requirement_to_run_map": {i: [rid] for i in ids},
            "requirement_to_output_map": {i: ["OUT-" + i] for i in ids},
            "shared_input_hashes": [rec["input_hash"]],
            "shared_scenario_hashes": [rec["scenario_hash"]],
            "compatibility_checks": ["INPUT", "SCENARIO", "CONSTRAINTS"],
            "compatibility": {
                "kind": "RUN_PORTFOLIO_V1",
                "version": "compatibility/v1",
                "ordered_ids": ids,
                "permuted_ids": list(reversed(ids)),
            },
            "dependency_bridges": [],
            "cross_requirement_constraints": [],
            "aggregate_objective": "Minimum preregistered primary metric for common portfolio",
            "tradeoff_rule": "ARGMIN_THEN_ID; preserve requirement-specific outputs and limits",
            "limitations": output["limitations"],
        },
    }
    claims, outputs = [], []
    for req in reqs:
        key = req["requirement_id"]
        facts = output["scientific_evidence"][key]
        predictive = "prediction_spec" in req
        ctype = (
            "PREDICTIVE"
            if predictive
            else "EMPIRICAL"
            if year == 2016
            else "DESCRIPTIVE"
            if key == "REQ-VALIDATION"
            else "SIMULATION_CONDITIONAL"
        )
        uncertainty = (
            facts["prediction_evidence"]["uncertainty"] if predictive else output["uncertainty"]
        )
        claim = {
            "claim_id": output["requirement_claims"][key]["claim_id"],
            "requirement_id": key,
            "claim_type": ctype,
            "statement": output["requirement_claims"][key]["claim_text"],
            "scope": facts["scope"],
            "evidence_class": "PROVIDED_EMPIRICAL" if year == 2016 else "THEORETICAL",
            "selected_run_ids": [rid],
            "selected_output_ids": ["OUT-" + key],
            "metric_ids": list(facts["metric_values"]),
            "comparator_ids": [],
            "support_predicates": {
                "scope_bounded": True,
                "registered_assumptions_bound": ctype == "SIMULATION_CONDITIONAL",
                "empirical_data_present": year == 2016,
            },
            "uncertainty": uncertainty,
            "counter_evidence": [],
            "limitations": output["limitations"],
            "status": "SUPPORTED",
            "claim_strength": "BOUNDED",
        }
        if predictive:
            claim["prediction_scope"] = "CONDITIONAL_ESTIMATE"
            claim["support_predicates"].update(
                validation_boundary_frozen=True,
                conditional_model_bound=True,
                historical_validation_recorded=True,
                held_out_test_valid=False,
                target_accuracy_verified=False,
            )
        claims.append(claim)
        outputs.append(
            {
                "output_id": "OUT-" + key,
                "metric_ids": list(facts["metric_values"]),
                "owner_run_id": rid,
                "requirement_id": key,
            }
        )
    semantic = {
        "contract_version": "claim-evidence/v3",
        "claims": claims,
        "runs": [rec],
        "outputs": outputs,
        "comparators": [],
        "validation": {"counter_evidence_detected": False},
        "aggregate": {
            "primary_requirement_ids": ids,
            "supported_requirement_ids": ids,
            "requirement_claim_ids": {c["requirement_id"]: c["claim_id"] for c in claims},
        },
    }
    put(core, root, "requirement_selection", selection)
    put(core, root, "semantic_claim_support", semantic)
    core.write_json(
        root / "evidence/proposal_creation.json",
        {
            "created_at": core.utc_now(),
            "selected_candidate_id": choice["selected_candidate_id"],
            "selected_run_id": rid,
            "selection_decision_hash": core.canonical_hash(choice),
            "accepted_scientific_gates": False,
        },
        overwrite=False,
    )
    print(json.dumps({"status": "PROPOSED_FOR_COMMON_CONTROLLER", "selected_run_id": rid}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "propose"])
    parser.add_argument("--year", type=int, choices=[2016, 2015], required=True)
    parser.add_argument("--subject")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.year, args.subject)
    else:
        propose(args.year)


if __name__ == "__main__":
    main()
