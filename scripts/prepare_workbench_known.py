"""Register and prepare one authorized known Q3 child. Never starts model/checker/Final."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "evals/results/modular-workbench-001"
sys.path.insert(0, str(REPO / ".agents/skills/cumcm-modeling-evidence/scripts"))
import cumcm_case as core  # noqa: E402
import synthetic_cases as synthetic  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "known_temporal_preparation", REPO / "scripts/prepare_phase004c6_development.py"
)
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
PARENT = REPO / ".cache/pr12-rc8/fresh/2016/case-r2"
BUDGET = {"model_cli_starts": 4, "independent_checker_starts": 6, "final_starts": 1}


def cid(revision):
    return f"CUMCM-2016-C-MODULE-USABILITY-DEVELOPMENT-008-R{revision}"


def register(revision, subject):
    if subject != core.current_git_commit():
        raise ValueError("EXACT_CURRENT_IMPLEMENTATION_SUBJECT_REQUIRED")
    case_id = cid(revision)
    own = BASE / case_id
    registry = yaml.safe_load((REPO / "benchmarks/case_registry.yaml").read_text())
    if any(c["case_id"] == case_id for c in registry["cases"]):
        raise ValueError("CASE_ALREADY_REGISTERED_USE_EXISTING_OR_AUTHORIZED_NEXT_REVISION")
    parent = next(c for c in registry["cases"] if c["case_id"] == "CUMCM-2016-C-VALIDATION-004")
    original_hashes = core.read_artifact(PARENT, "data_audit")["content"]["data_hashes"]
    for path, expected in original_hashes.items():
        if not (PARENT / path).is_file() or core.file_hash(PARENT / path) != expected:
            raise ValueError("ORIGINAL_INPUT_MISSING_OR_CHANGED_NOT_RUN")
    root = f".cache/modular-workbench-001/known/2016-q3-r{revision}"
    design = {
        "schema_version": "module-usability-development-design/v1",
        "case_id": case_id,
        "case_root": root,
        "revision": revision,
        "maximum_revisions": 2,
        "budget": BUDGET,
        "required_question_ids": ["REQ-Q3"],
        "independent_validation": False,
        "purpose": "Default scenario public-path closure, no model improvement claim",
        "candidates": ["BASELINE", "AFFINE"],
        "seeds": [20260909],
        "selection_metric": "q3_remaining_MRE",
        "created_at": core.utc_now(),
        "planned_starts": {"models": 2, "development_checks": 2, "independent_final": 1},
        "parent_terminal_sha256": core.file_hash(REPO / parent["terminal_decision"]),
        "scientific_limits": [
            "One known battery; six correlated historical origins.",
            "State3 endpoint unknown; no real future accuracy or whole-question acceptance.",
            "Q1/Q2 are excluded. No answer/reference search or unlock.",
        ],
    }
    core.write_json(own / "development_design.json", design, overwrite=False)
    case = {k: copy.deepcopy(parent[k]) for k in registry["required_case_fields"]}
    case.update(
        case_id=case_id,
        set_type="DEVELOPMENT",
        evidence_role="MODULE_USABILITY_DEVELOPMENT",
        independent_problem=False,
        contamination_status="KNOWN_PROBLEM_AND_PRIOR_RESULTS",
        parent_case_id=parent["case_id"],
        parent_terminal_sha256=design["parent_terminal_sha256"],
        case_root=root,
        skill_version=core.VERSION,
        skill_commit=subject,
        model="CURRENT_MAIN_AGENT",
        reasoning="CURRENT_SESSION_NOT_INFERRED",
        first_run_status="NOT_STARTED",
        start_time=None,
        freeze_time=None,
        unlock_time=None,
        generalizable_failures=[],
        problem_specific_findings=[],
        answer_access_status="SEALED",
        data_hashes=original_hashes,
    )
    registration = {
        **copy.deepcopy(case),
        "schema_version": "module-usability-development-registration/v1",
        "phase": "PHASE-SKILL-MODULAR-WORKBENCH-004C7",
        "authorization_path": "CUMCM_MODULAR_WORKBENCH_BUILD_PROMPT.md",
        "authorization_sha256": core.file_hash(REPO / "CUMCM_MODULAR_WORKBENCH_BUILD_PROMPT.md"),
        "parent_terminal_path": parent["terminal_decision"],
        "budget": BUDGET,
        "required_question_ids": ["REQ-Q3"],
        "shared_subject": subject,
        "development_design_sha256": core.file_hash(own / "development_design.json"),
        "registered_at": core.utc_now(),
    }
    relative = f"evals/results/modular-workbench-001/{case_id}/registration/case_registration.json"
    core.write_json(REPO / relative, registration, overwrite=False)
    case["registration"] = {"path": relative, "sha256": core.file_hash(REPO / relative)}
    with (REPO / "benchmarks/case_registry.yaml").open("a") as handle:
        handle.write(yaml.safe_dump([case], allow_unicode=True, sort_keys=False))
    return {"status": "REGISTERED_NOT_RUN", "case_id": case_id, "subject_commit": subject}


def prepare(revision):
    case_id = cid(revision)
    own = BASE / case_id
    design = core.load_json(own / "development_design.json")
    registration_path = own / "registration/case_registration.json"
    registration = core.load_json(registration_path)
    from cumcm_skill_lab.training_registry import repository_registry_errors

    registry = yaml.safe_load((REPO / "benchmarks/case_registry.yaml").read_text())
    errors = repository_registry_errors(REPO, registry)
    if errors:
        raise ValueError(";".join(errors))
    root = REPO / design["case_root"]
    if root.exists():
        raise ValueError("NEW_KNOWN_ROOT_ALREADY_EXISTS")
    subject = registration["skill_commit"]
    state = core.initialize_case(root, case_id, "prediction")
    policy = {
        "schema_version": "case-policy/v1",
        "case_id": case_id,
        "mode": "LAB_EVAL",
        "revision": revision,
        "execution_mode": "BUILD_AND_ACCEPT_EXERCISE",
        "automatic_publication": False,
        "budget_protocol": "MODULE_USABILITY_DEVELOPMENT_V1",
        "start_budget": BUDGET,
        "registration_sha256": core.file_hash(registration_path),
        "team_compliance_review": "NOT_RUN",
    }
    core.write_json(root / "state/case_policy.json", policy, overwrite=False)
    state["evidence_bindings"]["state/case_policy.json"] = core.file_hash(
        root / "state/case_policy.json"
    )
    core.write_json(core.state_path(root), state)
    for relative, expected in registration["data_hashes"].items():
        source = PARENT / relative
        if core.file_hash(source) != expected:
            raise ValueError("PARENT_INPUT_DRIFT")
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o444)
    temporal = legacy.temporal_index(root, core)
    req = next(
        copy.deepcopy(r)
        for r in core.read_artifact(PARENT, "problem_requirements")["content"]["requirements"]
        if r["requirement_id"] == "REQ-Q3"
    )
    req.update(
        minimum_data_fields=["voltage_V", "elapsed_min"],
        accuracy_scope="Conditional estimate only; state3 target accuracy UNKNOWN.",
        prediction_spec={
            "kind": "CONDITIONAL_ESTIMATE",
            "claim_type": "PREDICTIVE",
            "target_field": "future_remaining_time",
            "future_truth_field": "state3_terminal_elapsed_min",
            "known_input_fields": ["voltage_V", "elapsed_min"],
            "model_basis": (
                "Prior-state average trajectory scaled or affinely transferred using target prefix"
            ),
            "conditions": [
                "Same unknown constant current across aging states; transfer relation persists."
            ],
            "historical_validation_required": True,
            "empirical_accuracy_required": False,
        },
    )
    definitions = {k: v for k, v in legacy.metric_definitions(2016).items() if k.startswith("q3_")}
    req["metric_contracts"] = definitions
    legacy.put(
        core,
        root,
        "problem_requirements",
        {
            "contract_version": "requirement-evidence/v1",
            "case_id": case_id,
            "requirements": [req],
            "parent_scope_excluded": ["REQ-Q1", "REQ-Q2"],
        },
    )
    source = copy.deepcopy(core.read_artifact(PARENT, "source_ledger")["content"]["sources"][0])
    source["supports_requirement_ids"] = ["REQ-Q3"]
    legacy.put(
        core,
        root,
        "source_ledger",
        {
            "contract_version": "requirement-evidence/v1",
            "sources": [source],
            "answer_access_status": "NOT_ACCESSED",
        },
    )
    legacy.put(
        core,
        root,
        "research_plan",
        {
            "mode": "MODULE_USABILITY_DEVELOPMENT",
            "external_search": False,
            "questions": [
                "Does the default scenario path reach independent Final and bounded Q3 handoff?"
            ],
            "parent_terminal_sha256": design["parent_terminal_sha256"],
        },
    )
    legacy.put(
        core,
        root,
        "assumptions_and_symbols",
        {
            "assumptions": ["Same current across states; transfer persists; one battery only."],
            "symbols": {"a": "min", "b": "dimensionless", "t": "min", "U": "V"},
            "formulas": [
                "t_target(U)=a+b*mean(t_prior_states(U)); fit observed target prefix only",
                "MRE=mean(abs(predicted_end-true_end)/(true_end-origin)); zero denominator rejects",
            ],
        },
    )
    audit = {
        **registration["data_hashes"],
        temporal["index_path"]: core.file_hash(root / temporal["index_path"]),
    }
    legacy.put(core, root, "data_audit", {"raw_immutable": True, "data_hashes": audit})
    assessment = {
        "requirement_id": "REQ-Q3",
        "data_sufficiency_status": "SUFFICIENT",
        "missing_fields": [],
        "missing_entities": [],
        "missing_time_scope": [],
        "candidate_sources": [],
        "acquisition_cost": "NONE",
        "acquisition_time": "NONE",
        "allowed_substitutions": [],
        "forbidden_substitutions": ["Future target accuracy cannot be asserted"],
        "affected_downstream_stages": [],
    }
    legacy.put(
        core,
        root,
        "data_sufficiency",
        {
            "contract_version": "data-sufficiency/v1",
            "requirements": [req],
            "sources": [source],
            "acquisition_plans": [],
            "source_compositions": [],
            "aggregate_completion_claimed": False,
            "coverage_mode_by_requirement": {
                "REQ-Q3": {"mode": "SINGLE_SOURCE", "source_id": source["source_id"]}
            },
            "requirement_assessments": [assessment],
        },
    )
    legacy.put(
        core,
        root,
        "model_candidates",
        {
            "candidates": [
                {"candidate_id": "BASELINE", "baseline": True},
                {"candidate_id": "AFFINE", "baseline": False},
            ]
        },
    )
    legacy.advance(core, root, "MODELS_PROPOSED")
    code = synthetic._required_code_files(core)
    for name in ("produce.py", "check.py"):
        source = BASE / "known_code" / name
        shutil.copyfile(source, root / "models" / name)
        code.append(
            {
                "scope": "CASE_ROOT",
                "path": "models/" + name,
                "repository_path": source.relative_to(REPO).as_posix(),
                "sha256": core.file_hash(source),
            }
        )
    plan = {
        "preregistered": True,
        "execution_prepared": True,
        "candidate_ids": design["candidates"],
        "baseline_id": "BASELINE",
        "metric": "q3_remaining_MRE",
        "metric_direction": "MIN",
        "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        "selection_rule": "ARGMIN_THEN_ID",
        "random_seeds": design["seeds"],
        "required_code_files": code,
        "code_commit": subject,
        "required_input_hashes": audit,
        "metric_definitions": definitions,
        "temporal_design": temporal,
        "splits": {
            "train": ["PRIOR_STATES_AND_TARGET_PREFIX"],
            "validation": [
                s["sample_id"] for s in temporal["samples"] if s["split"] == "VALIDATION"
            ],
            "test": [],
        },
        "evaluation_design": {
            "mode": "CONDITIONAL_PREDICTION_FINAL_VERIFICATION",
            "start_budget": BUDGET,
            "independent_validation": False,
            "registration_sha256": core.file_hash(registration_path),
        },
        "stop_rule": (
            "Registered Q3 only: at most4 model starts,6 checker starts,"
            "1 Final per revision; no refund."
        ),
        "handoff_generated_at": core.utc_now(),
    }
    h = core.canonical_hash
    plan["trusted_freeze_registry"] = {
        "candidate_set": h(plan["candidate_ids"]),
        "metric": h(core.metric_freeze_payload(plan)),
        "seed_schedule": h(plan["random_seeds"]),
        "split_assignment": h(plan["splits"]),
        "baseline": h(plan["baseline_id"]),
        "input_set": h(audit),
        "code_set": h(code),
        "code_commit": h(subject),
        "execution_policy": h(
            core.execution_policy_payload(
                plan["stop_rule"], plan["handoff_generated_at"], plan["evaluation_design"]
            )
        ),
    }
    legacy.put(core, root, "experiment_plan", plan)
    synthetic._write_output_contract_probe(core, root, ["REQ-Q3"], metric="q3_remaining_MRE")
    core.advance_once(root)
    core.trusted_freezes(root)
    return {
        "status": "PREPARED_NOT_EXECUTED",
        "case_id": case_id,
        "scope": ["REQ-Q3"],
        "model_starts": 0,
        "scenario_explicit": "scenario_hash" in plan,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["register", "prepare", "propose"])
    parser.add_argument("--revision", type=int, choices=[1, 2], default=1)
    parser.add_argument("--subject")
    args = parser.parse_args()
    if args.command == "register":
        result = register(args.revision, args.subject)
    elif args.command == "prepare":
        result = prepare(args.revision)
    else:
        legacy.PHASE = BASE
        legacy.CASES = {2016: cid(args.revision)}
        legacy.propose(2016)
        return
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
