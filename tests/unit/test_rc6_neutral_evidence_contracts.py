from __future__ import annotations

import copy
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

HEX_A = "a" * 64
HEX_B = "b" * 64


@dataclass(frozen=True)
class NeutralCase:
    case_id: str
    domain: str
    payload: dict
    expected_status: str
    expected_reason_codes: tuple[str, ...] = ()


def release_snapshot(**changes) -> dict:
    value = {
        "project_version": "0.3.0-competition-rc6",
        "manifest_project_version": "0.3.0-competition-rc6",
        "skill_version_file": "0.2.0-competition-rc6",
        "skill_metadata_version": "0.2.0-competition-rc6",
        "runner_version": "0.2.0-competition-rc6",
        "manifest_skill_version": "0.2.0-competition-rc6",
        "state_skill_version": "0.2.0-competition-rc6",
        "changelog_versions": ["0.3.0-competition-rc6", "0.2.0-competition-rc6"],
        "discovered_skill_versions": ["0.2.0-competition-rc6"],
        "blocked_history_records": ["RC5_VERSION_FILE_MISMATCH"],
    }
    value.update(changes)
    return value


def requirement(
    requirement_id: str = "R-A",
    *,
    required_evidence_classes: list[str] | None = None,
    external_data_allowed: bool = False,
    external_data_required: bool = False,
    simulation_substitution_allowed: bool = False,
    partial_completion_allowed: bool = False,
) -> dict:
    required = required_evidence_classes or ["PROVIDED_EMPIRICAL", "ACQUIRED_EMPIRICAL"]
    return {
        "requirement_id": requirement_id,
        "role": "PRIMARY",
        "required_evidence_classes": required,
        "allowed_evidence_classes": required,
        "minimum_data_fields": ["x"],
        "required_time_scope": ["T-A", "T-B"],
        "required_entity_scope": ["E-A"],
        "external_data_allowed": external_data_allowed,
        "external_data_required": external_data_required,
        "simulation_substitution_allowed": simulation_substitution_allowed,
        "partial_completion_allowed": partial_completion_allowed,
        "dependency_requirements": [],
        "completion_rule": "ALL_REQUIRED_EVIDENCE",
    }


def source(
    source_id: str = "S-A",
    *,
    requirement_id: str = "R-A",
    evidence_class: str = "PROVIDED_EMPIRICAL",
) -> dict:
    return {
        "source_id": source_id,
        "supports_requirement_ids": [requirement_id],
        "evidence_class": evidence_class,
        "provenance": "REGISTERED_ORIGIN",
        "authority": "PRIMARY_PROVIDER",
        "retrieval_time": "T-RETRIEVED",
        "license_or_usage_status": "ALLOWED",
        "geographic_scope": ["G-A"],
        "time_scope": ["T-A", "T-B"],
        "entity_scope": ["E-A"],
        "field_schema": ["x", "y"],
        "hash": HEX_A,
        "freshness": "CURRENT_FOR_SCOPE",
        "limitations": [],
    }


def evidence_payload(
    *,
    requirements: list[dict] | None = None,
    sources: list[dict] | None = None,
    acquisition_plans: list[dict] | None = None,
    aggregate_completion_claimed: bool = False,
) -> dict:
    return {
        "requirements": requirements if requirements is not None else [requirement()],
        "sources": sources if sources is not None else [source()],
        "acquisition_plans": acquisition_plans or [],
        "aggregate_completion_claimed": aggregate_completion_claimed,
    }


def acquisition_plan(status: str = "PLANNED") -> dict:
    return {
        "requirement_id": "R-A",
        "candidate_sources": ["S-CANDIDATE"],
        "acquisition_cost": "LOW",
        "acquisition_time": "BOUNDED",
        "status": status,
    }


