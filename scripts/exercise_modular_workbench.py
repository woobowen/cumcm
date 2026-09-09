"""Explicit BUILD_AND_ACCEPT original exercise; never a future user's automatic workflow."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/cumcm-modeling-evidence/scripts"
sys.path.insert(0, str(SCRIPTS))
import cumcm_case as core  # noqa: E402
import synthetic_cases as synthetic  # noqa: E402


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load("tests/integration/test_actual_controller_neutral_e2e.py", "water_contract_builders")
SCIENCE = load("tests/integration/test_rc9_science_semantics.py", "water_temporal_builder")
SEED = 20260906


def accepted(root, kind, value):
    core.write_json(root / core.ARTIFACT_PATHS[kind], core.artifact(kind, value))


def cli(root, *args):
    started = core.utc_now()
    process = subprocess.run(
        [sys.executable, str(SCRIPTS / "cumcm_workbench.py"), *args, "--case-root", str(root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    events = root.parent / (root.name + "-commands.jsonl")
    try:
        result = json.loads(process.stdout)
    except ValueError:
        result = {"unparsed_stdout": process.stdout, "stderr": process.stderr}
    record = {
        "argv": ["PYTHON", "WORKBENCH", *args, "--case-root", "CASE_ROOT"],
        "started_at": started,
        "ended_at": core.utc_now(),
        "exit_code": process.returncode,
        "result_sha256": core.canonical_hash(result),
        "result_status": result.get("status"),
        "implementation_commit": core.current_git_commit(),
    }
    with events.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    if process.returncode:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    return result


def case_data(kind):
    raw, temporal = SCIENCE.temporal_data(kind)
    raw.update(
        kind=kind,
        threshold=10,
        baseline_delay=1,
        flow_litres_per_minute=1,
        fixed_demand_litres=8,
        containers=[{"litres": 3, "cost": 4}, {"litres": 5, "cost": 7}],
        provenance="PROJECT_ORIGINAL_SYNTHETIC_TRAJECTORY_NOT_EMPIRICAL",
    )
    return raw, temporal


def requirements_for(kind):
    ids = ["REQ-A", "REQ-B", "REQ-C"] if kind == "mixed" else ["REQ-A", "REQ-B"]
    reqs = []
    for index, rid in enumerate(ids):
        predictive = kind == "prediction" or (kind == "mixed" and rid == "REQ-B")
        req = H._requirement(
            rid,
            evidence_class="SIMULATION",
            fields=["time", "level", "containers"],
            simulation_allowed=True,
        )
        definition = SCIENCE.metric(predictive=predictive)
        if not predictive:
            definition.update(
                target="purchase_cost" if rid == "REQ-A" else "terminal_stock",
                target_unit="yuan" if rid == "REQ-A" else "L",
                unit="yuan" if rid == "REQ-A" else "L",
            )
        else:
            definition.update(target="water_remaining_time")
            req["prediction_spec"] = {
                "kind": "CONDITIONAL_ESTIMATE",
                "claim_type": "PREDICTIVE",
                "target_field": "future_remaining_time",
                "future_truth_field": "future_end_time",
                "known_input_fields": ["time", "level"],
                "model_basis": "Prefix-only affine level model continued to declared threshold",
                "conditions": ["Affine trend continues; no regime change."],
                "historical_validation_required": True,
                "empirical_accuracy_required": False,
            }
        if kind == "mixed":
            req["dependency_requirements"] = {
                "REQ-A": ["REQ-B"],
                "REQ-B": [],
                "REQ-C": ["REQ-A", "REQ-B"],
            }[rid]
        req.update(
            metric_contracts={f"metric_{chr(97 + index)}": definition},
            scientific_facts_required=True,
        )
        reqs.append(req)
    return reqs


def build_plan(root, kind, temporal):
    frozen = cli(
        root, "freeze-code", "--code", "models/runtime_model.py", "models/independent_check.py"
    )
    reqs = core.read_artifact(root, "problem_requirements")["content"]["requirements"]
    plan = {
        "preregistered": True,
        "execution_prepared": True,
        "candidate_ids": ["BASE", "CAND"],
        "baseline_id": "BASE",
        "metric": "metric_a",
        "metric_direction": "MIN",
        "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        "selection_rule": "ARGMIN_THEN_ID",
        "random_seeds": [SEED],
        "splits": {"train": [], "validation": [], "test": []},
        "required_input_hashes": core.read_artifact(root, "data_audit")["content"]["data_hashes"],
        "required_code_files": synthetic._required_code_files(core) + frozen["code_files"],
        "code_commit": core.current_git_commit(),
        "stop_rule": "one actual run per candidate",
        "handoff_generated_at": core.utc_now(),
        "metric_definitions": {k: v for r in reqs for k, v in r["metric_contracts"].items()},
        "evaluation_design": {"mode": "NONPREDICTIVE_FINAL_VERIFICATION"},
    }
    if kind != "optimization":
        plan.update(
            temporal_design=temporal,
            evaluation_design={"mode": "CONDITIONAL_PREDICTION_FINAL_VERIFICATION"},
            splits={"train": ["PREFIX"], "validation": ["A-origin-4", "A-origin-8"], "test": []},
        )
    freezes = synthetic._freezes(
        core,
        plan["candidate_ids"],
        plan["metric"],
        plan["splits"],
        plan["baseline_id"],
        plan["required_input_hashes"],
        plan["stop_rule"],
        plan["handoff_generated_at"],
        plan["required_code_files"],
        plan["code_commit"],
    )
    freezes["seed_schedule"] = core.canonical_hash([SEED])
    freezes["metric"] = core.canonical_hash(core.metric_freeze_payload(plan))
    freezes["execution_policy"] = core.canonical_hash(
        core.execution_policy_payload(
            plan["stop_rule"], plan["handoff_generated_at"], plan["evaluation_design"]
        )
    )
    plan["trusted_freeze_registry"] = freezes
    accepted(root, "experiment_plan", plan)
    synthetic._write_output_contract_probe(
        core, root, [r["requirement_id"] for r in reqs], metric="metric_a"
    )


def proposals(root, kind):
    reqs = core.read_artifact(root, "problem_requirements")["content"]["requirements"]
    mapping = {
        r["requirement_id"]: (
            "BASE" if kind == "mixed" and r["requirement_id"] == "REQ-B" else "CAND"
        )
        for r in reqs
    }
    types = {
        r["requirement_id"]: (
            "PREDICTIVE"
            if "prediction_spec" in r
            else "OPTIMALITY"
            if r["requirement_id"] == "REQ-A"
            else "FEASIBILITY"
        )
        for r in reqs
    }
    raw_hash = core.file_hash(root / "data/raw/input.json")
    input_hash = core.canonical_hash([raw_hash])
    scenario = core.resolve_scenario_identity(root)
    bridges = []
    for req in reqs:
        for parent in req["dependency_requirements"]:
            bridge = {
                "dependency_requirement_id": parent,
                "dependent_requirement_id": req["requirement_id"],
                "upstream_run_ids": [f"RUN-{mapping[parent]}-{SEED}"],
                "downstream_run_ids": [f"RUN-{mapping[req['requirement_id']]}-{SEED}"],
                "input_hash": input_hash,
                "scenario_hash": scenario,
            }
            bridge["lineage_hash"] = core.canonical_hash(bridge)
            bridges.append(bridge)
    selection, semantic = H._selection_and_semantic(
        core,
        reqs,
        raw_hash,
        mode="JOINT_PORTFOLIO" if kind == "mixed" else "GLOBAL_JOINT",
        selected_candidates=mapping,
        dependency_bridges=bridges,
        claim_types=types,
        evidence_classes={r["requirement_id"]: "SIMULATION" for r in reqs},
    )
    for record in (selection, semantic):
        for run in record["runs"]:
            run["scenario_hash"] = scenario
    selection["selection"]["shared_scenario_hashes"] = [scenario]
    for claim in semantic["claims"]:
        if claim["claim_type"] == "PREDICTIVE":
            claim["prediction_scope"] = "CONDITIONAL_ESTIMATE"
            claim["support_predicates"].update(
                validation_boundary_frozen=True,
                conditional_model_bound=True,
                historical_validation_recorded=True,
                held_out_test_valid=False,
                target_accuracy_verified=False,
            )
            claim["uncertainty"] = {"kind": "UNCALIBRATED_POINT_ESTIMATE", "calibrated": False}
        elif claim["claim_type"] == "OPTIMALITY":
            claim["claim_strength"] = "GLOBAL_OPTIMUM"
            claim["support_predicates"]["global_optimality_certificate"] = True
        else:
            claim["support_predicates"]["independent_constraint_recalculation"] = True
    accepted(root, "requirement_selection", selection)
    accepted(root, "semantic_claim_support", semantic)


def exercise(root, kind, stop_after):
    root.parent.mkdir(parents=True, exist_ok=True)
    raw, temporal = case_data(kind)
    case_id = "ORIGINAL-WATER-" + kind.upper()
    if not core.state_path(root).exists():
        cli(root, "init", "--case-id", case_id, "--kind", "general")
        core.write_json(root / "data/raw/input.json", raw, overwrite=False)
        (root / "problem/original.md").write_text(
            "项目原创合成备水题。完整题意、逐问与条件见research/analysis.md。\n"
            "水位到10 L后需按1 L/min备水；3 L容器4元，5 L容器7元。\n"
            f"本次类型：{kind}。不得宣称真实未来精度。\n"
        )
        shutil.copyfile(
            ROOT / "evals/results/modular-workbench-001/original_analysis.md",
            root / "research/analysis.md",
        )
    reqs = requirements_for(kind)
    for index in range(1, int(stop_after[1:]) + 1):
        mid, rid = f"M{index:02}", f"WATER-M{index:02}"
        if (root / "evidence/module_requests" / rid / "completion.json").exists():
            # Always verify, never trust file existence after a code/input change.
            existing = cli(root, "status")
            row = next(r for r in existing["modules"] if r["request_id"] == rid)
            if row["status"] != "COMPLETED":
                raise ValueError("EXERCISE_EXISTING_REQUEST_" + row["status"])
            continue
        cli(root, "prepare", "--module", mid, "--scope", "ALL", "--request-id", rid)
        artifacts = ["research/analysis.md"]
        if mid == "M01":
            artifacts += ["problem/original.md", "data/raw/input.json"]
        elif mid == "M02":
            accepted(
                root,
                "problem_requirements",
                {
                    "contract_version": "requirement-evidence/v1",
                    "case_id": case_id,
                    "requirements": reqs,
                },
            )
        elif mid == "M03":
            accepted(
                root,
                "research_plan",
                {
                    "mode": "OFFLINE_PROJECT_ORIGINAL",
                    "questions": [
                        "prefix formula",
                        "positive-cost finite bound",
                        "mass conservation",
                    ],
                    "external_search": False,
                    "analysis_path": "research/analysis.md",
                },
            )
            source = H._source(
                "SRC-ORIGINAL-WATER",
                [r["requirement_id"] for r in reqs],
                core.file_hash(root / "data/raw/input.json"),
                evidence_class="SIMULATION",
                fields=["time", "level", "containers"],
            )
            source.update(
                provenance="PROJECT_ORIGINAL_SYNTHETIC_NO_EMPIRICAL_CLAIM",
                retrieval_time=core.utc_now(),
            )
            accepted(
                root,
                "source_ledger",
                {
                    "contract_version": "requirement-evidence/v1",
                    "sources": [source],
                    "answer_access_status": "NOT_ACCESSED",
                },
            )
        elif mid == "M04":
            accepted(
                root,
                "assumptions_and_symbols",
                {
                    "assumptions": [
                        "strict affine synthetic trajectory continues",
                        "fixed unit flow",
                        "positive integer prices and unlimited stock; no leakage",
                    ],
                    "symbols": {"n3,n5": "integer counts", "d": "L", "T,t": "min", "cost": "yuan"},
                    "formulas": ["min 4*n3+7*n5; 3*n3+5*n5>=ceil((T-t)*flow)", "s(t)=s(0)-t"],
                },
            )
            artifacts += [core.ARTIFACT_PATHS["assumptions_and_symbols"]]
        elif mid == "M05":
            accepted(
                root,
                "data_audit",
                {
                    "raw_immutable": True,
                    "data_hashes": {
                        "data/raw/input.json": core.file_hash(root / "data/raw/input.json")
                    },
                },
            )
            sources = core.read_artifact(root, "source_ledger")["content"]["sources"]
            accepted(
                root,
                "data_sufficiency",
                {
                    "contract_version": "data-sufficiency/v1",
                    "requirements": reqs,
                    "sources": sources,
                    "acquisition_plans": [],
                    "source_compositions": [],
                    "aggregate_completion_claimed": False,
                    "coverage_mode_by_requirement": {
                        r["requirement_id"]: {
                            "mode": "SINGLE_SOURCE",
                            "source_id": sources[0]["source_id"],
                        }
                        for r in reqs
                    },
                    "requirement_assessments": [H._assessment(r["requirement_id"]) for r in reqs],
                },
            )
        elif mid == "M06":
            accepted(
                root,
                "model_candidates",
                {
                    "candidates": [
                        {
                            "candidate_id": "BASE",
                            "baseline": True,
                            "method": "all-small feasible purchase",
                        },
                        {
                            "candidate_id": "CAND",
                            "baseline": False,
                            "method": "dynamic programming",
                        },
                    ]
                },
            )
        elif mid == "M07":
            for source, dest in [("model", "runtime_model"), ("checker", "independent_check")]:
                shutil.copyfile(
                    ROOT / f"tests/fixtures/workbench_water_{source}.py", root / f"models/{dest}.py"
                )
                artifacts += [f"models/{dest}.py"]
        elif mid == "M08":
            build_plan(root, kind, temporal)
        elif mid == "M09":
            for candidate in ["BASE", "CAND"]:
                run = f"RUN-{candidate}-{SEED}"
                cli(
                    root,
                    "run",
                    "--request",
                    rid,
                    "--operation",
                    "model",
                    "--candidate",
                    candidate,
                    "--seed",
                    str(SEED),
                    "--run-id",
                    run,
                    "--code",
                    "models/runtime_model.py",
                )
                cli(
                    root,
                    "run",
                    "--request",
                    rid,
                    "--operation",
                    "checker",
                    "--run-id",
                    run,
                    "--code",
                    "models/independent_check.py",
                )
                artifacts += [f"runs/{run}/output.json", f"runs/{run}/scientific_check.json"]
        elif mid >= "M10":
            if mid == "M10":
                proposals(root, kind)
            cli(root, "run", "--request", rid, "--operation", "controller")
        template = core.load_json(
            root / "evidence/module_requests" / rid / "work-report.template.json"
        )
        template.update(
            summary_cn=f"{mid}原创{kind}备水案例；动作和科学边界见所附分析及当前真实产物。",
            original_requirements=["条件预测、正价格整数采购、逐分钟守恒；按本次类型适用范围。"],
            actions=["主Agent编写分析与代码；建设脚本复用已审阅材料并调用公共CLI。"],
            artifacts=artifacts,
            checks=["当前模块公共CLI与原生状态检查；数值证据仅以实际Run/checker为准。"],
            negative_results=["合成资料，不证明真实未来精度；真实网页/队员核验NOT_RUN。"],
            review_questions=["本模块数据、公式、边界和独立核验是否与原问一致？"],
            scientific_scope=(
                "分析/设计，待数值验证" if index < 9 else "仅本次原创合成条件模型，见实际核验产物"
            ),
        )
        core.write_json(root / f"work/{mid}.json", template)
        result = cli(root, "complete", "--request", rid, "--report", f"work/{mid}.json")
        assert result["next_module_started"] is False
        print(
            json.dumps(
                {
                    "module": mid,
                    "native_state": result["native_state"],
                    "package": result["review_package"]["package_hash"],
                }
            ),
            flush=True,
        )
    return cli(root, "status")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-exercise", action="store_true", required=True)
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--kind", choices=["mixed", "optimization", "prediction"], required=True)
    parser.add_argument("--stop-after", choices=[f"M{i:02}" for i in range(1, 15)], default="M14")
    args = parser.parse_args()
    exercise(args.case_root.resolve(), args.kind, args.stop_after)


if __name__ == "__main__":
    main()