def run(
    run_id: str,
    requirement_ids: list[str],
    output_ids: list[str],
    *,
    input_hash: str = HEX_A,
    scenario_hash: str = HEX_A,
    metric_ids: list[str] | None = None,
    policy_exposure: int = 1,
    outcome: str = "SUCCESS",
) -> dict:
    return {
        "run_id": run_id,
        "outcome": outcome,
        "sealed": True,
        "current": True,
        "supported_requirement_ids": requirement_ids,
        "selected_output_ids": output_ids,
        "metric_ids": metric_ids or ["M-A"],
        "input_hash": input_hash,
        "scenario_hash": scenario_hash,
        "policy_exposure": policy_exposure,
    }


def selection_payload(mode: str = "PER_REQUIREMENT") -> dict:
    return {
        "requirements": [
            {
                "requirement_id": "R-A",
                "selection_metric": "M-A",
                "selection_direction": "MIN",
                "dependency_requirements": [],
                "cross_requirement_constraints": [],
            },
            {
                "requirement_id": "R-B",
                "selection_metric": "M-B",
                "selection_direction": "MAX",
                "dependency_requirements": [],
                "cross_requirement_constraints": [],
            },
        ],
        "runs": [
            run("RUN-A", ["R-A"], ["OUT-A"], metric_ids=["M-A"]),
            run("RUN-B", ["R-B"], ["OUT-B"], metric_ids=["M-B"]),
        ],
        "selection": {
            "selection_mode": mode,
            "requirement_to_run_map": {"R-A": ["RUN-A"], "R-B": ["RUN-B"]},
            "requirement_to_output_map": {"R-A": ["OUT-A"], "R-B": ["OUT-B"]},
            "shared_input_hashes": [HEX_A],
            "shared_scenario_hashes": [HEX_A],
            "compatibility_checks": ["INPUT", "SCENARIO", "CONSTRAINTS"],
            "cross_requirement_constraints": [],
            "aggregate_objective": "DECLARED_TRADEOFF",
            "tradeoff_rule": "REQUIREMENT_LOCAL_METRICS",
            "limitations": [],
        },
    }


def semantic_payload(claim_type: str = "DESCRIPTIVE") -> dict:
    return {
        "claim": {
            "claim_id": "C-A",
            "requirement_id": "R-A",
            "claim_type": claim_type,
            "statement": "Bounded statement",
            "scope": {"fields": ["x"], "time": ["T-A"], "entities": ["E-A"]},
            "evidence_class": "PROVIDED_EMPIRICAL",
            "selected_run_ids": ["RUN-A"],
            "selected_output_ids": ["OUT-A"],
            "metric_ids": ["M-A"],
            "comparator_ids": [],
            "support_predicates": {"scope_bounded": True},
            "uncertainty": {"status": "BOUNDED"},
            "counter_evidence": [],
            "limitations": ["LIMIT-A"],
            "claim_strength": "BOUNDED",
            "status": "SUPPORTED",
        },
        "runs": [run("RUN-A", ["R-A"], ["OUT-A"], metric_ids=["M-A"])],
        "outputs": [{"output_id": "OUT-A", "metric_ids": ["M-A"]}],
        "comparators": [],
        "validation": {},
    }


def compatibility_payload(kind: str) -> dict:
    return {
        "kind": kind,
        "legacy_contract_version": "claim-evidence/v2",
        "requirement_ids": ["R-A"],
        "run_outcomes": ["SUCCESS"],
        "handoff_status": "COMPLETE",
        "ordered_claim_ids": ["C-A", "C-B"],
        "permuted_claim_ids": ["C-B", "C-A"],
    }


def changed(value: dict, path: tuple[str | int, ...], replacement) -> dict:
    result = copy.deepcopy(value)
    target = result
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    return result


def neutral_cases() -> list[NeutralCase]:
    cases: list[NeutralCase] = [
        NeutralCase("A01_RELEASE_ALL_CONSISTENT", "RELEASE", release_snapshot(), "PASS"),
        NeutralCase(
            "A02_SKILL_VERSION_OLD",
            "RELEASE",
            release_snapshot(skill_version_file="0.2.0-competition-rc5"),
            "BLOCK",
            ("RC_RELEASE_SKILL_VERSION_MISMATCH",),
        ),
        NeutralCase(
            "A03_RUNNER_VERSION_OLD",
            "RELEASE",
            release_snapshot(runner_version="0.2.0-competition-rc5"),
            "BLOCK",
            ("RC_RELEASE_RUNNER_VERSION_MISMATCH",),
        ),
        NeutralCase(
            "A04_METADATA_VERSION_OLD",
            "RELEASE",
            release_snapshot(skill_metadata_version="0.2.0-competition-rc5"),
            "BLOCK",
            ("RC_RELEASE_SKILL_METADATA_VERSION_MISMATCH",),
        ),
        NeutralCase(
            "A05_MANIFEST_VERSION_OLD",
            "RELEASE",
            release_snapshot(manifest_skill_version="0.2.0-competition-rc5"),
            "BLOCK",
            ("RC_RELEASE_MANIFEST_VERSION_MISMATCH",),
        ),
        NeutralCase(
            "A06_STATE_VERSION_OLD",
            "RELEASE",
            release_snapshot(state_skill_version="0.2.0-competition-rc5"),
            "BLOCK",
            ("RC_RELEASE_STATE_VERSION_MISMATCH",),
        ),
        NeutralCase(
            "A07_SKILL_VERSION_MISSING",
            "RELEASE",
            release_snapshot(skill_version_file=None),
            "BLOCK",
            ("RC_RELEASE_SKILL_VERSION_MISSING",),
        ),
        NeutralCase("A08_BLOCKED_HISTORY_PRESERVED", "RELEASE", release_snapshot(), "PASS"),
        NeutralCase(
            "A09_PROJECT_VERSION_MISMATCH",
            "RELEASE",
            release_snapshot(project_version="0.3.0-competition-rc5"),
            "BLOCK",
            ("RC_RELEASE_PROJECT_VERSION_MISMATCH",),
        ),
        NeutralCase(
            "A10_ILLEGAL_PRERELEASE",
            "RELEASE",
            release_snapshot(skill_version_file="0.2.0-rc6"),
            "BLOCK",
            ("RC_RELEASE_VERSION_FORMAT_INVALID",),
        ),
        NeutralCase(
            "A11_BLOCKED_HISTORY_REMOVED",
            "RELEASE",
            release_snapshot(blocked_history_records=[]),
            "BLOCK",
            ("RC_RELEASE_HISTORY_BLOCKED_RECORD_MISSING",),
        ),
        NeutralCase("B09_PROVIDED_EMPIRICAL", "DATA", evidence_payload(), "SUFFICIENT"),
        NeutralCase(
            "B10_ACQUIRED_EMPIRICAL",
            "DATA",
            evidence_payload(sources=[source(evidence_class="ACQUIRED_EMPIRICAL")]),
            "SUFFICIENT",
        ),
        NeutralCase(
            "B11_SIMULATION_FOR_EMPIRICAL",
            "DATA",
            evidence_payload(sources=[source(evidence_class="SIMULATION")]),
            "UNSATISFIABLE_WITH_CURRENT_INPUTS",
            ("RC_SIMULATION_CANNOT_SUPPORT_EMPIRICAL_CLAIM",),
        ),
        NeutralCase(
            "B12_ASSUMPTION_FOR_OBSERVATION",
            "DATA",
            evidence_payload(sources=[source(evidence_class="ASSUMPTION")]),
            "UNSATISFIABLE_WITH_CURRENT_INPUTS",
            ("RC_REQUIREMENT_EVIDENCE_CLASS_INSUFFICIENT",),
        ),
        NeutralCase(
            "B13_TIME_SCOPE_MISMATCH",
            "DATA",
            changed(evidence_payload(), ("sources", 0, "time_scope"), ["T-A"]),
            "UNSATISFIABLE_WITH_CURRENT_INPUTS",
            ("RC_REQUIREMENT_TIME_SCOPE_INSUFFICIENT",),
        ),
        NeutralCase(
            "B14_ENTITY_SCOPE_MISMATCH",
            "DATA",
            changed(evidence_payload(), ("sources", 0, "entity_scope"), ["E-B"]),
            "UNSATISFIABLE_WITH_CURRENT_INPUTS",
            ("RC_REQUIREMENT_ENTITY_SCOPE_INSUFFICIENT",),
        ),
        NeutralCase(
            "B15_PROVENANCE_MISSING",
            "DATA",
            changed(evidence_payload(), ("sources", 0, "provenance"), ""),
            "BLOCK",
            ("RC_DATA_PROVENANCE_INCOMPLETE",),
        ),
        NeutralCase(
            "B16_UNKNOWN_NOT_SUFFICIENT",
            "DATA",
            evidence_payload(sources=[source(evidence_class="UNKNOWN")]),
            "UNSATISFIABLE_WITH_CURRENT_INPUTS",
            ("RC_REQUIREMENT_EVIDENCE_CLASS_INSUFFICIENT",),
        ),
        NeutralCase(
            "B17_PARTIAL_REQUIREMENT",
            "DATA",
            evidence_payload(
                requirements=[requirement(), requirement("R-B", partial_completion_allowed=True)],
                sources=[source()],
            ),
            "PARTIAL",
            ("RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE",),
        ),
        NeutralCase(
            "B18_ALL_PRIMARY_INSUFFICIENT",
            "DATA",
            evidence_payload(sources=[]),
            "UNSATISFIABLE_WITH_CURRENT_INPUTS",
            ("RC_REQUIREMENT_EMPIRICAL_DATA_MISSING",),
        ),
    ]

    external_requirement = requirement(external_data_allowed=True, external_data_required=True)
    cases.extend(
        [
            NeutralCase(
                "C19_ACQUISITION_PLAN_PRESENT",
                "DATA",
                evidence_payload(
                    requirements=[external_requirement],
                    sources=[],
                    acquisition_plans=[acquisition_plan()],
                ),
                "ACQUISITION_REQUIRED",
            ),
            NeutralCase(
                "C20_ACQUISITION_PLAN_MISSING",
                "DATA",
                evidence_payload(requirements=[external_requirement], sources=[]),
                "BLOCK",
                ("RC_DATA_ACQUISITION_PLAN_MISSING",),
            ),
            NeutralCase(
                "C21_ACQUISITION_RECHECK_SUFFICIENT",
                "DATA",
                evidence_payload(
                    requirements=[external_requirement],
                    sources=[source(evidence_class="ACQUIRED_EMPIRICAL")],
                    acquisition_plans=[acquisition_plan("ACQUIRED")],
                ),
                "SUFFICIENT",
            ),
            NeutralCase(
                "C22_ACQUISITION_FAILED",
                "DATA",
                evidence_payload(
                    requirements=[external_requirement],
                    sources=[],
                    acquisition_plans=[acquisition_plan("FAILED")],
                ),
                "UNSATISFIABLE_WITH_CURRENT_INPUTS",
                ("RC_REQUIREMENT_EMPIRICAL_DATA_MISSING",),
            ),
            NeutralCase(
                "C23_LICENSE_UNKNOWN",
                "DATA",
                changed(
                    evidence_payload(
                        requirements=[external_requirement],
                        sources=[source(evidence_class="ACQUIRED_EMPIRICAL")],
                    ),
                    ("sources", 0, "license_or_usage_status"),
                    "UNKNOWN",
                ),
                "BLOCK",
                ("RC_DATA_PROVENANCE_INCOMPLETE",),
            ),
            NeutralCase(
                "C24_INDEPENDENT_REQUIREMENT_CONTINUES",
                "DATA",
                evidence_payload(
                    requirements=[
                        requirement(),
                        requirement("R-B", partial_completion_allowed=True),
                    ],
                    sources=[source()],
                ),
                "PARTIAL",
                ("RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE",),
            ),
            NeutralCase(
                "C25_AGGREGATE_CANNOT_CLAIM_COMPLETE",
                "DATA",
                evidence_payload(
                    requirements=[
                        requirement(),
                        requirement("R-B", partial_completion_allowed=True),
                    ],
                    sources=[source()],
                    aggregate_completion_claimed=True,
                ),
                "BLOCK",
                ("RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE",),
            ),
        ]
    )

    per_requirement = selection_payload()
    global_valid = selection_payload("GLOBAL_JOINT")
    global_valid["runs"] = [
        run("RUN-J", ["R-A", "R-B"], ["OUT-A", "OUT-B"], metric_ids=["M-A", "M-B"])
    ]
    global_valid["selection"]["requirement_to_run_map"] = {
        "R-A": ["RUN-J"],
        "R-B": ["RUN-J"],
    }
    portfolio = selection_payload("JOINT_PORTFOLIO")
    cases.extend(
        [
            NeutralCase("D26_DIFFERENT_RUNS_PER_REQUIREMENT", "SELECTION", per_requirement, "PASS"),
            NeutralCase("D27_GLOBAL_RUN_COVERS_ALL", "SELECTION", global_valid, "PASS"),
            NeutralCase(
                "D28_GLOBAL_RUN_MISSING_OUTPUT",
                "SELECTION",
                changed(global_valid, ("runs", 0, "selected_output_ids"), ["OUT-A"]),
                "BLOCK",
                ("RC_GLOBAL_SELECTION_REQUIREMENT_COVERAGE_INSUFFICIENT",),
            ),
            NeutralCase(
                "D29_METRIC_REQUIREMENT_MISMATCH",
                "SELECTION",
                changed(per_requirement, ("requirements", 1, "selection_metric"), "M-A"),
                "BLOCK",
                ("RC_SELECTION_METRIC_REQUIREMENT_MISMATCH",),
            ),
            NeutralCase(
                "D30_REQUIREMENT_POINTS_TO_WRONG_RUN",
                "SELECTION",
                changed(
                    per_requirement,
                    ("selection", "requirement_to_run_map", "R-A"),
                    ["RUN-B"],
                ),
                "BLOCK",
                ("RC_REQUIREMENT_SELECTED_RUN_SEMANTIC_MISMATCH",),
            ),
            NeutralCase(
                "D31_REQUIREMENT_POINTS_TO_WRONG_OUTPUT",
                "SELECTION",
                changed(
                    per_requirement,
                    ("selection", "requirement_to_output_map", "R-A"),
                    ["OUT-B"],
                ),
                "BLOCK",
                ("RC_REQUIREMENT_SELECTED_OUTPUT_MISSING",),
            ),
            NeutralCase(
                "D32_PORTFOLIO_INPUT_HASH_MISMATCH",
                "SELECTION",
                changed(portfolio, ("runs", 1, "input_hash"), HEX_B),
                "BLOCK",
                ("RC_PORTFOLIO_CROSS_REQUIREMENT_INCONSISTENT",),
            ),
            NeutralCase(
                "D33_PORTFOLIO_SCENARIO_MISMATCH",
                "SELECTION",
                changed(portfolio, ("runs", 1, "scenario_hash"), HEX_B),
                "BLOCK",
                ("RC_PORTFOLIO_CROSS_REQUIREMENT_INCONSISTENT",),
            ),
            NeutralCase(
                "D34_CROSS_REQUIREMENT_CONSTRAINT_CONFLICT",
                "SELECTION",
                changed(
                    portfolio,
                    ("selection", "cross_requirement_constraints"),
                    [{"constraint_id": "K-A", "status": "CONFLICT"}],
                ),
                "BLOCK",
                ("RC_PORTFOLIO_CROSS_REQUIREMENT_INCONSISTENT",),
            ),
            NeutralCase("D35_VALID_JOINT_PORTFOLIO", "SELECTION", portfolio, "PASS"),
        ]
    )

    policy = semantic_payload("POLICY_EVALUATION")
    policy["claim"]["comparator_ids"] = ["CMP-A"]
    policy["claim"]["support_predicates"] = {
        "policy_executed": True,
        "policy_exposure_positive": True,
        "comparator_present": True,
        "benefit_recorded": True,
        "cost_recorded": True,
        "scope_bounded": True,
    }
    policy["comparators"] = [{"comparator_id": "CMP-A", "metric_ids": ["M-A"]}]
    cases.extend(
        [
            NeutralCase("E36_POLICY_EXECUTED_WITH_COMPARATOR", "SEMANTIC", policy, "PASS"),
            NeutralCase(
                "E37_POLICY_EXPOSURE_ZERO",
                "SEMANTIC",
                changed(policy, ("runs", 0, "policy_exposure"), 0),
                "BLOCK",
                ("RC_POLICY_CLAIM_NO_POLICY_EXPOSURE",),
            ),
            NeutralCase(
                "E38_POLICY_COMPARATOR_MISSING",
                "SEMANTIC",
                changed(policy, ("comparators",), []),
                "BLOCK",
                ("RC_POLICY_CLAIM_COMPARATOR_MISSING",),
            ),
            NeutralCase(
                "E39_SIMULATION_ONLY_EMPIRICAL_CLAIM",
                "SEMANTIC",
                changed(semantic_payload("EMPIRICAL"), ("claim", "evidence_class"), "SIMULATION"),
                "BLOCK",
                ("RC_SIMULATION_CANNOT_SUPPORT_EMPIRICAL_CLAIM",),
            ),
            NeutralCase(
                "E40_FEASIBILITY_WITHOUT_RECALC",
                "SEMANTIC",
                semantic_payload("FEASIBILITY"),
                "BLOCK",
                ("RC_FEASIBILITY_INDEPENDENT_RECALC_MISSING",),
            ),
            NeutralCase(
                "E41_HEURISTIC_AS_GLOBAL_OPTIMUM",
                "SEMANTIC",
                changed(
                    semantic_payload("OPTIMALITY"),
                    ("claim", "claim_strength"),
                    "GLOBAL_OPTIMUM",
                ),
                "BLOCK",
                ("RC_OPTIMALITY_CERTIFICATE_MISSING",),
            ),
            NeutralCase(
                "E42_ASSOCIATION_AS_CAUSAL",
                "SEMANTIC",
                semantic_payload("CAUSAL"),
                "BLOCK",
                ("RC_CAUSAL_IDENTIFICATION_MISSING",),
            ),
            NeutralCase(
                "E43_PREDICTION_WITHOUT_TEST",
                "SEMANTIC",
                semantic_payload("PREDICTIVE"),
                "BLOCK",
                ("RC_PREDICTIVE_VALIDATION_MISSING",),
            ),
            NeutralCase(
                "E44_COUNTER_EVIDENCE_OMITTED",
                "SEMANTIC",
                changed(
                    semantic_payload(),
                    ("validation",),
                    {"counter_evidence_detected": True},
                ),
                "BLOCK",
                ("RC_CLAIM_COUNTER_EVIDENCE_UNRESOLVED",),
            ),
            NeutralCase("E45_VALID_BOUNDED_CLAIM", "SEMANTIC", semantic_payload(), "PASS"),
            NeutralCase(
                "E46_VALID_LOCAL_CLAIM_AGGREGATION",
                "SEMANTIC",
                {
                    **semantic_payload(),
                    "aggregate": {
                        "primary_requirement_ids": ["R-A", "R-B"],
                        "supported_requirement_ids": ["R-B", "R-A"],
                        "requirement_claim_ids": {"R-A": "C-A", "R-B": "C-B"},
                    },
                },
                "PASS",
            ),
            NeutralCase(
                "F47_SINGLE_REQUIREMENT_LEGACY",
                "COMPATIBILITY",
                compatibility_payload("SINGLE_REQUIREMENT_LEGACY"),
                "PASS",
            ),
            NeutralCase(
                "F48_MULTI_REQUIREMENT_CLAIM_V2",
                "COMPATIBILITY",
                compatibility_payload("MULTI_REQUIREMENT_CLAIM_V2"),
                "PASS",
            ),
            NeutralCase(
                "F49_SELECTED_OUTPUT_PREFLIGHT",
                "COMPATIBILITY",
                compatibility_payload("SELECTED_OUTPUT_PREFLIGHT"),
                "PASS",
            ),
            NeutralCase(
                "F50_INVALID_RUN_OUTCOMES",
                "COMPATIBILITY",
                changed(
                    compatibility_payload("INVALID_RUN_OUTCOMES"),
                    ("run_outcomes",),
                    ["FAILED", "STALE", "SUPERSEDED"],
                ),
                "BLOCK",
                ("RC_REQUIREMENT_SELECTED_RUN_INVALID_STATUS",),
            ),
            NeutralCase(
                "F51_PARTIAL_HANDOFF",
                "COMPATIBILITY",
                changed(compatibility_payload("PARTIAL_HANDOFF"), ("handoff_status",), "PARTIAL"),
                "PARTIAL",
                ("RC_AGGREGATE_PRIMARY_REQUIREMENT_INCOMPLETE",),
            ),
            NeutralCase(
                "F52_COMPLETE_HANDOFF",
                "COMPATIBILITY",
                compatibility_payload("COMPLETE_HANDOFF"),
                "PASS",
            ),
            NeutralCase(
                "F53_CLAIM_FILE_ORDER_PERMUTATION",
                "COMPATIBILITY",
                compatibility_payload("CLAIM_FILE_ORDER_PERMUTATION"),
                "PASS",
            ),
        ]
    )
    return cases


NEUTRAL_CASES = neutral_cases()


def load_module(path: Path, name: str):
    assert path.is_file(), f"RC6_CONTRACT_IMPLEMENTATION_MISSING:{path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def evaluate_case(repo_root: Path, case: NeutralCase) -> dict:
    if case.domain == "RELEASE":
        module = load_module(
            repo_root / "scripts/check_skill_release_consistency.py",
            "rc6_release_consistency",
        )
        evaluator = getattr(module, "evaluate_release_snapshot", None)
    else:
        module = load_module(
            repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
            "rc6_cumcm_case",
        )
        evaluator = {
            "DATA": getattr(module, "evaluate_data_sufficiency", None),
            "SELECTION": getattr(module, "validate_requirement_selection", None),
            "SEMANTIC": getattr(module, "validate_semantic_claim_support", None),
            "COMPATIBILITY": getattr(module, "validate_evidence_compatibility", None),
        }[case.domain]
    assert callable(evaluator), f"RC6_CONTRACT_FUNCTION_MISSING:{case.domain}"
    result = evaluator(copy.deepcopy(case.payload))
    assert isinstance(result, dict)
    return result


def test_neutral_case_registry_is_complete_and_case_neutral() -> None:
    assert len(NEUTRAL_CASES) == 56
    assert len({case.case_id for case in NEUTRAL_CASES}) == 56
    rendered = repr(NEUTRAL_CASES).lower()
    prohibited = (
        "airport",
        "taxi",
        "crop",
        "glass",
        "supplier",
        "credit",
        "2017",
        "2018",
        "2019",
        "2020",
        "2021",
        "2022",
        "2023",
        "2024",
        "2025",
    )
    assert not any(token in rendered for token in prohibited)


@pytest.mark.parametrize("case", NEUTRAL_CASES, ids=lambda case: case.case_id)
def test_frozen_rc6_neutral_contract(repo_root: Path, case: NeutralCase) -> None:
    actual = evaluate_case(repo_root, case)

    assert actual.get("status") == case.expected_status
    assert tuple(actual.get("reason_codes", [])) == case.expected_reason_codes
